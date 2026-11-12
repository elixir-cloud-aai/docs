# Run Interactive Services on TES

This page shows how to run interactive web services, such as RStudio Server,
JupyterLab, or OHDSI Atlas with an OMOP CDM database, as tasks of a [GA4GH
TES][ga4gh-tes] service, and how to open them in your browser. A TES service
can't publish the port of a task, so each task connects to a tunnel hub on a
virtual machine that you run. The [commands
page](interactive_services_tes_commands.md) has all commands without the
explanations.

!!! warning "Under construction"
    The deployment offers no tunnel hub, so you need your own virtual machine
    that the tasks can reach over HTTPS. The scripts were tested with one TES service
    only, the [TESK][tesk] of ELIXIR-FI, and not with the TES services of other
    Nodes or with proTES (see [How this page was
    tested](#how-this-page-was-tested)). For help, write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email].

!!! danger "Use synthetic data only"
    Whoever may read your tasks on the TES service (on a service without
    tokens: anyone) can read a task with `?view=FULL`, including the
    passwords of the hub and of the database that the scripts put into it.
    RStudio, JupyterLab and Atlas have no login. Don't use real or sensitive
    data with this setup.

## How it works

A TESK task can only make outbound HTTPS connections. Each task therefore
downloads [chisel](https://github.com/jpillora/chisel) and connects over
HTTPS to a chisel server on your virtual machine, the hub. nginx on the
virtual machine accepts the connection on the public HTTPS port and passes
it to the hub, which listens on `127.0.0.1:8090` only. The port of the
service then appears as `127.0.0.1:<PORT>` on the virtual machine, and you
forward it to your computer with SSH:

```text
On the virtual machine <HOST>:

  browser --ssh -L--> 127.0.0.1:8787  <-- hub 127.0.0.1:8090  <-- nginx :443 /tes-tunnel/
                                                                    ^
                                                                    | websocket over HTTPS
In the TES task:                                                    |
  RStudio 127.0.0.1:8787  <-- chisel client ------------------------+
```

- **One hub user per service:** each service gets its own user and password
  on the hub, and may open only its own ports. A password that someone reads
  from a task can't open other ports.
- **The task checks the hub:** the task gets the fingerprint of the hub's
  key, and refuses a server with another key.
- **A keep-alive loop:** a loop on the virtual machine sends a new task when
  the old one ends. If the old pod still holds the port, the loop first
  locks it out (see the next point).
- **Stopping locks the old task out:** on the TESK of ELIXIR-FI, a cancelled
  task is marked `CANCELED`, but its pod keeps running and its tunnel stays
  connected. `down` therefore first gives the service a new password and
  restarts the hub, and then cancels the task. The other tunnels reconnect
  within about 30 seconds.

| File | What it does |
|---|---|
| [`tes-hub/tes-hub.sh`](tes-hub/tes-hub.sh) | Runs the hub on the virtual machine. |
| [`tes-hub/common.sh`](tes-hub/common.sh) | Runs first in every task. Downloads chisel and opens the tunnel. |
| [`tes-hub/tes-api.sh`](tes-hub/tes-api.sh) | Sends the requests of the launchers to the TES service, with your access token. |
| [`tes-hub/tes-service.sh`](tes-hub/tes-service.sh) | Runs a service that fits into one container image, from a directory with a `service.conf` and a `pod.sh`. |
| [`rstudio-tesk/service.conf`](rstudio-tesk/service.conf), [`rstudio-tesk/pod.sh`](rstudio-tesk/pod.sh) | RStudio Server, with the image `rocker/rstudio`. |
| [`omop-tesk/omop-tesk-fi.sh`](omop-tesk/omop-tesk-fi.sh) | Runs the Atlas stack as three tasks, which reach each other through the hub. |
| [`omop-tesk/pod/db.sh`](omop-tesk/pod/db.sh) | Postgres with the [Eunomia](https://github.com/OHDSI/EunomiaDatasets) GiBleed demo CDM. Registers the CDM as a data source of WebAPI. |
| [`omop-tesk/pod/webapi.sh`](omop-tesk/pod/webapi.sh) | OHDSI WebAPI. |
| [`omop-tesk/pod/atlas.sh`](omop-tesk/pod/atlas.sh) | The Atlas web interface. Forwards `/WebAPI/` to the WebAPI task. |

Each script keeps what it generates in a folder `.state` next to it: the
passwords (readable only by you), the task IDs and the logs.

## What you need

- A Linux virtual machine (x86-64 or ARM64) with `bash`, `curl`, `python3`,
  `ss`, `setsid` and `flock`, that you can reach with SSH. The services run on the TES service, not on
  the virtual machine.
- A public host name for the virtual machine (`<HOST>` below), and port 443
  open to the internet. The tasks must reach this port: the TESK of
  ELIXIR-FI allows outbound HTTPS, and other ports were not tested.
- nginx and a TLS certificate for `<HOST>` on the virtual machine, for
  example from [Let's Encrypt](https://letsencrypt.org/) with
  [Certbot](https://certbot.eff.org/). The hub itself speaks plain HTTP.
- A TES service whose tasks can make outbound HTTPS connections, and an
  access token for it if it needs one (see [Get an access
  token](#get-an-access-token)). The scripts use the TESK of ELIXIR-FI
  (`https://csc-tesk-noauth.rahtiapp.fi`). To use another service, set
  `TES_URL`.

!!! note "The default address will change"
    The TES services of ELIXIR On-Cloud move to access with tokens. The
    default `TES_URL` will change to the address of the TESK of ELIXIR-FI
    with tokens once that is published. Until then, set `TES_URL` to the
    address that you were given.

## Set up the hub

### 1. Install the scripts

Copy the scripts to the virtual machine, in the folders of the table above,
for example into `~/eoc_services`. The [commands
page](interactive_services_tes_commands.md#install-the-scripts) has a block
that creates all files when you paste it. Then make the launchers
executable:

```bash
cd ~/eoc_services
chmod +x tes-hub/tes-hub.sh tes-hub/tes-service.sh omop-tesk/omop-tesk-fi.sh
```

### 2. Start the hub

Replace `<HOST>` with the public host name of the virtual machine. The last
argument makes the hub listen on `127.0.0.1` only, so that it is reachable
through nginx only:

```bash
./tes-hub/tes-hub.sh setup https://<HOST>/tes-tunnel/ 127.0.0.1
```

`setup` downloads chisel, creates the key of the hub and its list of users,
prints the configuration for nginx (step 3) and starts the hub on port
8090. The hub doesn't start again after a reboot of the virtual machine:
then run `./tes-hub/tes-hub.sh start`.

### 3. Add the path to nginx

Add the block that `setup` printed to the HTTPS `server` block of `<HOST>`
(the one with `listen 443 ssl`), and reload nginx with
`sudo systemctl reload nginx`:

```nginx
location /tes-tunnel/ {
    proxy_pass http://127.0.0.1:8090/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 1d;
    proxy_send_timeout 1d;
    proxy_buffering off;
}
```

The long timeouts keep tunnels open while no one uses them. Don't open port
8090, or the ports of the services, in the firewall: they must stay on
`127.0.0.1`.

### 4. Check the hub

```bash
./tes-hub/tes-hub.sh status
```

The output must contain `proxy route OK`. The hub answers requests without
a tunnel with `Not found`, so `curl https://<HOST>/tes-tunnel/` must return
exactly this text.

## Get an access token

The TES services of ELIXIR On-Cloud accept only requests with an access
token of [LS Login](https://www.lifescience-ri.eu/life-science-login/). To
run tasks, your LS Login account must be a member of the ELIXIR On-Cloud
compute group `ECP_CLN:EOC-Compute` (members of `ECP_CLN:ADMIN` may run tasks
too). To join the group, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email].

1. Get an access token of your LS Login account from the web interface of
   the deployment that you use, or as [Using the
   APIs](../../partners-and-developers/apis.md#2-get-an-access-token)
   describes. A token lives for about 4 hours.
2. Set it in the shell in which you run the scripts. With `read -s`, the
   token is neither shown nor saved in the shell history:

    ```bash
    read -rsp 'TES token: ' TES_TOKEN && echo && export TES_TOKEN
    ```

If `TES_TOKEN` is set, the scripts send it with every request to the TES
service, in the header `Authorization: Bearer`. They pass it to `curl`
through a pipe, so that it doesn't appear on a command line, and they don't
write it to files or logs. Without `TES_TOKEN`, they send no token, for TES
services that don't need one.

Each command that uses the TES service first checks the token, and ends
with an error if the service refuses it:

| Answer | Meaning | What to do |
|---|---|---|
| `401 Unauthorized` | No token, or the token is invalid or has expired. | Get a new token and set `TES_TOKEN` again. |
| `403 Forbidden` | The token is valid, but your account may not run tasks. | Ask for membership in `ECP_CLN:EOC-Compute`. |

The keep-alive loop keeps the token that it started with, in its
environment. When the token has expired, the loop writes the error to its
log and sends no new tasks, but running tasks go on. Get a new token, set
`TES_TOKEN` and run `up` again: with `TES_TOKEN` set, `up` replaces the
loop, so that it uses the new token.

## Start RStudio Server

```bash
./tes-hub/tes-service.sh rstudio-tesk selftest   # optional: a short task without tunnel; fails unless it prints SELFTEST_OK
./tes-hub/tes-service.sh rstudio-tesk up
```

`up` creates the hub user `rstudio` the first time, sends the task, starts
the keep-alive loop and waits until the tunnel is up, usually 1 to 3
minutes. It doesn't send a second task while one runs. On your computer,
forward the port, then open <http://localhost:8787>:

```bash
ssh -N -L 8787:127.0.0.1:8787 <USER>@<VM>
```

The task runs as a random user without root, so the image can't start
RStudio as usual. `pod.sh` starts RStudio Server directly, without login,
and gives R a home folder in `/tmp/home`.

## Start Atlas with OMOP demo data

```bash
./omop-tesk/omop-tesk-fi.sh selftest db   # optional: loads the CDM in a short task; fails unless it prints SELFTEST_OK
./omop-tesk/omop-tesk-fi.sh up
```

`up` creates the hub user `omop` and a password for the database the first
time, sends three tasks and starts the keep-alive loop:

| Task | Image | Port on the virtual machine |
|---|---|---|
| `db` | `postgres:16-alpine`, with the Eunomia GiBleed CDM 5.3 | 15432 |
| `webapi` | `ohdsi/webapi:2.15.2`. Reaches the database through the hub. | 18081 |
| `atlas` | `ohdsi/atlas:2.15.0`. Reaches WebAPI through the hub. | 8080 (`HUB_ATLAS_PORT`) |

When WebAPI runs, the `db` task creates the results schema and registers
the CDM as the data source `EUNOMIA`. The first start takes 10 to 15
minutes, because WebAPI creates its tables. `up` waits up to 40 minutes,
until Atlas answers and WebAPI lists the data source. All three tasks share
one hub user, so the keep-alive loop replaces the whole stack when the
database ends: a new database is empty.
Then forward the port and open <http://localhost:8080/atlas/>:

```bash
ssh -N -L 8080:127.0.0.1:8080 <USER>@<VM>
```

If another program uses port 8080 on the virtual machine, choose another
port before the first `up`, for example `export HUB_ATLAS_PORT=8088`, and
keep it set, for example in `~/.bashrc`.

To check Atlas, create a cohort through WebAPI with the Python script on
the [commands page](interactive_services_tes_commands.md#troubleshooting).
It must report 479 persons.

## Add your own service

`tes-service.sh` runs any web service that fits into one container image.
Create a folder next to `tes-hub` with two files:

- **`service.conf`:** `NAME` (the hub user and the name of the task),
  `IMAGE`, and `PORT` (the port of the service in the task). Optional:
  `HUB_PORT` (the port on the virtual machine, by default `PORT`), `RAM_GB`
  and `CPU_CORES` (by default 1), and `POD_SHELL` (by default `/bin/sh`).
  The task gets every other `KEY=value` as an environment variable.
- **`pod.sh`:** runs in the task after `common.sh`. It starts the service
  on `127.0.0.1:$PORT`, calls
  `start_tunnel "R:127.0.0.1:${HUB_PORT}:127.0.0.1:${PORT}"` and keeps
  running. With `SELFTEST=1`, it checks the service and ends instead.

The [commands
page](interactive_services_tes_commands.md#add-jupyterlab-as-your-own-service)
has an example for JupyterLab. Start it with
`./tes-hub/tes-service.sh jupyter-tesk up` and forward port 8888.

## Manage the services

`tes-service.sh` and `omop-tesk-fi.sh` have the same commands:

| Command | What it does |
|---|---|
| `status` | Shows the state of the task, the tunnel and the keep-alive loop. |
| `logs` | Shows the logs of the task. The TESK of ELIXIR-FI fills them only when the task ends. |
| `print` | Shows the TES task that the script would send. |
| `restart` | Replaces the service with a new one (`down`, then `up`). |
| `down` | Stops the keep-alive loop, locks the old task out of the hub and cancels it. |

For example: `./tes-hub/tes-service.sh rstudio-tesk status` or
`./omop-tesk/omop-tesk-fi.sh logs webapi`. `./tes-hub/tes-hub.sh status`
shows the hub, the path in nginx and all tunnels.

After a reboot of the virtual machine, start the hub, set `TES_TOKEN`, then
run `up` for each service. Running tasks reconnect by themselves, and `up` starts the
keep-alive loop again.

## Limits

- **1 GB of memory and no disk:** on the TESK of ELIXIR-FI, tasks that asked
  for more than 1 GB of memory or for any disk (`disk_gb`) didn't start
  (October 2026). WebAPI therefore runs with a small Java heap
  (`WEBAPI_JAVA_OPTS`).
- **Nothing is kept:** files, R packages and the database are in `/tmp` of
  the task. They are lost when the task ends or is replaced. Copy out what
  you want to keep.
- **WebAPI 2 only:** the WebAPI 3 images (`ohdsi/webapi:latest` since
  November 2026) start differently, and `pod/webapi.sh` doesn't support them
  yet. Keep `WEBAPI_IMAGE` at a 2.x version.
- **Outbound HTTPS only:** tasks can download files, for example from
  GitHub, but can't use other ports, for example SSH.
- **Old tasks keep running:** locked-out tasks keep running and use
  resources of the TES service, until its operators delete them. When you
  are done, ask them to delete the tasks.

## Settings

To change a default, set the environment variable before you run a script:

| Variable | Default | Used by |
|---|---|---|
| `TES_URL` | `https://csc-tesk-noauth.rahtiapp.fi` (will change, see [What you need](#what-you-need)) | all scripts |
| `TES_TOKEN` | none: no token is sent (see [Get an access token](#get-an-access-token)) | all scripts |
| `HUB_LISTEN_PORT` | `8090` (`setup` saves it) | `tes-hub.sh` |
| `CHISEL_VERSION` | `1.12.0` | `tes-hub.sh` |
| `WATCH_INTERVAL` | `60` (seconds) | the keep-alive loops |
| `HUB_ATLAS_PORT`, `HUB_WEBAPI_PORT`, `HUB_DB_PORT` | `8080`, `18081`, `15432` | `omop-tesk-fi.sh` |
| `DB_IMAGE`, `WEBAPI_IMAGE`, `ATLAS_IMAGE` | `postgres:16-alpine`, `ohdsi/webapi:2.15.2`, `ohdsi/atlas:2.15.0` | `omop-tesk-fi.sh` |
| `EUNOMIA_URL` | the GiBleed CDM 5.3 of [EunomiaDatasets](https://github.com/OHDSI/EunomiaDatasets) | `omop-tesk-fi.sh` |
| `WEBAPI_RAM_GB`, `WEBAPI_JAVA_OPTS` | `1`, `-Xmx640m -XX:MaxMetaspaceSize=192m ...` | `omop-tesk-fi.sh` |

## Troubleshooting

- **`401 Unauthorized` or `403 Forbidden`:** the TES service refused the
  token, see [Get an access token](#get-an-access-token). If the keep-alive
  loop stops replacing a service after a few hours, its token has expired:
  its log `.state/watch.log` shows the error. Set a new token and run `up`
  again.
- **`proxy route not working`:** the hub doesn't run (start it with
  `./tes-hub/tes-hub.sh start`), or the path is missing in nginx. If
  `curl https://<HOST>/tes-tunnel/` returns HTML or a redirect, the request
  doesn't reach the hub.
- **`tunnel not connected`, but the task is `RUNNING`:** an old task holds
  the port. The hub log `tes-hub/.state/hub.log` then shows
  `cannot listen on R:127.0.0.1:<PORT>`. Run `restart` for the service.
- **`Login failed for user "<NAME>"` in the hub log:** a locked-out old task
  tries to reconnect. It does no harm, but uses resources of the TES
  service.
- **The task stays `QUEUED`, or `RUNNING` without output:** the task asks
  for too many resources. Keep `RAM_GB=1` and don't ask for disk.
- **RStudio shows `Unable to connect to service`:** the R session can't
  start. Run `selftest` and read its output.
- **Atlas has no data source:** WebAPI is still starting, or the `db` task
  ended. Check with `./omop-tesk/omop-tesk-fi.sh status`. If the database
  ended while WebAPI runs, run `restart`: a new database is empty.

## How this page was tested

During the BioHackathon Europe 2026 (project 27), the project team ran the
scripts on one virtual machine with the TESK of ELIXIR-FI, behind the
reverse proxy of `elixir-on.cloud`. According to the notes of the project,
RStudio Server, JupyterLab, and Atlas with the Eunomia data worked, and a
cohort created through WebAPI had 479 persons.

This page fixes and changes the scripts of the project. Among others, the
script of the database task is named `db.sh`, `rstudio-tesk/service.conf`
is filled in, and the OMOP images are pinned to `ohdsi/webapi:2.15.2` and
`ohdsi/atlas:2.15.0`, because `ohdsi/webapi:latest` (WebAPI 3.0.1) doesn't
start with `pod/webapi.sh`.

We tested the changed scripts on a second virtual machine, without TESK:
a small local TES service ran each task as a Docker container with a
random user ID and 1 GB of memory, and, like the TESK of ELIXIR-FI, kept a
container running when its task was cancelled. It also gave the random
user ID an entry in `/etc/passwd`, which RStudio Server needs. The hub ran
on the virtual machine, and the tasks connected to it over HTTP, without
nginx:

- **Self-tests:** `selftest` passed for RStudio, `db` and `atlas`, and
  failed for RStudio without the entry in `/etc/passwd`.
- **Services:** RStudio answered through the tunnel. The Atlas stack was
  ready within a few minutes, and a cohort created through WebAPI had 479
  persons.
- **Replacing and stopping:** after a cancel, the keep-alive loop locked the
  still-running container out and the new task got the port. After `down`,
  no task was sent again, and all tunnels were closed.

We did not run the changed scripts on the TESK of ELIXIR-FI, and did not
test nginx with TLS or JupyterLab.

We tested the access tokens against a small mock of a TES service that
required tokens, with a stand-in for the hub: without a token, with an
invalid one and with one outside the compute group, every command ended
after its first request with the matching error. With a valid token,
`selftest`, `up`, `status`, `logs`, `print` and `down` worked for both
launchers, `up` replaced the keep-alive loop, and the loop logged the error
when the token expired. The token appeared in no command line, file or log.
We did not test the tokens against a real TES service.

## Where to go next

- [Interactive Services on TES: Commands](interactive_services_tes_commands.md)
- [chisel](https://github.com/jpillora/chisel), [TESK][tesk], and the
  [TESK page](../../operators/services/tesk.md) for operators.
- [OHDSI Atlas](https://github.com/OHDSI/Atlas),
  [WebAPI](https://github.com/OHDSI/WebAPI) and the [Rocker
  images](https://rocker-project.org/images/).
- To send other tasks to a TES service: [Use the Command
  Line](../../researchers/cli.md).
- Questions: the [Discussions][elixir-on-cloud-forum] or the
  [About](../../about.md) page.
