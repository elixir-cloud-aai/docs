# Use Krini

[Krini][krini-repo] is the web portal of ELIXIR On-Cloud. It replaces the TES
Dashboard. In your browser, you log in with [LS Login][ls-login], choose
services from the [Cloud Registry][elixir-cloud-registry], run
[GA4GH TES][ga4gh-tes] tasks and [GA4GH WES][ga4gh-wes] workflows on them,
and follow your runs. This page shows how, and says what doesn't work yet.

Krini has no user guide of its own; its
[README](https://github.com/elixir-cloud-aai/krini/tree/staging#readme) and
[deployment guide](https://github.com/elixir-cloud-aai/krini/blob/staging/docs/deployment.md)
are for developers and operators.

!!! note "The new Krini"
    This page describes the new Krini (branch `staging` of the [Krini
    repository][krini-repo], commit
    [`c81a259`](https://github.com/elixir-cloud-aai/krini/commit/c81a259)).
    Parts of it are still in progress; see [What's coming](#whats-coming).

## What works now

| You want to | In Krini | Limits |
|---|---|---|
| Log in and out | [LS Login](#log-in), in the sidebar or the top bar | No other login provider. |
| Find services | [A list of the TES and WES services](#choose-a-service) in the Cloud Registry | Only TES and WES services, no search. |
| Run a task | [A form for TES tasks](#run-a-task) | Krini doesn't send your token to TES services yet, and drops the outputs that you enter. |
| Follow your tasks | [A list of tasks, with their details](#follow-your-tasks) | No search or filter yet. |
| Run a workflow | [A form for WES runs](#run-a-workflow) | You give the workflow by its URL or as attached files. |
| Follow your workflow runs | [A list of runs, with their states](#follow-your-workflow-runs) | No details and no outputs in Krini yet; read them [through the API](#read-the-details-and-outputs-of-a-run). |
| Use your token elsewhere | [Copy your access token](#copy-your-access-token) | Only while you are logged in. |

## Before you start

1. **Get an LS Login account.** See the [LS Login and registration
   guide][ls-login-guide]. Krini has no sign-up page of its own.
2. **Get access to services.** Each service decides whom it lets in. Krini
   shows the services of the Cloud Registry, but doesn't give you access to
   them, and has no form to ask for it yet. To ask for services that you can
   use, write to [cloud-service@elixir-europe.org][elixir-on-cloud-email].

!!! warning "Synthetic or public data only"
    The deployment is a sandbox for demos and tests (see [Researchers: Start
    Here](index.md)). Don't use Krini with personal or other sensitive data.

## Find your way

The sidebar on the left has two pages, under **Services**:

- **Tasks:** TES tasks, at `/dashboard/tasks`.
- **Workflows:** WES runs, at `/dashboard/workflows`.

The menu at the bottom of the sidebar shows who is logged in and has the
commands **Login**, **Copy token to Dashboard** and **Logout**. The top bar
switches between light and dark mode. The button at the top left of the
page hides and shows the sidebar.

The start page, **Dashboard**, has no content yet; open **Tasks** or
**Workflows** instead. The **TEST SERVER** entry in the list of TES services
and the info icon in the top bar don't work yet
([krini#67](https://github.com/elixir-cloud-aai/krini/issues/67)).

## Log in

1. Select the **LS Login** button in the top bar, or **Login** in the menu
   at the bottom of the sidebar.
2. Log in at LS Login with an identity provider of your choice, e.g., your
   home organisation, and agree to share your profile with Krini if LS Login
   asks.
3. LS Login sends you back to Krini. The sidebar shows your name and email
   address.

Krini keeps you logged in, and renews your access token in the background
while the page is open. If Krini can't renew it, it sends you to LS Login
again.

To log out, select **Logout** in the menu at the bottom of the sidebar. This
ends your session in Krini, not at LS Login: if you log in again in the same
browser, LS Login may not ask for your password.

## Choose a service

On **Tasks** and on **Workflows**, choose a service in the list at the top
right (**Select TES Instance** or **Select WES Instance**). Krini fills the
lists from the Cloud Registry:

- **TES:** services of the types `tes` and `tes-gateway`, e.g., TESK, Funnel
  and the proTES gateway.
- **WES:** services of the types `wes` and `wes-gateway` with an `https`
  address. Krini checks each one: it shows its health and the number of
  workflow types that it supports. You can't select a service that is
  unreachable, and Krini leaves out services that answer with an error.
  **Refresh**, at the top of the list, checks them again.

!!! warning "Krini sends your token to the WES service that you choose"
    Krini lists every TES and WES service in the Cloud Registry, whether you
    can trust it or not, and doesn't show whether a service is verified.
    Choose only services that you trust: anyone who runs a service that gets
    your token can act as you until the token expires. Check a service in
    the [Cloud Registry][elixir-cloud-registry] first: on the safe side, use
    only services that are both verified and synced (see [Using the Cloud
    Registry](../operators/using-cloud-registry.md#looking-up-services)).

To see more about a WES service, point at the info icon next to it, which
lists the workflow types and versions that it supports, or select the icon
to open its service info: the service, its organisation, its workflow types,
engines and file systems, the number of runs in each state, its tags and its
API endpoint.

!!! tip "Not in the list?"
    Krini shows only the services that are registered in the Cloud Registry.
    To find services and their addresses, see [Using the
    APIs](../partners-and-developers/apis.md#1-find-the-services).

## Run a task

A TES task runs one or more container images, one after the other. See
[GA4GH TES][ga4gh-tes] for its parts.

!!! warning "Krini doesn't send your token to TES services yet"
    Krini calls TES services without your access token
    ([krini#41](https://github.com/elixir-cloud-aai/krini/issues/41),
    [krini#44](https://github.com/elixir-cloud-aai/krini/issues/44)). Tasks
    work only on TES services that accept requests without a token. For the
    others, send your requests to the API with your token (see [Using the
    APIs](../partners-and-developers/apis.md)).

1. Open **Tasks** and select **Create Task**.
2. Choose a TES service in **Select TES Instance**.
3. Fill in the form. Only the image and the command of an executor are
   required:

    | Field | What to enter |
    |---|---|
    | **Name**, **Description** | Free text that helps you find the task later. |
    | **Executors** | One or more containers. For each: the **Image** (e.g., `alpine:3.20`), the **Commands**, one part per field (e.g., `echo` and `Hello`), and optionally environment variables (**Env**), the files for standard input and output (**Stdin**, **Stdout**, **Stderr**) and the working directory (**Workdir**). |
    | **Inputs** | Files that the service copies into the container before the task starts: the **URL** of each file and the **Path** in the container. |
    | **Outputs** | See the warning below. |
    | **Resources section** | CPU cores, RAM and disk in GB, zones, and whether the task may run on preemptible machines. |
    | **Tags** | Names and values, e.g., for a project. |
    | **Volumes** | Paths in the container that the executors share. |

4. Submit the form. Krini shows the ID of the new task, or the error of the
   service.

!!! warning "Outputs aren't sent yet"
    The task form of Krini doesn't pass the **Outputs** that you enter on to
    the TES service, so the service doesn't copy any result files out of the
    container
    ([cloud-components#574](https://github.com/elixir-cloud-aai/cloud-components/issues/574)).
    To keep results for now, write them to a place that the container can
    reach, e.g., from the command, or create the task through the API.

## Follow your tasks

**Tasks** lists the tasks of the selected service, ten per page, with their
IDs and states. Expand a task to see its details: name, description,
resources, tags, executors, volumes, creation time, inputs and outputs, and
the logs with standard output and standard error of each executor.

What a TES service lists depends on the service: some list only your own
tasks, others the tasks of all users.

To cancel a task that hasn't finished, expand it and select **Delete**. The
button cancels the task; it doesn't remove it from the list.

The states of a task:

| State | Meaning |
|---|---|
| `QUEUED`, `INITIALIZING` | Waiting for resources, or preparing the inputs. |
| `RUNNING` | The executors run. |
| `PAUSED` | Paused by the service. |
| `COMPLETE` | Finished without error. |
| `EXECUTOR_ERROR` | A command of the task failed; see its logs. |
| `SYSTEM_ERROR` | The service failed, not the task. |
| `CANCELING`, `CANCELED` | Being canceled, or canceled. |
| `PREEMPTED` | Stopped because its machine was taken away. |
| `UNKNOWN` | The service doesn't know the task's state. |

## Run a workflow

A WES service runs a whole workflow, e.g., in CWL, Nextflow, Snakemake or
WDL, depending on the service. See [GA4GH WES][ga4gh-wes].

Krini sends your access token to WES services, so you need to be logged in,
and to have access to the service (see [Before you start](#before-you-start)).

1. Open **Workflows** and select **Create Workflow**.
2. Choose a WES service in **Select WES Instance**. Krini shows the
   workflow types and versions that it supports.
3. Fill in the form:

    | Field | What to enter |
    |---|---|
    | **Workflow URL** (required) | The address of the workflow file, e.g., on GitHub (use the raw file), or a path within the files that you attach. |
    | **Workflow Type**, **Workflow Type Version** (required) | One of the types and versions that the service supports. |
    | **Workflow Parameters (JSON)** (required) | The inputs of the workflow as a JSON object, e.g., `{"input_file": "https://example.com/input.txt"}`. Use `{}` if it has none. |
    | **Engine Parameters (JSON)**, under **Advanced Configuration** | Settings of the workflow engine, if the service accepts them. |
    | **Tags (Optional)** | Keys and values, e.g., for a project. |
    | **Workflow Attachments (Optional)** | Files that the service needs next to the workflow, e.g., its other files or a configuration. |

4. Select **Submit Run**. Krini shows the run ID, or the error of the
   service. **Reset** clears the form.

## Follow your workflow runs

**Workflows** lists the runs of the selected service, ten per page, with
their run IDs and states. **Cancel** stops a run that is queued,
initialising or running.

The states are those of WES: `QUEUED`, `INITIALIZING`, `RUNNING`, `PAUSED`,
`COMPLETE`, `EXECUTOR_ERROR`, `SYSTEM_ERROR`, `CANCELING`, `CANCELED`,
`PREEMPTED` and `UNKNOWN` (see [Follow your tasks](#follow-your-tasks) for
what they mean).

### Read the details and outputs of a run

The button **View Details** doesn't open anything in Krini yet
([krini#66](https://github.com/elixir-cloud-aai/krini/issues/66)). To read the log and the outputs of a run, ask the WES service directly
with your access token:

1. In Krini, select **Copy token to Dashboard** (see [Copy your access
   token](#copy-your-access-token)).
2. Look up the API endpoint of the service: select the info icon next to the
   service in **Select WES Instance**. **API endpoint** shows the address of
   its service info, e.g.,
   `https://wes.example.org/ga4gh/wes/v1/service-info`; the API endpoint is
   that address without `/service-info`.
3. In a terminal (Bash or Zsh), read the token, then call the service with
   the endpoint and the run ID:

    ```bash
    read -rs TOKEN   # paste the token and press Enter; it isn't shown or saved in the history
    printf 'Authorization: Bearer %s\n' "$TOKEN" |
      curl -H @- "<API endpoint>/runs/<run ID>"
    ```

    `curl -H @-` reads the header from its input, so the token doesn't
    appear in the list of running processes either.

The answer has the state of the run, its request, the logs of the run and
of its tasks, and, under `outputs`, its outputs. Where the outputs are
depends on the service, e.g., in a bucket of its object storage.

## Copy your access token

To use the services outside Krini, e.g., with `curl` (see [Using the
APIs](../partners-and-developers/apis.md)), select **Copy token to Dashboard** in the menu at the bottom
of the sidebar. Krini copies your LS Login access token to the clipboard.

!!! warning "Keep your token to yourself"
    Anyone with your token can act as you at the services until it expires.
    Don't share it, and don't paste it into chats, issues or files that you
    commit.

The token expires after a while; copy a new one when a service answers
`401 Unauthorized`.

## Troubleshooting

| Message | What to do |
|---|---|
| "Login to fetch TES servers from registry." | The Cloud Registry asked for a login. Log in and open the page again. |
| "Failed to fetch TES servers." or "Failed to load WES instances" | Krini couldn't reach the Cloud Registry. Try again later; for WES, select **Retry**. |
| A WES service is greyed out in the list | The service didn't answer. Select **Refresh** later. |
| "Service Information Unavailable" or "No Workflow Types Reported" | The service didn't say which workflow types it supports. You can still submit, but check with its operator first. |
| "Identity Provider Error" in the sidebar | Krini couldn't reach LS Login. Select the message to try again. |
| "Invalid state found. State does not match." or "Invalid request parameters found." after login | The login didn't complete. Select **Go to Login** and log in again. |
| A service answers `401` or `403` | You aren't logged in, your token expired, or the service doesn't give you access. Log in again, or ask for access (see [Before you start](#before-you-start)). |

## What's coming

These are planned in the [Krini repository][krini-repo], not available yet:

- Run TES tasks with your token, through the Cloud Components
  ([krini#41](https://github.com/elixir-cloud-aai/krini/issues/41)), and
  send your token to all services
  ([krini#44](https://github.com/elixir-cloud-aai/krini/issues/44)).
- Access tiers, so that Krini shows what you may use
  ([krini#43](https://github.com/elixir-cloud-aai/krini/issues/43)), and a
  link to ask for access to compute
  ([krini#45](https://github.com/elixir-cloud-aai/krini/issues/45)).
- Forms for workflow inputs, built from the workflow's I/O schema
  ([krini#47](https://github.com/elixir-cloud-aai/krini/issues/47)).
- For tasks through the proTES gateway: where a task ran
  ([krini#48](https://github.com/elixir-cloud-aai/krini/issues/48)), and
  which gateway plugins to use
  ([krini#49](https://github.com/elixir-cloud-aai/krini/issues/49)).
- The details, log and outputs of a workflow run in Krini
  ([krini#66](https://github.com/elixir-cloud-aai/krini/issues/66)), and task outputs from the task form
  ([cloud-components#574](https://github.com/elixir-cloud-aai/cloud-components/issues/574)).
- A prefilled demo task and workflow
  ([krini#57](https://github.com/elixir-cloud-aai/krini/issues/57)).

## Getting help

- **Access to services and questions about the deployment:** write to
  [cloud-service@elixir-europe.org][elixir-on-cloud-email].
- **Problems with LS Login itself,** e.g., your account: see the [LS
  Login][ls-login] pages.
- **Bugs in Krini:** open an issue in the [Krini repository][krini-repo].
  Report security problems privately instead, as the [security
  policy][security-policy] describes.

[krini-repo]: <https://github.com/elixir-cloud-aai/krini>
[ls-login]: <https://www.lifescience-ri.eu/life-science-login/>
[ls-login-guide]: <https://www.lifescience-ri.eu/ls-login-and-registration-guide/>
[security-policy]: <https://github.com/elixir-cloud-aai/.github/blob/main/SECURITY.md>
