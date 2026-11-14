# Interactive Services on TES: Commands

This page lists the commands of [Run Interactive Services on
TES](interactive_services_tes.md) without the explanations. They use the
values of the virtual machine `eoc-services` of the BioHackathon Europe 2026:
replace the addresses with your own. All commands run on the virtual machine
in `~/eoc_services`, except those marked `laptop`, which run on your
computer.

## Install the scripts

```bash
# disable "!" history expansion while pasting
set +H
# create the directory layout and change into it
mkdir -p ~/eoc_services/{tes-hub,omop-tesk/pod,rstudio-tesk} && cd ~/eoc_services
# tunnel hub
cat > tes-hub/tes-hub.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/tes-hub/tes-hub.sh"
__TES_SERVICES_EOF__
# requests to the TES service, with the access token in TES_TOKEN
cat > tes-hub/tes-api.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/tes-hub/tes-api.sh"
__TES_SERVICES_EOF__
# code sent into every task: downloads chisel, opens the tunnel
cat > tes-hub/common.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/tes-hub/common.sh"
__TES_SERVICES_EOF__
# generic launcher for single-container services
cat > tes-hub/tes-service.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/tes-hub/tes-service.sh"
__TES_SERVICES_EOF__
# Atlas stack launcher
cat > omop-tesk/omop-tesk-fi.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/omop-tesk/omop-tesk-fi.sh"
__TES_SERVICES_EOF__
# Atlas stack: database task
cat > omop-tesk/pod/db.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/omop-tesk/pod/db.sh"
__TES_SERVICES_EOF__
# Atlas stack: WebAPI task
cat > omop-tesk/pod/webapi.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/omop-tesk/pod/webapi.sh"
__TES_SERVICES_EOF__
# Atlas stack: Atlas UI task
cat > omop-tesk/pod/atlas.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/omop-tesk/pod/atlas.sh"
__TES_SERVICES_EOF__
# RStudio: image and port
cat > rstudio-tesk/service.conf <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/rstudio-tesk/service.conf"
__TES_SERVICES_EOF__
# RStudio: what runs in the task
cat > rstudio-tesk/pod.sh <<'__TES_SERVICES_EOF__'
--8<-- "docs/tutorials/tes-services/rstudio-tesk/pod.sh"
__TES_SERVICES_EOF__
# make the launchers executable
chmod +x tes-hub/tes-hub.sh tes-hub/tes-service.sh omop-tesk/omop-tesk-fi.sh
# re-enable history expansion, list the installed files
set -H; ls -R ~/eoc_services/{tes-hub,omop-tesk,rstudio-tesk}
```

## Set up the hub

```bash
# once: download chisel, create the hub key, start the hub on 10.0.2.165:8090
# (the elixir-on.cloud proxy runs on another machine, so the hub listens on the VM address)
./tes-hub/tes-hub.sh setup https://elixir-on.cloud/tes-tunnel/ 10.0.2.165
# check hub, proxy route and all tunnels; must print "proxy route OK: https://elixir-on.cloud/tes-tunnel/"
./tes-hub/tes-hub.sh status
```

```nginx
# on the proxy (194.94.4.89), in the server block of elixir-on.cloud
location /tes-tunnel/ {
    proxy_pass http://10.0.2.165:8090/;           # the hub on eoc-services
    proxy_http_version 1.1;                       # needed for websockets
    proxy_set_header Upgrade $http_upgrade;       # pass the websocket upgrade
    proxy_set_header Connection "upgrade";        # pass the websocket upgrade
    proxy_set_header Host $host;                  # keep the original host name
    proxy_read_timeout 1d;                        # keep idle tunnels open
    proxy_send_timeout 1d;                        # keep idle tunnels open
    proxy_buffering off;                          # stream tunnel traffic unbuffered
}
```

```bash
# on the proxy (194.94.4.89): apply the location block
sudo systemctl reload nginx
```

## Set the access token

An LS Login access token, of an account in the compute group, lives for
about 4 hours: see [Get an access
token](interactive_services_tes.md#get-an-access-token).

```bash
# paste an LS Login access token (account in ECP_CLN:EOC-Compute); not shown, not in the history
read -rsp 'TES token: ' TES_TOKEN && echo && export TES_TOKEN
# check it: lists one task, or curl fails (error 22) with 401 (invalid or expired token) or 403 (not in the compute group)
printf 'Authorization: Bearer %s\n' "$TES_TOKEN" | curl -q -fsS -H @- "${TES_URL:-https://csc-tesk-noauth.rahtiapp.fi}/ga4gh/tes/v1/tasks?view=MINIMAL&page_size=1"
```

## Start Atlas with OMOP demo data

```bash
# Atlas uses port 8088 on this VM, because the cloud-registry container holds 127.0.0.1:8080
# (set permanently in ~/.bashrc)
export HUB_ATLAS_PORT=8088
# create credentials, submit DB, WebAPI and Atlas tasks, start the keep-alive loop, wait until ready (first start ~15 min)
./omop-tesk/omop-tesk-fi.sh up
# laptop: forward Atlas, then open http://localhost:8088/atlas/
ssh -N -L 8088:127.0.0.1:8088 ubuntu@eoc-services
```

## Start RStudio Server

```bash
# submit the RStudio task (rocker/rstudio:latest), start the keep-alive loop, wait for the tunnel (1-3 min)
./tes-hub/tes-service.sh rstudio-tesk up
# laptop: forward RStudio, then open http://localhost:8787
ssh -N -L 8787:127.0.0.1:8787 ubuntu@eoc-services
```

## Add JupyterLab as your own service

```bash
# service directory next to tes-hub/
mkdir -p jupyter-tesk
# service definition: hub user/task name, image, port
cat > jupyter-tesk/service.conf <<'EOF'
# JupyterLab, run with: ../tes-hub/tes-service.sh jupyter-tesk up
NAME=jupyter                      # hub user, task name
IMAGE=quay.io/jupyter/base-notebook:latest
PORT=8888                         # JupyterLab port in the pod, and on the VM
EOF
# what runs in the task: start JupyterLab without token, open the tunnel, stay in the foreground
cat > jupyter-tesk/pod.sh <<'EOF'
# Runs inside the TES pod (image quay.io/jupyter/base-notebook) as a random UID, so all
# writable state goes to /tmp. No token: the port is only reachable from the hub VM.
export HOME=/tmp/home; mkdir -p "$HOME"; cd "$HOME" || exit 1

jupyter lab --ip=127.0.0.1 --port="$PORT" --no-browser --IdentityProvider.token='' &
APP=$!

if [ "${SELFTEST:-0}" = 1 ]; then
  sleep 15
  rc=1
  python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:$PORT/api').read().decode())" \
    && { log "SELFTEST_OK"; rc=0; }
  kill $APP; exit $rc
fi

start_tunnel "R:127.0.0.1:${HUB_PORT}:127.0.0.1:${PORT}"
wait $APP
log "jupyter exited"; exit 1
EOF
# start it
./tes-hub/tes-service.sh jupyter-tesk up
# laptop: forward JupyterLab, then open http://localhost:8888
ssh -N -L 8888:127.0.0.1:8888 ubuntu@eoc-services
```

## Forward the ports

```bash
# laptop: Atlas, RStudio and JupyterLab in one connection
ssh -N -L 8088:127.0.0.1:8088 -L 8787:127.0.0.1:8787 -L 8888:127.0.0.1:8888 ubuntu@eoc-services
# VS Code Remote-SSH instead: Ports panel -> Forward a Port -> 8088, 8787, 8888
```

## Manage the services

```bash
# go to the scripts
cd ~/eoc_services
# hub, proxy route and every tunnel
./tes-hub/tes-hub.sh status
# hub users and the ports each may open
./tes-hub/tes-hub.sh users

# Atlas stack: tasks, tunnels, WebAPI and data source
./omop-tesk/omop-tesk-fi.sh status
# Atlas stack: logs of one task (db, webapi or atlas; filled once the task ends)
./omop-tesk/omop-tesk-fi.sh logs webapi
# Atlas stack: replace with a fresh instance
./omop-tesk/omop-tesk-fi.sh restart
# Atlas stack: stop
./omop-tesk/omop-tesk-fi.sh down
# Atlas stack: show the TES request of one task
./omop-tesk/omop-tesk-fi.sh print atlas

# RStudio: task, tunnel, keep-alive loop
./tes-hub/tes-service.sh rstudio-tesk status
# RStudio: task logs (filled once the task ends)
./tes-hub/tes-service.sh rstudio-tesk logs
# RStudio: replace with a fresh instance
./tes-hub/tes-service.sh rstudio-tesk restart
# RStudio: stop
./tes-hub/tes-service.sh rstudio-tesk down
# RStudio: show the TES request
./tes-hub/tes-service.sh rstudio-tesk print

# token expired (after about 4 hours, 401 in .state/watch.log): set a new token as in
# "Set the access token", then run up again, which gives the keep-alive loop the new token
./omop-tesk/omop-tesk-fi.sh up
./tes-hub/tes-service.sh rstudio-tesk up

# JupyterLab: status / logs / restart / down
./tes-hub/tes-service.sh jupyter-tesk status
./tes-hub/tes-service.sh jupyter-tesk logs
./tes-hub/tes-service.sh jupyter-tesk restart
./tes-hub/tes-service.sh jupyter-tesk down

# list all tasks on the TES service (the token goes through stdin, not the command line)
printf 'Authorization: Bearer %s\n' "$TES_TOKEN" | curl -q -fsS -H @- "${TES_URL:-https://csc-tesk-noauth.rahtiapp.fi}/ga4gh/tes/v1/tasks?view=MINIMAL"
```

## After a reboot

```bash
# start the hub again; running tasks reconnect within ~30 seconds
./tes-hub/tes-hub.sh start
# restart the keep-alive loops of the single-container services (set the access token first)
./tes-hub/tes-service.sh rstudio-tesk up
./tes-hub/tes-service.sh jupyter-tesk up
```

## Settings

```bash
# TES instance: TESK @ ELIXIR-FI (default; will change to the address with tokens)
export TES_URL=https://csc-tesk-noauth.rahtiapp.fi
# access token: see "Set the access token" (never as TES_TOKEN=... on the command line)
# hub port and chisel version (defaults)
export HUB_LISTEN_PORT=8090 CHISEL_VERSION=1.12.0
# Atlas stack images (defaults)
export DB_IMAGE=postgres:16-alpine WEBAPI_IMAGE=ohdsi/webapi:2.15.2 ATLAS_IMAGE=ohdsi/atlas:2.15.0
# Atlas stack dataset: Eunomia GiBleed (default)
export EUNOMIA_URL=https://raw.githubusercontent.com/OHDSI/EunomiaDatasets/main/datasets/GiBleed/GiBleed_5.3.zip
# WebAPI memory (defaults)
export WEBAPI_RAM_GB=1 WEBAPI_JAVA_OPTS="-Xmx640m -XX:MaxMetaspaceSize=192m -Xss512k -Djava.security.egd=file:///dev/./urandom"
# Atlas stack ports on the VM: Atlas on 8088 (8080 is the cloud-registry), WebAPI and DB defaults
export HUB_ATLAS_PORT=8088 HUB_WEBAPI_PORT=18081 HUB_DB_PORT=15432
# hub settings written by setup
cat tes-hub/.state/config
# the Atlas port is set permanently here
grep HUB_ATLAS_PORT ~/.bashrc
```

## Troubleshooting

```bash
# hub log: "Login failed" (locked-out old pod, or run the service's restart), "cannot listen" (old pod holds the port)
tail -f tes-hub/.state/hub.log
# failed logins per user today (locked-out pods that still use TESK capacity)
grep "^$(date +%Y/%m/%d).*Login failed" tes-hub/.state/hub.log | grep -o 'user "[a-z]*"' | sort | uniq -c
# restart the hub after a stop or crash
./tes-hub/tes-hub.sh start
# what holds a port on the VM (e.g. 8080 = cloud-registry container)
ss -ltn | grep -E ':(8080|8088|8787|8888|15432|18081)\b'
docker ps --format '{{.Names}}\t{{.Ports}}' | grep 8080
# RStudio shows "Unable to connect to service": short test task, check its output
./tes-hub/tes-service.sh rstudio-tesk selftest
# JupyterLab: short test task
./tes-hub/tes-service.sh jupyter-tesk selftest
# Atlas stack: short test task for the database or Atlas role
./omop-tesk/omop-tesk-fi.sh selftest db
# WebAPI answers through the tunnel (long timeout, it is slow)
curl -fsS -m 60 http://127.0.0.1:18081/WebAPI/info
# Atlas answers on the VM (HUB_ATLAS_PORT: 8088 on this VM, 8080 by default)
curl -fsS -m 30 -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:${HUB_ATLAS_PORT:-8080}/atlas/"
```

```bash
# create and generate a cohort through the WebAPI REST interface; expected: cohort <id> persons: 479
python3 - <<'EOF'
import json, os, time, urllib.request
W = f"http://127.0.0.1:{os.environ.get('HUB_ATLAS_PORT', '8080')}/WebAPI"
def call(method, path, body=None):
    req = urllib.request.Request(W + path, method=method, headers={"Content-Type": "application/json"},
                                 data=None if body is None else json.dumps(body).encode())
    with urllib.request.urlopen(req, timeout=120) as r:
        text = r.read().decode()
        return json.loads(text) if text.strip()[:1] in ("[", "{") else text

expression = {
    "ConceptSets": [{"id": 0, "name": "GI hemorrhage", "expression": {"items": [
        {"concept": {"CONCEPT_ID": 192671}, "includeDescendants": True}]}}],
    "PrimaryCriteria": {"CriteriaList": [{"ConditionOccurrence": {"CodesetId": 0}}],
                        "ObservationWindow": {"PriorDays": 0, "PostDays": 0},
                        "PrimaryCriteriaLimit": {"Type": "First"}},
    "QualifiedLimit": {"Type": "First"}, "ExpressionLimit": {"Type": "First"},
    "InclusionRules": [], "CensoringCriteria": [], "CollapseSettings": {"CollapseType": "ERA", "EraPad": 0},
    "CensorWindow": {}, "cdmVersionRange": ">=5.0.0"}

cohort = call("POST", "/cohortdefinition/", {"name": "GI bleed, first event (API)",
                                             "expressionType": "SIMPLE_EXPRESSION", "expression": expression})
call("GET", f"/cohortdefinition/{cohort['id']}/generate/EUNOMIA")
while True:
    info = call("GET", f"/cohortdefinition/{cohort['id']}/info")
    if info and info[0]["status"] == "COMPLETE":
        print("cohort", cohort["id"], "persons:", info[0]["personCount"]); break
    time.sleep(5)
EOF
```
