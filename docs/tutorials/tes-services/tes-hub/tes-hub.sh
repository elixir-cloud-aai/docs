#!/usr/bin/env bash
# Tunnel hub for services that run as GA4GH TES tasks (default: TESK @ ELIXIR-FI).
#
# TES cannot publish ports and TESK pods only get outbound HTTPS, so each task dials this
# chisel server through your HTTPS reverse proxy (websocket) and publishes its port
# as 127.0.0.1:<port> on this VM:
#
#   TES pod --https--> HUB_URL (e.g. https://hub.example.org/tes-tunnel/)
#           --> chisel HUB_LISTEN_HOST:8090 --> VM 127.0.0.1:<port>
#
# Each service owns a hub user that may only open its own ports. Pods get common.sh
# prepended to their script and call start_tunnel <remote>...
#
# Usage:
#   ./tes-hub.sh setup <HUB_URL> [LISTEN_HOST]   # once: chisel, hub key, proxy snippet, start
#   ./tes-hub.sh start | stop | restart | status
#   ./tes-hub.sh users                  # hub users and the remotes each may open
#   ./tes-hub.sh add-user <user:password> <regex>...   # add or replace a user
#   ./tes-hub.sh env                    # HUB_URL, CHISEL_URL, HUB_FINGERPRINT for clients
#
# The hub and the users survive restarts; tasks reconnect by themselves. It does not
# survive a VM reboot: run start again.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
STATE_DIR="${HUB_STATE_DIR:-$HERE/.state}"
mkdir -p "$STATE_DIR"; chmod 700 "$STATE_DIR"
CONFIG="$STATE_DIR/config"
# setup writes HUB_URL and HUB_LISTEN_HOST here; environment variables override them.
while IFS='=' read -r k v; do [[ -n "${!k:-}" ]] || eval "$k=$v"; done < <(cat "$CONFIG" 2>/dev/null)

# ---- configuration -----------------------------------------------------------------------
HUB_URL="${HUB_URL:-}"                                              # public URL (proxy location)
HUB_LISTEN_HOST="${HUB_LISTEN_HOST:-127.0.0.1}"                     # where the proxy reaches the VM
HUB_LISTEN_PORT="${HUB_LISTEN_PORT:-8090}"
CHISEL_VERSION="${CHISEL_VERSION:-1.12.0}"
CHISEL_URL="https://github.com/jpillora/chisel/releases/download/v${CHISEL_VERSION}/chisel_${CHISEL_VERSION}_linux_amd64.gz"
# ------------------------------------------------------------------------------------------

CHISEL="$STATE_DIR/bin/chisel"
AUTHFILE="$STATE_DIR/authfile.json"
PIDF="$STATE_DIR/hub.pid"
LOGF="$STATE_DIR/hub.log"
KEYF="$STATE_DIR/hub.key"

die() { echo "ERROR: $*" >&2; exit 1; }
running() { [[ -s "$PIDF" ]] && kill -0 "$(cat "$PIDF")" 2>/dev/null; }
fingerprint() { grep -o 'Fingerprint [^ ]*' "$LOGF" 2>/dev/null | tail -1 | cut -d' ' -f2 || true; }

cmd_setup() {
  HUB_URL="${1:-$HUB_URL}"; HUB_LISTEN_HOST="${2:-$HUB_LISTEN_HOST}"
  [[ "$HUB_URL" == https://*/ ]] || die "usage: $0 setup https://<proxy-host>/<path>/ [LISTEN_HOST]"
  printf 'HUB_URL=%q\nHUB_LISTEN_HOST=%q\n' "$HUB_URL" "$HUB_LISTEN_HOST" > "$CONFIG"
  if [[ ! -x "$CHISEL" ]]; then
    mkdir -p "$STATE_DIR/bin"
    curl -fsSL "$CHISEL_URL" | gunzip > "$CHISEL" && chmod 755 "$CHISEL"
    echo "installed chisel $("$CHISEL" --version 2>&1 | head -1) to $CHISEL"
  fi
  [[ -s "$KEYF" ]] || { "$CHISEL" server --keygen "$KEYF" >/dev/null; chmod 600 "$KEYF"; echo "generated hub key $KEYF"; }
  [[ -f "$AUTHFILE" ]] || { echo '{}' > "$AUTHFILE"; chmod 600 "$AUTHFILE"; }
  local host path
  host="$(python3 -c "from urllib.parse import urlparse; print(urlparse('$HUB_URL').hostname)")"
  path="$(python3 -c "from urllib.parse import urlparse; print(urlparse('$HUB_URL').path or '/')")"
  cat <<EOF

Add this to the server block of $host on your proxy, then reload it:

    location $path {
        proxy_pass http://$HUB_LISTEN_HOST:$HUB_LISTEN_PORT/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 1d;
        proxy_send_timeout 1d;
        proxy_buffering off;
    }

EOF
  cmd_start
}

cmd_start() {
  [[ -x "$CHISEL" && -s "$KEYF" && -n "$HUB_URL" ]] || die "run: $0 setup <HUB_URL>"
  if running; then echo "hub already running (pid $(cat "$PIDF"))"; return; fi
  # setsid: the hub outlives this shell. exec: the pid file holds chisel's own pid.
  setsid -f sh -c 'echo $$ > "$0"; exec "$@"' "$PIDF" "$CHISEL" server \
    --host "$HUB_LISTEN_HOST" --port "$HUB_LISTEN_PORT" --reverse \
    --authfile "$AUTHFILE" --keyfile "$KEYF" --keepalive 25s >>"$LOGF" 2>&1 < /dev/null
  sleep 2
  running || { tail -5 "$LOGF"; die "hub failed to start"; }
  echo "hub listening on $HUB_LISTEN_HOST:$HUB_LISTEN_PORT (pid $(cat "$PIDF"), log: $LOGF)"
  echo "fingerprint $(fingerprint)"
}

cmd_stop() { if running; then kill "$(cat "$PIDF")" && rm -f "$PIDF" && echo "hub stopped"; else echo "hub not running"; fi; }

cmd_status() {
  [[ -n "$HUB_URL" ]] || die "hub not set up (run: $0 setup <HUB_URL>)"
  if running; then echo "hub running (pid $(cat "$PIDF"))"; else echo "hub not running"; fi
  # While the hub runs, chisel answers plain HTTP with "Not found"; anything else is the proxy.
  if [[ "$(curl -s -m 10 "$HUB_URL" 2>/dev/null)" == "Not found" ]]; then echo "proxy route OK: $HUB_URL"
  else echo "proxy route not working: $HUB_URL (hub down, or the proxy location is missing)"; fi
  # Ports the users may publish, and which of them are connected right now.
  local ports listening p
  ports="$(python3 - "$AUTHFILE" <<'PY' 2>/dev/null || true
import json, re, sys
ports = {p for v in json.load(open(sys.argv[1])).values() for r in v if r.startswith("^R:")
         for p in re.findall(r"\d{2,5}", r.split(":")[-1])}
print(" ".join(sorted(ports, key=int)))
PY
)"
  listening="$(ss -tln 2>/dev/null)"
  for p in $ports; do
    [[ "$listening" == *"127.0.0.1:$p "* ]] && echo "  tunnel up:   127.0.0.1:$p" || echo "  not connected: 127.0.0.1:$p"
  done
}

cmd_users() {
  python3 - "$AUTHFILE" <<'PY'
import json, sys
for k, v in json.load(open(sys.argv[1])).items():
    print(f"{k.split(':')[0]:10} {' '.join(v)}")
PY
}

# add-user <user:password> <regex>...: replaces any existing entry for that user.
# chisel reloads the authfile when it changes, so no restart is needed.
cmd_add_user() {
  local auth="${1:-}"; shift || true
  [[ "$auth" == *:* && $# -gt 0 ]] || die "usage: $0 add-user <user:password> <regex>..."
  [[ -f "$AUTHFILE" ]] || die "run: $0 setup <HUB_URL>"
  python3 - "$AUTHFILE" "$auth" "$@" <<'PY'
import json, sys
p, auth, regexes = sys.argv[1], sys.argv[2], sys.argv[3:]
user = auth.split(":")[0] + ":"
a = {k: v for k, v in json.load(open(p)).items() if not k.startswith(user)}
a[auth] = regexes
json.dump(a, open(p, "w"), indent=2)
PY
  echo "hub user '${auth%%:*}' may open: $*"
}

cmd_env() {
  [[ -n "$HUB_URL" ]] || die "run: $0 setup <HUB_URL>"
  printf 'HUB_URL=%q\nCHISEL_URL=%q\nHUB_FINGERPRINT=%q\n' "$HUB_URL" "$CHISEL_URL" "$(fingerprint)"
}

case "${1:-}" in
  setup)    shift; cmd_setup "$@" ;;
  start)    cmd_start ;;
  stop)     cmd_stop ;;
  restart)  cmd_stop; sleep 1; cmd_start ;;
  status)   cmd_status ;;
  users)    cmd_users ;;
  add-user) shift; cmd_add_user "$@" ;;
  env)      cmd_env ;;
  *) sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 1 ;;
esac
