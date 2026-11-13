# Tutorial: Your First Run from the Command Line

## Synopsis

This tutorial takes you from installing `ga4gh-cli`, the command-line tool of
the [GA4GH SDK](https://github.com/ga4gh/ga4gh-sdk), to the results of your
first analysis on ELIXIR On-Cloud. You find services in the Cloud Registry,
log in with an LS Login token, and count the lines, words and characters of
a small text file twice: once as a [GA4GH TES][ga4gh-tes] task, and once as
a [GA4GH WES][ga4gh-wes] workflow. It takes about an hour, most of it for
building the tool.

The tutorial uses the demo files in this documentation. Each step does one
thing and links to [Use the Command Line](cli.md), the reference of the
tool, which explains all commands and options; this page doesn't repeat it.
The commands are for Bash or Zsh on Linux or macOS.

!!! warning "What the CLI can't do yet"
    - **No ready-made binaries:** you build the CLI from its source code
      ([ga4gh-sdk#91](https://github.com/ga4gh/ga4gh-sdk/issues/91)).

The CLI doesn't log in itself: it sends an LS Login access token that you
put into a variable. Step 5 shows how to get one.

!!! warning "Synthetic or public data only"
    The deployment is a sandbox for demos and tests. The demo file is public;
    don't use the services with personal or other sensitive data.

## 1. Before you start

You need:

- **Git and [Rust](https://www.rust-lang.org/tools/install)**, installed
  with `rustup`, to build the CLI, and `curl` and
  [`jq`](https://jqlang.org/) for the demo files and results.
- **An LS Login account.** See the [LS Login and registration
  guide](https://www.lifescience-ri.eu/ls-login-and-registration-guide/).
- **Access to a TES service,** for part 1, and **to a WES service that runs
  CWL,** for part 2, and the information which LS Login tokens they accept.

The deployment doesn't publish the addresses of all its services for
researchers yet. To ask for services that you can use, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email] and say that you
want to follow this tutorial.

The demo files:

| File | What it is |
|---|---|
| [`LICENSE`](https://raw.githubusercontent.com/elixir-cloud-aai/docs/main/LICENSE) of this documentation | The text file that you count. |
| [`count-words.cwl`](tutorial-files/count-words.cwl) | A workflow in CWL that counts the lines, words and characters of a text file with `wc`, in the container image `alpine:3.20`. |
| [`count-words.json`](tutorial-files/count-words.json) | The parameters of the workflow: the address of the text file. |

## 2. Install the CLI

Build and install the CLI at the commit that [Use the Command
Line](cli.md#install) describes:

```bash
git clone https://github.com/ga4gh/ga4gh-sdk.git
cd ga4gh-sdk
git checkout af0e021
cargo install --path cli --locked
cd ..
```

**Check:**

```bash
ga4gh-cli --version
```

The command prints the version of the CLI. If the shell doesn't find
`ga4gh-cli`, open a new terminal, so that it reads the `PATH` that `rustup`
set.

## 3. Point the CLI at the Cloud Registry

The CLI reads the addresses of the services from `~/.ga4gh-cli/config.json`.
Create it with the Cloud Registry of ELIXIR On-Cloud, which anyone can read
without a token. The command doesn't change a file that already exists; in
that case, add the `REGISTRY` section in a text editor (see
[Configure](cli.md#configure)).

```bash
mkdir -p ~/.ga4gh-cli
[ -e ~/.ga4gh-cli/config.json ] || printf '%s\n' '{
  "REGISTRY": {
    "base_path": "https://elixir-on.cloud/ga4gh/registry/v1"
  }
}' > ~/.ga4gh-cli/config.json
chmod 600 ~/.ga4gh-cli/config.json
```

## 4. Find your services

List the TES and the WES services in the Cloud Registry (see [Find services
in the Cloud Registry](cli.md#find-services-in-the-cloud-registry)):

```bash
ga4gh-cli registry list --type tes
ga4gh-cli registry list --type wes
```

**Check:** the TES and WES services that you got access to are in the lists,
with their `URL`s. If a service isn't listed, use the address that its
operators gave you.

Before you send a token to a service, check in the [front end of the Cloud
Registry][elixir-cloud-registry] that it is verified: the CLI doesn't show
this.

Then add a `TES` and a `WES` section to `~/.ga4gh-cli/config.json` in a text
editor. `base_path` is the root of the API of the service, e.g., ending in
`/ga4gh/tes/v1` for proTES (see [Configure](cli.md#configure)). Your file
then looks like this, with the addresses of your services instead of
`<TES HOST>` and `<WES HOST>`:

```json
{
  "REGISTRY": {
    "base_path": "https://elixir-on.cloud/ga4gh/registry/v1"
  },
  "TES": {
    "base_path": "https://<TES HOST>/ga4gh/tes/v1",
    "oauth_access_token_env": "LS_LOGIN_TOKEN"
  },
  "WES": {
    "base_path": "https://<WES HOST>/ga4gh/wes/v1",
    "oauth_access_token_env": "LS_LOGIN_TOKEN"
  }
}
```

`oauth_access_token_env` tells the CLI to send the token in the variable
`LS_LOGIN_TOKEN`. Leave it out for a service that doesn't need a token.

## 5. Log in

The CLI sends a token that you put into a variable; it doesn't get one
itself. Get an LS Login access token in one of these ways, and ask the
operators of your services which of them they accept:

- **With your own LS Login client,** as [Get an access
  token](../partners-and-developers/apis.md#2-get-an-access-token)
  describes.
- **From Krini,** the web portal: log in, then copy your token, as [Copy your
  access token](krini.md#copy-your-access-token) describes.

Put the token into the variable in the terminal where you use the CLI (see
[Log in with LS Login](cli.md#log-in-with-ls-login)). The token isn't shown
and isn't saved in the history of the shell:

```bash
read -rs LS_LOGIN_TOKEN   # paste the token, then press Enter
export LS_LOGIN_TOKEN
```

**Check:** both services answer:

```bash
ga4gh-cli tes list
ga4gh-cli wes list
```

The commands list your tasks and runs, or none. `401 Unauthorized` means
that the token expired or that the service doesn't accept it: get a new one,
or ask the operators.

## Part 1: Run a task

A TES task runs a command in a container. Here, the command is `wc`, and the
service copies the text file into the container before the command starts.

### 6. Create the task

Write the task into a file and send it (see [Create a
task](cli.md#create-a-task)):

```bash
printf '%s\n' '{
  "name": "count-words",
  "inputs": [
    {
      "url": "https://raw.githubusercontent.com/elixir-cloud-aai/docs/main/LICENSE",
      "path": "/data/LICENSE",
      "type": "FILE"
    }
  ],
  "executors": [
    {
      "image": "alpine:3.20",
      "command": ["wc", "/data/LICENSE"]
    }
  ]
}' > count-words-task.json
TASK_ID=$(ga4gh-cli tes create count-words-task.json)
echo "$TASK_ID"
```

**Check:** the CLI prints the ID of the new task. If it ends with an error,
see [Check for errors](cli.md#check-for-errors) before you send the task
again.

### 7. Follow the task

Ask for its state until it is `COMPLETE` (see [Get the state of a
task](cli.md#get-the-state-of-a-task)). Tasks first wait in `QUEUED` until
the service has resources; this can take a few minutes.

```bash
ga4gh-cli tes status "$TASK_ID"
```

If the state is `EXECUTOR_ERROR` or `SYSTEM_ERROR`, read the logs as in the
next step. Not every TES service can fetch files from an `https` address: if
the input is the problem, remove `inputs` from the task and use the command
`["echo", "Hello"]` instead, which checks everything else.

### 8. Read the result

Get the task with its logs, and pick the standard output of its command (see
[Get a task](cli.md#get-a-task)):

```bash
ga4gh-cli tes get "$TASK_ID" FULL | jq -r '.logs[-1].logs[0].stdout'
```

**Result:** the numbers of lines, words and characters of the file:

```text
      121      1066      7048 /data/LICENSE
```

The numbers change if the file changes. Some services return no standard
output in the logs; then the result is `null`.

## Part 2: Run a workflow

A WES service runs a whole workflow. Here, the workflow is
[`count-words.cwl`](tutorial-files/count-words.cwl), which does the same as
the task, and writes the result to the file `counts.txt`. Check with the
operators of your WES service that it runs CWL `v1.0`; if it runs other
languages only, ask them for an example workflow instead.

### 9. Start the workflow

Download the parameters of the workflow, then start a run with the address
of the workflow (see [Start a run](cli.md#start-a-run)):

```bash
curl -fsSLO https://raw.githubusercontent.com/elixir-cloud-aai/docs/main/docs/researchers/tutorial-files/count-words.json
RUN_ID=$(ga4gh-cli wes run \
  https://raw.githubusercontent.com/elixir-cloud-aai/docs/main/docs/researchers/tutorial-files/count-words.cwl \
  --type CWL --type_version v1.0 --params count-words.json)
echo "$RUN_ID"
```

**Check:** the CLI prints the ID of the new run.

### 10. Follow the run

Ask for its state until it is `COMPLETE` (see [Follow a
run](cli.md#follow-a-run)):

```bash
ga4gh-cli wes status "$RUN_ID"
```

### 11. Read the result

Get the run, and pick its outputs:

```bash
ga4gh-cli wes get "$RUN_ID" | jq '.outputs'
```

**Result:** `outputs` lists the file `counts.txt` with its address. Where
the file is, and how you download it, depends on the service, e.g., in a
bucket of its object storage. Its content is the same as in step 8, without
the file name:

```text
      121      1066      7048
```

If the run failed, `jq '.run_log'` instead of `jq '.outputs'` shows the log
of the workflow engine.

## 12. Clean up

Remove the token from the terminal, and the demo files from your folder:

```bash
unset LS_LOGIN_TOKEN
rm count-words-task.json count-words.json
```

The configuration file holds no token, so you can keep it for next time.

## Where to go next

- All commands and options, e.g., to find workflows in WorkflowHub or to
  attach files to a run: [Use the Command Line](cli.md).
- Do the same in your browser: [Tutorial: Your First Run in
  Krini](tutorial-krini.md).
- Run a workflow on the TES services of several Nodes: [Run Workflows
  Across Nodes](federated-workflows.md).

## How this tutorial was tested

The workflow [`count-words.cwl`](tutorial-files/count-words.cwl) ran with
`cwltool` and Docker on one computer, with
[`count-words.json`](tutorial-files/count-words.json), and gave the result
shown in step 11; the command of the task gave the result shown in step 8 in
the image `alpine:3.20`. The commands and options of the CLI follow [Use
the Command Line](cli.md), which was tested at commit `af0e021` of the SDK.
The steps have not yet been run against deployed TES and WES services of
ELIXIR On-Cloud, and not yet by someone who didn't write them. If you follow
this tutorial, please tell us what didn't work: in the
[Discussions][elixir-on-cloud-forum] or in an issue in the [docs
repository](https://github.com/elixir-cloud-aai/docs/issues).
