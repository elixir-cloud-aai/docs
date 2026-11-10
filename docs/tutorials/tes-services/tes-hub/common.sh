# Pod-side tunnel helpers, prepended to the pod script by the launchers
# (tes-service.sh, ../omop-tesk/omop-tesk-fi.sh).
# Runs inside a TES pod: random UID, read-only image, outbound HTTPS only.
set -u
export HOME=/tmp
log() { echo "[$(date -u +%H:%M:%S) ${ROLE}] $*"; }

fetch() { # url dest; works with curl, wget or python3, whichever the image has
  if command -v curl >/dev/null 2>&1; then curl -fsSL --retry 3 -o "$2" "$1"
  elif command -v wget >/dev/null 2>&1; then wget -q -O "$2" "$1"
  else python3 -c 'import sys, urllib.request; urllib.request.urlretrieve(*sys.argv[1:])' "$1" "$2"; fi
}

# Connects to the chisel hub on the VM (through the HTTPS proxy) and keeps the given
# remotes open. chisel reconnects by itself, so the tunnel survives hub/proxy restarts.
start_tunnel() {
  if [ -z "${HUB_URL:-}" ]; then log "HUB_URL not set, running without tunnel"; return 0; fi
  fetch "$CHISEL_URL" /tmp/chisel.gz && gunzip -f /tmp/chisel.gz && chmod 755 /tmp/chisel \
    || { log "ERROR: could not download chisel from $CHISEL_URL"; exit 2; }
  log "tunnel to $HUB_URL: $*"
  /tmp/chisel client --auth "$HUB_AUTH" --keepalive 25s --max-retry-interval 30s \
    ${HUB_FINGERPRINT:+--fingerprint "$HUB_FINGERPRINT"} "$HUB_URL" "$@" &
  TUNNEL_PID=$!
}
