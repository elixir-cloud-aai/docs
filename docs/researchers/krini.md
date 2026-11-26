---
last_verified: 2026-11-21
---

# Use Krini

[Krini][krini-repo] is the web portal of ELIXIR On-Cloud, at
**<https://portal.elixir-on.cloud>**. It replaces the TES Dashboard. In
your browser, you log in with [LS Login][ls-login], choose services from
the [Cloud Registry][elixir-cloud-registry], run [GA4GH TES][ga4gh-tes]
tasks and [GA4GH WES][ga4gh-wes] workflows on them with your own access
token, and follow your runs. This page shows how, and says what doesn't
work yet.

The portal runs Krini 0.1.0 (see its [release
notes](https://github.com/elixir-cloud-aai/krini/releases/tag/v0.1.0)).
Krini's own [documentation](https://krini.readthedocs.io/en/v0.1.0/) has a
short user guide and the guides for operators and developers. The old
address `https://krini.rahtiapp.fi` leads to the same Krini; logging in
there takes you to the portal address.

## What works now

| You want to | In Krini | Limits |
|---|---|---|
| Look around | [The task and workflow pages](#find-your-way), without logging in | You see the services, not the forms to run tasks and workflows. |
| Log in and out | [LS Login](#log-in) | No other login provider. |
| Run a task | [A form for TES tasks](#run-a-task), with your token | Only with [compute access](#before-you-start). |
| Follow your tasks | [A list of tasks, and the details of each](#follow-your-tasks) | What a service lists depends on the service. |
| Run a workflow | [A form for WES runs](#run-a-workflow) | No WES service can be selected yet: [none is reachable](#no-wes-service-yet). |
| Follow your workflow runs | [A list of runs, and the details of each](#follow-your-workflow-runs) | As above. |
| Use your token elsewhere | [Copy your access token](#copy-your-access-token) | Only while you are logged in. |

## Before you start

1. **Get an LS Login account.** See the [LS Login and registration
   guide][ls-login-guide]. Krini has no sign-up page of its own.
2. **Get compute access.** You can run tasks and workflows only as a
   member of the LS Login group `ECP_CLN:EOC-Compute`. Apply for it with the application form (see [Apply for compute
   access](index.md#apply-for-compute-access)). Once your application is
   approved, log out of Krini and log in again: tokens that you got before
   the approval don't carry the group.
3. **Check that the service lets you in.** Each TES and WES service decides
   whom it accepts: Krini only offers the forms, and sends your token. The
   TES gateway of the deployment, proTES, accepts the members of
   `ECP_CLN:EOC-Compute` (see [proTES](../operators/services/protes.md#in-the-elixir-on-cloud)).
   For other services, ask their operators, or write to
   [cloud-service@elixir-europe.org][elixir-on-cloud-email].

!!! warning "Synthetic or public data only"
    The deployment is a sandbox for demos and tests (see [Researchers: Start
    Here](index.md)). Don't use Krini with personal or other sensitive data.

### Access tiers

When you log in, Krini derives your tier from your LS Login groups, and
shows it in the menu at the bottom of the sidebar (**User Tier**):

| Tier | Who | What Krini offers |
|---|---|---|
| Admin | Members of `ECP_CLN:ADMIN` | The same forms as Compute; Krini has no admin pages. Only members of `ECP_CLN:EOC-Compute` may run tasks, so admins who run tasks join that group too. |
| Compute | Members of `ECP_CLN:EOC-Compute` | The forms to run tasks and workflows (**Create Task**, **Create Workflow**). |
| User | Everybody else who is logged in | The lists, without the forms. Instead of **Create Task** and **Create Workflow**, Krini shows **Request compute access** (a link, if the deployment set one) or **Compute access required**. |

The tier only decides what Krini's pages offer. The services decide what
your token may do, whatever your tier.

## Find your way

The sidebar on the left has these pages:

- **Services**:
    - **Tasks:** TES tasks, at `/dashboard/tasks`.
    - **Workflows:** WES runs, at `/dashboard/workflows`.
- **About**:
    - **Privacy:** the privacy notice, at `/privacy`: what Krini processes
      and which cookies it sets. Without logging in, Krini sets no cookies,
      unless you start a login or change the sidebar.

The start page, **Dashboard**, links to **Tasks (TES)** and **Workflows
(WES)**. The menu at the bottom of the sidebar shows who is logged in and
has the commands **Copy access token** and **Logout**, or **Login** if you
aren't logged in. The top bar switches between light and dark mode (Krini
keeps your choice), and the button at the top left of the page hides and
shows the sidebar.

## Log in

1. Select **Log in** in the top bar, or **Login** in the menu at the bottom
   of the sidebar.
2. On the login page, select **LS Login**. The page also links to the
   privacy notice.
3. Log in at LS Login with an identity provider of your choice, e.g., your
   home organisation, and agree to share your profile with Krini if LS Login
   asks.
4. LS Login sends you back to Krini. The sidebar shows your name; its menu
   shows your email address and your [tier](#access-tiers).

Krini keeps you logged in, and renews your access token in the background
while the page is open. If LS Login can't be reached for a while, Krini
keeps your session and tries again; if LS Login rejects the renewal, Krini
ends the session and you log in again.

To log out, select **Logout** in the menu at the bottom of the sidebar.
Krini ends your session in Krini and at LS Login, and LS Login sends you
back to the start page of the portal.

## Choose a service

On **Tasks** and on **Workflows**, choose a service in the list at the top
right (**Select TES Instance** or **Select WES Instance**). Krini fills the
lists from the Cloud Registry, with the services that are served over
`https`:

- **TES:** services of the types `tes` and `tes-gateway`, e.g., the proTES
  gateway (**ELIXIR On-Cloud TES Gateway**), TESK and Funnel.
- **WES:** services of the types `wes` and `wes-gateway`. Krini checks
  each one: it shows its health and the number of workflow types that it
  supports. You can't select a service that is unreachable, and Krini
  leaves out services that answer with an error. **Refresh**, at the top of
  the list, checks them again.

Your tasks run on the service that you choose. proTES forwards each task
to one of the TES services that it knows (see [Which TES services you can
use](index.md#which-tes-services-you-can-use)); the other services run it
themselves.

!!! warning "Krini sends your token to the service that you choose"
    Krini lists every TES and WES service in the Cloud Registry, whether you
    can trust it or not, and doesn't show whether a service is verified.
    Choose only services that you trust: anyone who runs a service that gets
    your token can act as you until the token expires. Check a service in
    the [Cloud Registry][elixir-cloud-registry] first: on the safe side, use
    only services that are both verified and synced (see [Using the Cloud
    Registry](../operators/using-cloud-registry.md#looking-up-services)).

Krini calls the services from your browser. You can't use a service from
Krini, even if it is in the list, if it doesn't accept your token or
doesn't allow requests from the portal's address (CORS); ask its operator.

To see more about a WES service, point at the info icon next to it, which
lists the workflow types and versions that it supports, or select the icon
to open its service info.

!!! tip "Not in the list?"
    Krini shows only the services that are registered in the Cloud Registry.
    To find services and their addresses, see [Using the
    APIs](../partners-and-developers/apis.md#1-find-the-services).

## Run a task

A TES task runs one or more container images, one after the other. See
[GA4GH TES][ga4gh-tes] for its parts. You need to be logged in with
[compute access](#before-you-start).

1. Open **Tasks** and select **Create Task**.
2. Choose a TES service in **Select TES Instance**, e.g., **ELIXIR
   On-Cloud TES Gateway**.
3. Fill in the form. Only the image and the command of one executor are
   required:

    | Field | What to enter |
    |---|---|
    | **Name**, **Description** | Free text that helps you find the task later. |
    | **Executors** | One or more containers, run in order; **Add executor** adds one. For each: the **Image** (e.g., `alpine:3.20`) and the **Command**, one argument per line (e.g., `echo` and `Hello`). **Advanced executor options** has the working directory (**Workdir**), the files for standard input and output (**Stdin**, **Stdout**, **Stderr**), environment variables (**Environment**) and **Ignore error**, to go on with the next executor if this one fails. |
    | **Inputs** | Under **Inputs, outputs, resources and metadata**: files that the service copies into the container before the task starts. For each: the **URL** of the file, or its content inline, the **Path in container**, and the type, `FILE` or `DIRECTORY`. |
    | **Outputs** | Files that the service copies out of the container when the task ends. For each: the **URL** to copy it to, the **Path in container** (or a **Path prefix** with wildcards), and the type. The URL must be a place that the service can write to; ask its operator which ones it supports. |
    | Resources | **CPU cores**, **RAM (GB)** and **Disk (GB)**, **Zones** (comma separated), **Preemptible**, and **Backend parameters** for the service, optionally strict (the task fails if the service doesn't support one). |
    | **Tags** | Names and values, e.g., for a project. |
    | **Volumes** | Paths in the container that the executors share. |

4. Select **Submit Task**. Krini shows "Task submitted successfully!" with
   the ID of the new task, or the error of the service. **Reset** clears
   the form.

## Follow your tasks

**Tasks** lists the tasks of the selected service, ten per page, with
their names, states and creation times. You can search them by the
beginning of their names, and filter them by state.

What a TES service lists depends on the service: a gateway such as proTES
lists only your own tasks, others may list the tasks of all users.

**View Details** opens the details of a task: its state, executors,
inputs and outputs, resources, tags and logs, with the standard output and
standard error of each executor. The details page always shows the task on
the service that you listed it from, so you can reload or bookmark it.

**Cancel**, in the list or on the details page, cancels a task that hasn't
finished; it doesn't remove it from the list.

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

### No WES service yet

As of November 2026, there is no WES service that you can select in
Krini: the only WES service in the Cloud Registry is registered with the
address of its service info instead of its API, so Krini leaves it out.
Until a WES service is registered and reachable, the steps below can't be
followed at the portal. To run workflows now, let a workflow engine send
their tasks to a TES service (see [Run Workflows Across
Nodes](federated-workflows.md)).

### Submit a run

With a WES service in the list and [compute access](#before-you-start):

1. Open **Workflows** and select **Create Workflow**.
2. Choose a WES service in **Select WES Instance**. Krini shows the
   workflow types and versions that it supports.
3. Fill in the form:

    | Field | What to enter |
    |---|---|
    | **Workflow URL** (required) | The address of the workflow file, e.g., on GitHub (use the raw file), or a path within the files that you attach. |
    | **Workflow Type**, **Workflow Type Version** (required) | One of the types and versions that the service supports. |
    | **Workflow Parameters (JSON)** | The inputs of the workflow as a JSON object, e.g., `{"input_file": "https://example.com/input.txt"}`. |
    | **Engine Parameters (JSON)**, under **Advanced Configuration** | Settings of the workflow engine, if the service accepts them. |
    | **Tags (Optional)** | Keys and values, e.g., for a project. |
    | **Workflow Attachments (Optional)** | Files that the service needs next to the workflow, e.g., its other files or a configuration (**Add Files**). |

4. Select **Submit Run**. Krini shows the run ID, or the error of the
   service. **Reset** clears the form.

## Follow your workflow runs

**Workflows** lists the runs of the selected service, ten per page, with
their run IDs and states. **Cancel** stops a run that hasn't finished.

The states are those of WES: `QUEUED`, `INITIALIZING`, `RUNNING`, `PAUSED`,
`COMPLETE`, `EXECUTOR_ERROR`, `SYSTEM_ERROR`, `CANCELING`, `CANCELED`,
`PREEMPTED` and `UNKNOWN` (see [Follow your tasks](#follow-your-tasks) for
what they mean).

### Read the details and outputs of a run

**View Details** opens the details of a run: its state, the request
(workflow URL, type, parameters, engine parameters and tags), the log of
the run and of its tasks, and its outputs. Like the task details, the page
always shows the run on the service that you listed it from. Where the
outputs are depends on the service, e.g., in a bucket of its object
storage.

## Copy your access token

To use the services outside Krini, e.g., with `curl` or the [command
line](cli.md) (see [Using the APIs](../partners-and-developers/apis.md)),
select **Copy access token** in the menu at the bottom of the sidebar.
Krini copies your LS Login access token to the clipboard. proTES accepts
tokens that LS Login issued to Krini.

!!! warning "Keep your token to yourself"
    Anyone with your token can act as you at the services until it expires.
    Don't share it, and don't paste it into chats, issues or files that you
    commit.

The token expires after a while; copy a new one when a service answers
`401 Unauthorized`.

## Troubleshooting

| Message | What to do |
|---|---|
| **Request compute access** or **Compute access required** instead of **Create Task** | You aren't a member of `ECP_CLN:EOC-Compute`. Apply (see [Before you start](#before-you-start)); if you were approved after you logged in, log out and log in again. |
| "Login to fetch TES servers from registry." | The Cloud Registry asked for a login. Log in and open the page again. |
| "Failed to fetch TES servers." or "Failed to load WES instances" | Krini couldn't reach the Cloud Registry. Try again later; for WES, select **Retry**. |
| A WES service is greyed out in the list | The service didn't answer. Select **Refresh** later. |
| "Service Information Unavailable" | The WES service didn't say which workflow types it supports. You can still submit, but check with its operator first. |
| "Identity Provider Error" in the sidebar | Krini couldn't reach LS Login. Select the message to try again. |
| "Invalid state found. State does not match." or "Invalid request parameters found." after login | The login didn't complete. Select **Go to Login** and log in again. |
| A service answers `401` or `403` | You aren't logged in, your token expired, or the service doesn't give you access. Log in again, or ask for access (see [Before you start](#before-you-start)). |

## What's coming

These are planned in the [Krini repository][krini-repo], not available yet:

- Forms for workflow inputs, built from the workflow's I/O schema
  ([krini#47](https://github.com/elixir-cloud-aai/krini/issues/47)).
- For tasks through the proTES gateway: where a task ran
  ([krini#48](https://github.com/elixir-cloud-aai/krini/issues/48)), and
  which gateway plugins to use
  ([krini#49](https://github.com/elixir-cloud-aai/krini/issues/49)).
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
