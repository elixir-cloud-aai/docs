# Use the Command Line

This page shows how to send tasks to a [GA4GH TES][ga4gh-tes] service in
ELIXIR On-Cloud from your terminal with `ga4gh-cli`, the command-line tool of
the [GA4GH SDK](https://github.com/ga4gh/ga4gh-sdk). The tool is at an early
stage and has no releases yet. This page describes what it does today,
including what it can't do yet.

!!! warning "What the CLI can't do yet"
    - **No authentication:** the CLI doesn't send an access token or any
      other credentials, even if they are in its configuration file. It can't
      use a service that requires an LS Login token.
    - **No proTES:** the CLI ignores the path in the service address, so it
      can't reach a service that serves its API only at `/ga4gh/tes/v1`, such
      as [proTES](../operators/services/protes.md).
    - **No WES:** the CLI has no commands for workflows.

    [Work without the CLI](#work-without-the-cli) shows how to reach these
    services with `curl` instead.

## Install

The project publishes no binaries or packages, so you build the CLI from its
source code. You need Git and [Rust](https://www.rust-lang.org/tools/install).

```bash
git clone https://github.com/ga4gh/ga4gh-sdk.git
cd ga4gh-sdk
git checkout 82432c3   # the commit that this page describes
cargo build
./target/debug/cli --version
```

The program is called `cli`, not `ga4gh-cli` as in the [CLI's
README](https://github.com/ga4gh/ga4gh-sdk/blob/main/cli/README.md). You can
copy it to a directory on your `PATH`. The commands below use the name `cli`.

Build the whole project with `cargo build`, as shown. `cargo build -p
ga4gh-cli` and `cargo install --path cli` currently fail with a compile
error in commit `82432c3`.

The build was tested on that commit in the `rust:1` container image (Rust
1.99.1), which comes with the system libraries that the build uses. The
project has no lock file, so your build can pick newer dependencies.

## Configure

The CLI reads the address of the service from `~/.ga4gh-cli/config.json`:

```json
{
  "TES": {
    "base_path": "http://localhost:8000",
    "basic_auth": null,
    "oauth_access_token": null
  }
}
```

- **All three keys must be there:** without `basic_auth` or
  `oauth_access_token`, the CLI stops with the error `no entry found for
  key`. Set them to `null`.
- **`base_path`:** use the scheme, the host and the port. The CLI ignores any
  path (see [Which services work](#which-services-work)).
- **One service at a time:** to use another service, edit the file. There are
  no profiles and no command-line option for the address.
- **No file:** without the file, the CLI uses `http://localhost`.

!!! danger "Don't put credentials in the configuration file"
    The file also accepts a user name and password (`basic_auth`) and a token
    (`oauth_access_token`). The CLI never sends them. Keep both set to `null`.

## Which services work

The CLI calls these paths on the host of `base_path`:

| Command | Request |
|---|---|
| all but `status` and `cancel` | `GET /service-info` |
| `tes create` | `POST /ga4gh/tes/v1/tasks` |
| `tes list` | `GET /tasks` |
| `tes get`, `tes status` | `GET /tasks/{id}` |
| `tes cancel` | `POST /tasks/{id}:cancel` |

A service must answer at all these paths, without authentication, and its
service info must have the type `tes`. [Funnel](../operators/services/funnel.md)
does. A service that serves its API only at `/ga4gh/tes/v1` answers `404` to
the first request, and the CLI reports `Error accessing the service`.

## Send and manage tasks

### Create a task

Write the task in a file, for example `task.json`. The [TES
specification][ga4gh-tes] describes all fields.

```json
{
  "name": "Hello world",
  "executors": [
    {
      "image": "alpine",
      "command": ["echo", "hello"]
    }
  ]
}
```

Then send it:

```bash
cli tes create task.json
```

The output is the ID of the new task and nothing else, so scripts can use it
directly:

```text
dbl8msskodig00bsscsg
```

The argument must be a file: the CLI doesn't accept the JSON text directly,
although its README shows that.

### List tasks

```bash
cli tes list
```

```text
TASK ID                   State
dbl8msskodig00bsscsg      Executor Error
```

| Option | What it does |
|---|---|
| `-n`, `--name_prefix` | Show only tasks whose name starts with this text. |
| `-s`, `--state` | Show only tasks in this state. Write the state with its double quotes: `-s '"COMPLETE"'`. Without them, the CLI crashes. |
| `-p`, `--page_size` | Ask for this number of tasks per page. |
| `-t`, `--page_token` | Ask for this page. The CLI doesn't show the token of the next page. |
| `-w`, `--view` | Send this view (`MINIMAL`, `BASIC` or `FULL`). The output stays the same. |

The options `-k` and `-v` (tags) are accepted, but ignored.

### Get a task

```bash
cli tes get <TASK_ID> FULL
```

The view is required: `MINIMAL`, `BASIC` or `FULL`. The CLI prints the task in
the internal format of the program, not as JSON.

### Get the status of a task

```bash
cli tes status <TASK_ID>
```

```text
TASKID: dbl8msskodig00bsscsg
STATUS: ExecutorError
```

### Cancel a task

```bash
cli tes cancel <TASK_ID>
```

### Check for errors

If the service answers `tes create` or `tes list` with an error, the CLI writes
the message to stderr, leaves stdout empty and still ends with the exit code
`0`. In scripts, check for empty stdout, not the exit code:

```bash
TASK_ID=$(cli tes create task.json)
if [ -z "$TASK_ID" ]; then
  echo "The task was not created" >&2
  exit 1
fi
```

This check also covers failures that do change the exit code: if the CLI can't
read the task file or reach the service, or if the service info is missing or
not of the type `tes`, it ends with the exit code `1` and stdout stays empty.

`tes get` works differently: it prints `Err(...)` to stdout, also with the exit
code `0`, so look for that text in its output instead. `tes status` and
`tes cancel` report errors on stderr and end with the exit code `1`.

## Authentication

The CLI can't send a bearer token, such as an LS Login access token. No setting
changes this: the SDK reads the values from the file, but no request carries an
`Authorization` header. This also applies to the WES client of the SDK's Rust
library.

## Work without the CLI

For a service that needs a token, get an access token as [Using the
APIs](../partners-and-developers/apis.md#2-get-an-access-token) describes, then
call the API with `curl`. Replace `<HOST>` with the address of the service, and
ask its operators which tokens they accept.

```bash
unset TOKEN      # so that the token can't stay exported to other programs
read -rs TOKEN   # paste the token; it is not shown or saved in the history
```

With `--fail-with-body`, `curl` shows the answer of the service and ends with
an error code if the service reports an error.

Send a task to a TES service such as proTES:

```bash
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl --fail-with-body -X POST "https://<HOST>/ga4gh/tes/v1/tasks" -H @- -H 'Content-Type: application/json' -d @task.json
```

Read the task:

```bash
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl --fail-with-body "https://<HOST>/ga4gh/tes/v1/tasks/<TASK_ID>?view=BASIC" -H @-
```

Send a workflow to a WES service. The path and the supported workflow types
depend on the service; the [WES
specification](https://github.com/ga4gh/workflow-execution-service-schemas)
describes the fields.

```bash
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl --fail-with-body -X POST "https://<HOST>/ga4gh/wes/v1/runs" -H @- \
  -F workflow_type=CWL \
  -F workflow_type_version=v1.2 \
  -F workflow_url=https://example.org/workflow.cwl \
  -F 'workflow_params={}'
```

## How this page was tested

We built the CLI at commit `82432c3` of the SDK and ran it in the `rust:1`
container image, on one computer:

- **Funnel in a container, no authentication:** all `tes` commands reached
  the service, and `tes create` printed only the ID. The test task ended in
  `EXECUTOR_ERROR`, because the container has no Docker to run it with, so no
  task was seen to finish.
- **Local mock service:** it recorded the requests of the CLI. With a token and
  a password in the configuration, none of them had an `Authorization`
  header. With the API only at `/ga4gh/tes/v1`, as in proTES, the requests went
  to the wrong paths and failed. When it answered with errors, or when no
  service was listening, the CLI behaved as [Check for
  errors](#check-for-errors) describes, and the script there stopped.
- **`curl`:** the commands above were sent to the mock service over HTTP, not
  HTTPS, with the token passed to `read` by a redirect instead of being pasted.
  The mock service recorded the token for all of them. It has no WES API and
  answered the workflow request with `404`.

We did not test against a deployed service, a real proTES or a real WES
service, and we saw no task finish.

## Where to go next

- The [GA4GH SDK repository](https://github.com/ga4gh/ga4gh-sdk) and the
  [CLI's README](https://github.com/ga4gh/ga4gh-sdk/blob/main/cli/README.md).
  The project has no other user docs yet.
- Open requests for the SDK: [WES commands](https://github.com/ga4gh/ga4gh-sdk/issues/51),
  [basic authentication](https://github.com/ga4gh/ga4gh-sdk/issues/31) and
  [several service profiles](https://github.com/ga4gh/ga4gh-sdk/issues/47).
- Questions: the [Discussions][elixir-on-cloud-forum] or the
  [About](../about.md) page.
