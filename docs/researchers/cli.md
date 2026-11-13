# Use the Command Line

This page shows how to use the services of ELIXIR On-Cloud from your terminal
with `ga4gh-cli`, the command-line tool of the [GA4GH
SDK](https://github.com/ga4gh/ga4gh-sdk): find services in the Cloud
Registry, log in with an LS Login token, send tasks to a [GA4GH
TES][ga4gh-tes] service such as the proTES gateway, run workflows on a [GA4GH
WES][ga4gh-wes] service, find workflows in a [GA4GH TRS][ga4gh-trs] registry
such as WorkflowHub, and look up objects in a [GA4GH DRS][ga4gh-drs] service.
The tool is at an early stage and has no releases yet. This page describes
what it does today and what is planned. For the full reference, see the
[SDK's own docs](#where-to-go-next).

!!! warning "What the CLI can't do yet"
    - **No ready-made binaries:** you build the CLI from its source code.

## What works now

| Commands | Service | What you do |
|---|---|---|
| `ga4gh-cli registry` | GA4GH Service Registry, such as the Cloud Registry | [Find services](#find-services-in-the-cloud-registry) and their addresses. |
| `ga4gh-cli tes` | GA4GH TES, such as proTES, TESK or Funnel | [Create, list, read and cancel tasks](#run-tasks-with-tes). |
| `ga4gh-cli wes` | GA4GH WES, such as WESkit or cwl-WES | [Start runs of workflows, follow and cancel them](#run-workflows-with-wes). |
| `ga4gh-cli trs` | GA4GH TRS, such as WorkflowHub or Dockstore | [Find workflows and download their files](#find-workflows-with-trs). |
| `ga4gh-cli drs` | GA4GH DRS, such as DRS-Filer | [Read the metadata and access URLs of objects](#look-up-objects-with-drs). |

All commands can send a token to the service, such as an [LS
Login](#log-in-with-ls-login) access token. The CLI also has experimental
`workflow` commands for client-side checks of workflow runs; this page doesn't
cover them (see the SDK's [workflow contracts
guide](https://github.com/ga4gh/ga4gh-sdk/blob/main/docs/workflow-contracts.md)).

## Install

The project publishes no binaries or packages, so you build the CLI from its
source code. You need Git and [Rust](https://www.rust-lang.org/tools/install),
installed with `rustup`. The repository pins the version of Rust that it
needs, and `rustup` installs it on the first build.

```bash
git clone https://github.com/ga4gh/ga4gh-sdk.git
cd ga4gh-sdk
git checkout af0e021   # the commit that this page describes
cargo install --path cli --locked
ga4gh-cli --version
```

`cargo install` puts the program `ga4gh-cli` into `~/.cargo/bin`, which
`rustup` adds to your `PATH`. Without `git checkout`, you get the latest
version, which can differ from this page. See
[Installation](https://github.com/ga4gh/ga4gh-sdk#installation) in the SDK's
README.

## Configure

The CLI reads the addresses of the services from `~/.ga4gh-cli/config.json`.
It has one section per kind of service: `REGISTRY`, `TES`, `WES`, `TRS` and
`DRS`. To start, point the CLI at the Cloud Registry of ELIXIR On-Cloud and at
WorkflowHub, which you can both read without a token. The commands below
create the file only if it doesn't exist yet; to change an existing file, edit
it in a text editor instead, so that its other sections stay.

```bash
mkdir -p ~/.ga4gh-cli
[ -e ~/.ga4gh-cli/config.json ] || cat > ~/.ga4gh-cli/config.json <<'JSON'
{
  "REGISTRY": {
    "base_path": "https://elixir-on.cloud/ga4gh/registry/v1"
  },
  "TRS": {
    "base_path": "https://workflowhub.eu/ga4gh/trs/v2"
  }
}
JSON
chmod 600 ~/.ga4gh-cli/config.json
```

Add a section for each other service that you use, for example:

```json
{
  "REGISTRY": {
    "base_path": "https://elixir-on.cloud/ga4gh/registry/v1"
  },
  "TRS": {
    "base_path": "https://workflowhub.eu/ga4gh/trs/v2"
  },
  "TES": {
    "base_path": "https://<HOST>/ga4gh/tes/v1",
    "oauth_access_token_env": "LS_LOGIN_TOKEN"
  },
  "WES": {
    "base_path": "https://<HOST>/ga4gh/wes/v1",
    "oauth_access_token_env": "LS_LOGIN_TOKEN"
  },
  "DRS": {
    "base_path": "https://<HOST>/ga4gh/drs/v1"
  }
}
```

- **`base_path` is the API root:** the scheme, the host and the path of the
  API, such as `/ga4gh/tes/v1` for [proTES](../operators/services/protes.md).
  A trailing slash is optional; a query string or fragment isn't allowed. A
  service behind a gateway keeps its whole path, for example
  `https://gateway.example.org/my-tes/ga4gh/tes/v1`.
- **Only `base_path` is required.** A missing file, or a missing section for
  the command that you run, is an error, for example `Configuration file must
  contain a 'TES' object`.
- **`oauth_access_token_env` names a variable that holds your token,** not the
  token itself. See [Log in with LS Login](#log-in-with-ls-login).

### Use several deployments with profiles

A section holds one service of each kind. To switch between deployments, for
example the services of ELIXIR On-Cloud and a local test service, put the
sections into named profiles:

```json
{
  "default_profile": "elixir",
  "profiles": {
    "elixir": {
      "REGISTRY": {
        "base_path": "https://elixir-on.cloud/ga4gh/registry/v1"
      },
      "TES": {
        "base_path": "https://<HOST>/ga4gh/tes/v1",
        "oauth_access_token_env": "LS_LOGIN_TOKEN"
      }
    },
    "local": {
      "TES": {
        "base_path": "http://localhost:8000/ga4gh/tes/v1"
      }
    }
  }
}
```

Choose a profile with `--profile`, before or after the command, or with the
variable `GA4GH_CLI_PROFILE`:

```bash
ga4gh-cli --profile local tes list
GA4GH_CLI_PROFILE=local ga4gh-cli tes list
```

`--profile` wins over the variable, and the variable over `default_profile`.
Without any of them, the CLI uses the profile `default`. A file without
`profiles`, as in [Configure](#configure), counts as the profile `default`. An
unknown profile is an error that lists the profiles in the file, for example
`Profile 'nope' not found; profiles in the configuration file: elixir, local`.

## Log in with LS Login

[LS Login](https://www.lifescience-ri.eu/life-science-login/) is the identity
provider of ELIXIR On-Cloud. Services that need a login, such as proTES or a
WES, accept an LS Login access token. The CLI sends the token with every
request to a service whose section names it, including the first request that
checks the service (`service-info`).

1. **Get an access token** as [Using the
   APIs](../partners-and-developers/apis.md#2-get-an-access-token)
   describes, and ask the operators of the service which LS Login clients it
   accepts. The CLI doesn't log in itself: it sends the token that you give
   it.
2. **Put the token into a variable** in the terminal where you use the CLI.
   The token isn't shown and isn't saved in the history of the shell:

    ```bash
    read -rs LS_LOGIN_TOKEN   # paste the token, then press Enter
    export LS_LOGIN_TOKEN
    ```

3. **Name the variable in the section of each service** that needs the
   token, with `"oauth_access_token_env": "LS_LOGIN_TOKEN"`, as in the
   example in [Configure](#configure). Sections without it, such as
   `REGISTRY`, send no token.

Access tokens expire after a while. When a service answers `401
Unauthorized`, get a new token and repeat step 2.

Every program that you start from this terminal while the variable is set can
read the token. Start only the CLI and programs you trust there, and remove the
token when you're done, or close the terminal:

```bash
unset LS_LOGIN_TOKEN
```

!!! danger "Keep the token out of the configuration file"
    The section can also hold the token itself (`oauth_access_token`), but
    then the file keeps it on disk. Use `oauth_access_token_env` instead.
    Send tokens only over `https`: if `base_path` of a remote service starts
    with `http:`, the CLI warns, but still sends the token, which anyone on
    the network path can then read and use. Never name the variable in a
    section whose `base_path` starts with `http:`, unless it points at your
    own computer (`localhost`).

If the variable isn't set, the CLI stops before it sends a request, for
example with `Environment variable 'LS_LOGIN_TOKEN' is not set; it is named by
oauth_access_token_env in 'TES'`. A section may name only one source of
credentials; the [authentication
guide](https://github.com/ga4gh/ga4gh-sdk/blob/main/docs/authentication.md)
of the SDK lists the others, such as HTTP Basic.

## Find services in the Cloud Registry

The [Cloud Registry](../operators/using-cloud-registry.md) lists the services
of ELIXIR On-Cloud. Anyone can read it without a token, so the `registry`
commands work with the configuration above.

!!! info "Few services are listed yet"
    The deployment doesn't publish the addresses of all its TES, DRS and WES
    services for researchers yet (see [Researchers: Start
    Here](index.md#before-you-start)). Until then, the list is short. Write
    to [cloud-service@elixir-europe.org][elixir-on-cloud-email] to ask for
    services that you can use.

List all services:

```bash
ga4gh-cli registry list
```

```text
ID      TYPE                              URL
GC6ZQG  org.ga4gh:tes:unknown             https://spe4hd.tes.bihealth.org/ga4gh/tes/v1
J0LBQG  org.ga4gh:service-registry:1.0.0  https://elixir-on.cloud/ga4gh/registry/v1
```

List only the services of one API, by the artifact of their type (`tes`,
`wes`, `drs`, `trs`, …; case is ignored):

```bash
ga4gh-cli registry list --type tes
```

Show all details of one service, such as its description and operator, by its
ID, as JSON:

```bash
ga4gh-cli registry get GC6ZQG
```

List the API types that the registry knows, one `group:artifact:version` per
line:

```bash
ga4gh-cli registry types
```

To use a service that you found, copy its `URL` into `base_path` of the
section for its API, such as `TES`. If the URL ends before the path of the API
(for example, without `/ga4gh/tes/v1`), add the path from the docs of the
product. If `base_path` is wrong, the CLI ends with a `404` error and the hint
`Check that base_path is the TES API root`. A service in the registry doesn't
always accept your token: ask its operators.

The commands show only the fields of the Service Registry specification. The
labels of the Cloud Registry, such as whether a service is
[verified](../operators/using-cloud-registry.md#verified-services), aren't
shown: check them in the [front end][elixir-cloud-registry] before you trust a
service.

## Run tasks with TES

Add a `TES` section to the configuration, as shown above. To send tasks
through the gateway of ELIXIR On-Cloud, set `base_path` to the address of
[proTES](../operators/services/protes.md), which forwards each task to the
TES service of a Node. If the service needs a login, add
`oauth_access_token_env` (see [Log in with LS Login](#log-in-with-ls-login)).

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
TASK_ID=$(ga4gh-cli tes create task.json)
echo "$TASK_ID"
```

The output is the ID of the new task and nothing else, so scripts can use it
directly. Instead of a file name, you can also pass the JSON text itself, or
`-` to read it from standard input:

```bash
cat task.json | ga4gh-cli tes create -
```

The CLI checks the task before it sends it: text that isn't JSON fails with
`Failed to parse JSON`, and a task that doesn't match the TES specification,
such as an executor without `image`, fails with `Invalid TES task`. With
`--format json`, the output is `{"id":"…"}`, for programs that read the ID.

### List tasks

```bash
ga4gh-cli tes list
```

```text
TASK ID                   State
task1                     Complete
task2                     Canceled
```

| Option | What it does |
|---|---|
| `-n`, `--name_prefix` | Show only tasks whose name starts with this text. |
| `-s`, `--state` | Show only tasks in this state, such as `COMPLETE` or `"executor error"`; case is ignored. |
| `-k`, `--tag_key` and `-v`, `--tag_value` | Show only tasks with this tag. Repeat both for several tags; the values match the keys in the same order. |
| `-p`, `--page_size` | Ask for this number of tasks per page. |
| `-t`, `--page_token` | Ask for this page. If there are more pages, the CLI prints `Next page token: …` after the table. |
| `-w`, `--view` | Ask for this view: `MINIMAL`, `BASIC` or `FULL`. The table stays the same. |
| `--all --format jsonl` | Fetch all pages and print one task per line as JSON. |
| `--max-pages`, `--max-items` | Stop `--all` after this number of pages (default: 1000) or tasks. |

If `--all` stops at a limit, the tasks so far stay on stdout, and the CLI ends
with the exit code `1` and writes a resume checkpoint to stderr:

```bash
ga4gh-cli tes list --all --format jsonl --max-items 100 > tasks.jsonl
```

### Get a task

```bash
ga4gh-cli tes get "$TASK_ID" FULL
```

The view is required: `MINIMAL`, `BASIC` or `FULL`, in any case. The CLI
prints the JSON of the service, without a final line break; pipe it to a tool
such as `jq` to format it.

### Get the state of a task

```bash
ga4gh-cli tes status "$TASK_ID"
```

```text
QUEUED
```

The CLI prints the TES state, such as `RUNNING`, `COMPLETE` or
`EXECUTOR_ERROR`, or `UNKNOWN` for a state that the TES specification doesn't
define. `tes get` shows the state as the service sent it.

### Cancel a task

```bash
ga4gh-cli tes cancel "$TASK_ID"
```

### Check for errors

All `tes` commands end with the exit code `0` on success and `1` on errors,
for example when the service rejects a task or can't be reached. The message
goes to stderr, with the HTTP status, such as `Request failed with status: 401
Unauthorized`. The CLI doesn't print the answer of the service, which could
repeat your token. A missing command or argument ends with the exit code `2`.
In scripts, check the exit code:

```bash
if ! TASK_ID=$(ga4gh-cli tes create task.json); then
  echo "The task may not have been created" >&2
  exit 1
fi
```

An error from `tes create` doesn't always mean that there is no task: if the
service accepted the task but its answer got lost, for example in a timeout,
the task runs anyway. The CLI sends a task only once, and its error says so
when the task may have been accepted. Before you send it again, check with
`ga4gh-cli tes list -n "<name of the task>"` whether it exists. A task that
the service has just accepted may take a moment to show up in the list, so
an empty list right after the error doesn't prove that there is no task:
wait a minute and check again. Every task you send again that the service
had accepted after all runs twice.

## Run workflows with WES

Add a `WES` section with the address of a WES service to the configuration,
as shown above, with `oauth_access_token_env` if the service needs a login.
Which workflow languages and versions a service runs depends on the service;
ask its operators.

### Start a run

Pass the URL of the workflow, its language (`--type`) and the version of the
language (`--type_version`). Put the inputs of the workflow into a JSON file,
for example `params.json`, and pass it with `--params`:

```bash
RUN_ID=$(ga4gh-cli wes run https://example.org/workflows/main.cwl \
  --type CWL --type_version v1.2 --params params.json)
echo "$RUN_ID"
```

The output is the ID of the new run. As with `tes create`, the parameters can
also be JSON text or `-` for standard input; without `--params`, the run gets
no parameters (`{}`). With `--format json`, the output is `{"run_id":"…"}`.

| Option | What it does |
|---|---|
| `--type` | The workflow language, such as `CWL`, `WDL` or `NFL`. Required. |
| `--type_version` | The version of the language, such as `v1.2`. Required. |
| `--params` | The workflow parameters: a JSON file, JSON text or `-`. |
| `-a`, `--attachment` | Upload this file with the run. Repeat it for several files. |
| `--tag` | Add a tag to the run, as `KEY=VALUE`. Repeat it for several tags. |
| `-e`, `--engine` and `--engine_version` | Choose a workflow engine, if the service offers several. |
| `--engine_parameter` | Pass a parameter to the engine, as `KEY=VALUE`. Repeat it for several. |
| `--format` | `text` (default) or `json`. |

To run a workflow from files on your computer, attach them and pass the path
of the main file instead of a URL, if the service accepts uploads. Run the
command in the folder that the paths are relative to; absolute paths and `..`
aren't allowed. The CLI follows symbolic links, so check the files before you
attach them.

```bash
ga4gh-cli wes run main.cwl --type CWL --type_version v1.2 \
  -a main.cwl -a tools/step.cwl --params params.json
```

As with `tes create`, the CLI checks the input before it contacts the service
and sends a run only once; its error says so when the run may have started
anyway. Check with `wes list` before you start it again, and, as with tasks,
check again after a minute if the run isn't listed yet: a run you start again
that had started after all runs twice.

### Follow a run

List the runs:

```bash
ga4gh-cli wes list
```

```text
RUN ID  STATE
run1    RUNNING
```

`-p` sets the page size, `-t` asks for the next page, and `--all --format
jsonl` prints all runs as one JSON object per line, with the same
`--max-pages` and `--max-items` limits as `tes list`.

Get the state of a run, such as `QUEUED`, `RUNNING`, `COMPLETE` or
`EXECUTOR_ERROR`; a state that the WES specification doesn't define shows as
`UNKNOWN`:

```bash
ga4gh-cli wes status "$RUN_ID"
```

Get the details of a run, with its request, logs and outputs, as the JSON of
the service:

```bash
ga4gh-cli wes get "$RUN_ID"
```

Cancel a run; the CLI prints its ID:

```bash
ga4gh-cli wes cancel "$RUN_ID"
```

All `wes` commands end with the exit codes of the `tes` commands: `0` on
success, `1` on errors (with the HTTP status on stderr) and `2` on a missing
command or argument.

## Find workflows with TRS

A Tool Registry Service (TRS) lists tools and workflows, with their versions
and files. The `trs` commands only read from it. The configuration in
[Configure](#configure) points them at
[WorkflowHub](https://workflowhub.eu/), which you can read without a token.

Find workflows, for example the CWL workflows; all filters are optional:

```bash
ga4gh-cli trs tools --tool-class Workflow --descriptor-type CWL --limit 5
```

Look at one workflow and its versions, by the IDs that the list shows (on
WorkflowHub, numbers such as `3`):

```bash
ga4gh-cli trs tool 3
ga4gh-cli trs versions 3
```

List the files of a version and download its main file (the primary
descriptor), or all its files as one ZIP archive:

```bash
ga4gh-cli trs files 3 1 --type CWL
ga4gh-cli trs descriptor 3 1 --type CWL --plain > main.cwl
ga4gh-cli trs files 3 1 --type CWL --zip workflow.zip
```

| Command | Result |
|---|---|
| `trs tools` | Tools, filtered by `--tool-class`, `--descriptor-type`, `--organization`, `--name` and `--tag` (repeatable), paged with `--offset` and `--limit`. |
| `trs tool <TOOL_ID>` | One tool and its versions. |
| `trs versions <TOOL_ID>` | The versions of a tool. |
| `trs version <TOOL_ID> <VERSION_ID>` | One version and its workflow languages. |
| `trs files <TOOL_ID> <VERSION_ID> --type <TYPE>` | The paths and types of its files; with `--zip <FILE>`, all files as a ZIP archive in `FILE`, which must not exist yet. |
| `trs descriptor <TOOL_ID> <VERSION_ID> --type <TYPE>` | Its primary descriptor; `--path <RELATIVE_PATH>` selects another file, and `--plain` prints the file itself instead of JSON. |
| `trs tests <TOOL_ID> <VERSION_ID> --type <TYPE>` | Its test parameter files. |

To run a workflow that you downloaded, unpack the archive and pass its files
to [`wes run`](#start-a-run) with `-a`. For other registries, such as
Dockstore (`https://dockstore.org/api/ga4gh/trs/v2`), change `base_path`; the
options for registries that implement TRS differently, such as
`--api-version`, are in the [CLI
README](https://github.com/ga4gh/ga4gh-sdk/blob/main/cli/README.md#trs-examples).

## Look up objects with DRS

Add a `DRS` section to the configuration, as shown above. Set the ID of the
object, then read its metadata:

```bash
OBJECT_ID='the ID of the object'
ga4gh-cli drs get "$OBJECT_ID"
```

The output is the JSON of the service, with the size, the checksums and the
`access_methods` of the object. To get a URL for the bytes of the object, pass
the `access_id` of one of its access methods:

```bash
ACCESS_ID='the access_id of the access method'
ga4gh-cli drs access "$OBJECT_ID" "$ACCESS_ID"
```

The answer can contain headers that you need to download the bytes. The CLI
doesn't download them; use a tool such as `curl` with the URL. Both commands
end with the exit code `1` on errors and `2` on missing arguments, like the
`tes` commands.

!!! tip "Keep the URL out of the command line"
    An access URL can grant access by itself, for example as a signed URL.
    On the command line of `curl`, other users of the computer can see it. Pass
    it to `curl` through standard input instead, for example with
    [`jq`](https://jqlang.org/):

    ```bash
    ga4gh-cli drs access "$OBJECT_ID" "$ACCESS_ID" | jq -r '"url = \"\(.url)\""' | curl -K - -o object.bin
    ```

    This doesn't send the headers of the answer; add them if the service
    returns any.

## What's coming

These features are planned in the GA4GH SDK. Follow the issues to see when
they arrive; this page will be updated when they do.

| Feature | Status |
|---|---|
| Ready-made binaries, without Rust | Planned: [ga4gh-sdk#91](https://github.com/ga4gh/ga4gh-sdk/issues/91). |
| A container image of the CLI | Planned: [ga4gh-sdk#189](https://github.com/ga4gh/ga4gh-sdk/issues/189). |
| Download the logs and output files of TES tasks | Planned: [ga4gh-sdk#188](https://github.com/ga4gh/ga4gh-sdk/issues/188). |

## How this page was tested

We built the CLI at commit `af0e021` of the SDK in the `rust:1.97` container
image and checked every command and option on this page against its `--help`
output and the SDK's docs. Then we ran it on one computer:

- **Cloud Registry of ELIXIR On-Cloud, without a token:** `registry list`,
  `registry list --type tes`, `registry get` and `registry types` gave the
  output shown above.
- **WorkflowHub, without a token:** all `trs` commands on this page for
  workflow `3`, version `1`, including the download with `--zip`.
- **Local mock service, with its APIs at `/ga4gh/tes/v1` and
  `/ga4gh/wes/v1`, as in proTES and WESkit, and a test token in
  `LS_LOGIN_TOKEN`:** all `tes` and `wes` commands on this page reached the
  right paths and sent the token, also to `service-info`, with profiles
  chosen by `--profile` and `GA4GH_CLI_PROFILE`. Without the variable, the CLI
  stopped before any request; with a wrong token, it ended with `401
  Unauthorized`.

We did not run the CLI with an LS Login token against a deployed TES or WES
service of ELIXIR On-Cloud yet. The `drs` commands are unchanged since the
previous version of this page, which tested them against a mock service.

## Where to go next

- The SDK's docs: its [README](https://github.com/ga4gh/ga4gh-sdk#readme)
  (install and quick start with a local Funnel), the [CLI
  README](https://github.com/ga4gh/ga4gh-sdk/blob/main/cli/README.md) (all
  commands), the [usage
  guide](https://github.com/ga4gh/ga4gh-sdk/blob/main/docs/usage.md)
  (configuration and the Rust library) and the [authentication
  guide](https://github.com/ga4gh/ga4gh-sdk/blob/main/docs/authentication.md).
  They describe the latest version, which can be ahead of this page.
- How to find services and get a token without the CLI: [Using the
  APIs](../partners-and-developers/apis.md).
- Questions: the [Discussions][elixir-on-cloud-forum] or the
  [About](../about.md) page.
