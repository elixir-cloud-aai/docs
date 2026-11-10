# Use the Command Line

This page shows how to use the services of ELIXIR On-Cloud from your terminal
with `ga4gh-cli`, the command-line tool of the [GA4GH
SDK](https://github.com/ga4gh/ga4gh-sdk): find services in the Cloud
Registry, send tasks to a [GA4GH TES][ga4gh-tes] service and look up objects
in a [GA4GH DRS][ga4gh-drs] service. The tool is at an early stage and has no
releases yet. This page describes what it does today and what is planned. For
the full reference, see the [SDK's own docs](#where-to-go-next).

!!! warning "What the CLI can't do yet"
    - **No authentication:** the CLI reads tokens from its configuration
      file, but doesn't send them. It can only use services that you can
      call without a token, such as the Cloud Registry. For services that
      require an LS Login token, see [Work without the
      CLI](#work-without-the-cli).
    - **No workflows and no tool registries:** commands for WES and TRS are
      planned (see [What's coming](#whats-coming)).

## What works now

| Commands | Service | What you do |
|---|---|---|
| `ga4gh-cli registry` | GA4GH Service Registry, such as the Cloud Registry | [Find services](#find-services-in-the-cloud-registry) and their addresses. |
| `ga4gh-cli tes` | GA4GH TES, such as proTES, TESK or Funnel | [Create, list, read and cancel tasks](#run-tasks-with-tes). |
| `ga4gh-cli drs` | GA4GH DRS, such as DRS-Filer | [Read the metadata and access URLs of objects](#look-up-objects-with-drs). |

## Install

The project publishes no binaries or packages, so you build the CLI from its
source code. You need Git and [Rust](https://www.rust-lang.org/tools/install),
installed with `rustup`. The repository pins the version of Rust that it
needs, and `rustup` installs it on the first build.

```bash
git clone https://github.com/ga4gh/ga4gh-sdk.git
cd ga4gh-sdk
git checkout 8b8030f   # the commit that this page describes
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
It has one section per kind of service: `REGISTRY`, `TES` and `DRS`. To start,
point the CLI at the Cloud Registry of ELIXIR On-Cloud. The commands below
create the file only if it doesn't exist yet; to change an existing file, edit
it in a text editor instead, so that its other sections stay.

```bash
mkdir -p ~/.ga4gh-cli
[ -e ~/.ga4gh-cli/config.json ] || cat > ~/.ga4gh-cli/config.json <<'JSON'
{
  "REGISTRY": {
    "base_path": "https://elixir-on.cloud/ga4gh/registry/v1"
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
  "TES": {
    "base_path": "https://<HOST>/ga4gh/tes/v1"
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
- **One service of each kind at a time:** to use another TES service, edit its
  section. There are no profiles and no command-line option for the address.

## Find services in the Cloud Registry

The [Cloud Registry](../operators/using-cloud-registry.md) lists the services
of ELIXIR On-Cloud. Anyone can read it without a token, so the `registry`
commands work with the configuration above.

!!! info "Few services are listed yet"
    The deployment doesn't publish the addresses of its TES, DRS and WES
    services for researchers yet (see [Researchers: Start
    Here](index.md#before-you-start)). Until then, the list can be short. Write
    to [cloud-service@elixir-europe.org][elixir-on-cloud-email] to ask for
    services that you can use.

List all services:

```bash
ga4gh-cli registry list
```

```text
ID                               TYPE                              URL
ELIXIR_CLOUD_SERVICE_REGISTRY_1  org.ga4gh:service-registry:1.0.0  https://elixir-on.cloud/ga4gh/registry/v1
```

List only the services of one API, by the artifact of their type (`tes`,
`wes`, `drs`, `trs`, …; case is ignored):

```bash
ga4gh-cli registry list --type tes
```

Show all details of one service, by its ID, as JSON:

```bash
ga4gh-cli registry get ELIXIR_CLOUD_SERVICE_REGISTRY_1
```

List the API types that services in the registry use, one
`group:artifact:version` per line:

```bash
ga4gh-cli registry types
```

To use a service that you found, copy its `URL` into `base_path` of the
section for its API, such as `TES`. If the URL ends before the path of the API
(for example, without `/ga4gh/tes/v1`), add the path from the docs of the
product. If `base_path` is wrong, the CLI ends with a `404` error and the hint
`Check that base_path is the TES API root`.

The commands show only the fields of the Service Registry specification. The
labels of the Cloud Registry, such as whether a service is
[verified](../operators/using-cloud-registry.md#verified-services), aren't
shown: check them in the [front end][elixir-cloud-registry] before you trust a
service.

## Run tasks with TES

Add a `TES` section to the configuration, as shown above. The service must
accept requests without a token (see [Authentication](#authentication)).

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

### List tasks

```bash
ga4gh-cli tes list
```

```text
TASK ID                   State
task1                     Queued
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
prints the JSON of the service unchanged, without a final line break; pipe it
to a tool such as `jq` to format it.

### Get the state of a task

```bash
ga4gh-cli tes status "$TASK_ID"
```

```text
QUEUED
```

The CLI prints the TES state, such as `RUNNING`, `COMPLETE` or
`EXECUTOR_ERROR`.

### Cancel a task

```bash
ga4gh-cli tes cancel "$TASK_ID"
```

### Check for errors

All `tes` commands end with the exit code `0` on success and `1` on errors,
for example when the service rejects a task or can't be reached. The message
goes to stderr, with the HTTP status and the answer of the service. A missing
command or argument ends with the exit code `2`. In scripts, check the exit
code:

```bash
if ! TASK_ID=$(ga4gh-cli tes create task.json); then
  echo "The task may not have been created" >&2
  exit 1
fi
```

An error from `tes create` doesn't always mean that there is no task: if the
service accepted the task but its answer got lost, for example in a timeout,
the task runs anyway. Before you send it again, check with `ga4gh-cli tes list
-n "<name of the task>"` whether it exists, so that it doesn't run twice.

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

!!! warning "Treat access URLs like passwords"
    An access URL can be signed: anyone who has it can download the object
    until it expires. Don't paste it into a command line, where it stays in
    the shell history and other users of the computer can see it. Pass it to
    `curl` through standard input instead, for example with
    [`jq`](https://jqlang.org/):

    ```bash
    ga4gh-cli drs access "$OBJECT_ID" "$ACCESS_ID" | jq -r '"url = \"\(.url)\""' | curl -K - -o object.bin
    ```

    This doesn't send the headers of the answer; add them if the service
    returns any.

## Authentication

The CLI can't send a token yet, such as an LS Login access token. It reads
`oauth_access_token` and `basic_auth` from the configuration file, but no
request carries them ([ga4gh-sdk#31](https://github.com/ga4gh/ga4gh-sdk/issues/31)).
A service that requires a token answers `401 Unauthorized`, and the CLI ends
with an error.

!!! danger "Don't put tokens in the configuration file"
    They have no effect yet, and the file would keep them on disk. Get a
    token only when you need it, as [Using the
    APIs](../partners-and-developers/apis.md#2-get-an-access-token)
    describes, and use it as shown below.

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
depend on the service; the [WES specification][ga4gh-wes] describes the
fields.

```bash
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl --fail-with-body -X POST "https://<HOST>/ga4gh/wes/v1/runs" -H @- \
  -F workflow_type=CWL \
  -F workflow_type_version=v1.2 \
  -F workflow_url=https://example.org/workflow.cwl \
  -F 'workflow_params={}'
```

## What's coming

These features are planned in the GA4GH SDK. Follow the issues to see when
they arrive; this page will be updated when they do.

| Feature | Status |
|---|---|
| WES commands: run workflows and check their state | Planned: [ga4gh-sdk#105](https://github.com/ga4gh/ga4gh-sdk/issues/105). The SDK's Rust library has a WES client already. |
| TRS commands: list tools and read workflow descriptors, e.g., from WorkflowHub | In progress: [ga4gh-sdk#115](https://github.com/ga4gh/ga4gh-sdk/issues/115). The SDK's Rust library has a TRS client already. |
| Send tokens with requests | Planned: [ga4gh-sdk#31](https://github.com/ga4gh/ga4gh-sdk/issues/31). |
| Log in with LS Login from the CLI (OIDC device flow) | Planned: [ga4gh-sdk#90](https://github.com/ga4gh/ga4gh-sdk/issues/90). |
| Several services of the same kind (profiles) | Planned: [ga4gh-sdk#47](https://github.com/ga4gh/ga4gh-sdk/issues/47). |
| Ready-made binaries, without Rust | Planned: [ga4gh-sdk#91](https://github.com/ga4gh/ga4gh-sdk/issues/91). |

## How this page was tested

We built the CLI at commit `8b8030f` of the SDK in the `rust:1.97` container
image and checked every command and option on this page against its `--help`
output and its source code. Then we ran it on one computer:

- **Cloud Registry of ELIXIR On-Cloud, without a token:** `registry list`,
  `registry list --type tes`, `registry get` and `registry types` gave the
  output shown above.
- **Local mock service, with its APIs at `/ga4gh/tes/v1` and `/ga4gh/drs/v1`,
  as in proTES and DRS-Filer:** all `tes` and `drs` commands on this page
  reached the right paths, with the options passed on as shown, and gave the
  output shown above. With a token in the configuration, no request had an
  `Authorization` header.

We did not test the CLI against a deployed TES or DRS service, and we saw no
task run. The `curl` commands were tested against a mock service for an
earlier version of this page.

## Where to go next

- The SDK's docs: its [README](https://github.com/ga4gh/ga4gh-sdk#readme)
  (install and quick start with a local Funnel), the [CLI
  README](https://github.com/ga4gh/ga4gh-sdk/blob/main/cli/README.md) (all
  commands) and the [usage
  guide](https://github.com/ga4gh/ga4gh-sdk/blob/main/docs/usage.md)
  (configuration and the Rust library). They describe the latest version,
  which can be ahead of this page.
- How to find services and get a token: [Using the
  APIs](../partners-and-developers/apis.md).
- Questions: the [Discussions][elixir-on-cloud-forum] or the
  [About](../about.md) page.
