# Tutorial: Your First Run in Krini

## Synopsis

This tutorial takes you from your first login to the results of your first
analysis in [Krini][krini-repo], the web portal of ELIXIR On-Cloud. You count
the lines, words and characters of a small text file twice: once as a
[GA4GH TES][ga4gh-tes] task, and once as a [GA4GH WES][ga4gh-wes] workflow.
It takes about 30 minutes, and you need nothing but a web browser and, for
the last part, a terminal.

The tutorial uses the demo files in this documentation. Each step does one
thing and links to the [Krini user guide](krini.md), which explains every
field, button and message; this page doesn't repeat it.

!!! note "The new Krini"
    This tutorial describes the new Krini (branch `staging` of the [Krini
    repository][krini-repo], commit
    [`c81a259`](https://github.com/elixir-cloud-aai/krini/commit/c81a259)),
    like the [Krini user guide](krini.md). Parts of it are still in progress
    (see [What's coming](krini.md#whats-coming)), so what you see can
    differ.

!!! warning "Synthetic or public data only"
    The deployment is a sandbox for demos and tests. The demo file is public;
    don't use Krini with personal or other sensitive data.

## 1. Before you start

You need:

- **An LS Login account.** See [Before you start](krini.md#before-you-start)
  in the user guide.
- **Access to a TES service that accepts requests without a token,** for
  part 1. Krini doesn't send your token to TES services yet (see [Run a
  task](krini.md#run-a-task)).
- **Access to a WES service that runs CWL `v1.0`,** for part 2.

Krini shows the services of the Cloud Registry, but doesn't give you access
to them. To ask for services that you can use, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email] and say that you
want to follow this tutorial.

The demo files:

| File | What it is |
|---|---|
| [`LICENSE`](https://raw.githubusercontent.com/elixir-cloud-aai/docs/main/LICENSE) of this documentation | The text file that you count. |
| [`count-words.cwl`](tutorial-files/count-words.cwl) | A workflow in CWL that counts the lines, words and characters of a text file with `wc`, in the container image `alpine:3.20`. |
| [`count-words.json`](tutorial-files/count-words.json) | The parameters of the workflow: the address of the text file. |

## 2. Log in

1. Open Krini in your browser.
2. Log in with LS Login, as [Log in](krini.md#log-in) describes.

**Check:** the sidebar shows your name and email address.

## Part 1: Run a task

A TES task runs a command in a container. Here, the command is `wc`, and the
service copies the text file into the container before the command starts.

### 3. Choose a TES service

1. Open **Tasks** in the sidebar.
2. Choose the TES service that you got access to in **Select TES Instance**
   (see [Choose a service](krini.md#choose-a-service)).

**Check:** the list below shows the tasks of the service, or none.

!!! warning "Don't choose TEST SERVER"
    The **TEST SERVER** entry in the list of TES services doesn't work yet
    ([krini#67](https://github.com/elixir-cloud-aai/krini/issues/67)).
    Choose the service that you got access to.

### 4. Create the task

1. Select **Create Task**.
2. Fill in the form with these values, and leave the other fields empty
   (see [Run a task](krini.md#run-a-task) for all fields):

    | Field | Value |
    |---|---|
    | **Name** | `count-words` |
    | **Executors** › **Image** | `alpine:3.20` |
    | **Executors** › **Commands** | `wc` in the first field, `/data/LICENSE` in the second |
    | **Inputs** › **URL** | `https://raw.githubusercontent.com/elixir-cloud-aai/docs/main/LICENSE` |
    | **Inputs** › **Path** | `/data/LICENSE` |

3. Submit the form.

**Check:** Krini shows the ID of the new task. Note it.

!!! tip "If the service can't fetch the input"
    Not every TES service can fetch files from an `https` address. If the
    task ends in `SYSTEM_ERROR`, create it again without the input, with the
    commands `echo` and `Hello`. That checks everything else.

### 5. Follow the task and read the result

1. Open **Tasks** again. Your task is in the list with its state (see
   [Follow your tasks](krini.md#follow-your-tasks) for what the states
   mean).
2. Wait until the state is `COMPLETE`. Tasks first wait in `QUEUED` until the
   service has resources; this can take a few minutes.
3. Expand the task and read the standard output in its logs.

**Result:** the standard output of `wc`, the numbers of lines, words and
characters of the file:

```text
      121      1066      7048 /data/LICENSE
```

The numbers change if the file changes. If the state is `EXECUTOR_ERROR` or
`SYSTEM_ERROR`, read the logs and see
[Troubleshooting](krini.md#troubleshooting).

!!! warning "No result files from tasks yet"
    This task writes its result to the standard output only. Tasks that
    write result files need **Outputs**, which the task form of Krini
    doesn't pass on to the service yet
    ([cloud-components#574](https://github.com/elixir-cloud-aai/cloud-components/issues/574);
    see [Run a task](krini.md#run-a-task)). Part 2 gets a result file
    through WES instead.

## Part 2: Run a workflow

A WES service runs a whole workflow. Here, the workflow is
[`count-words.cwl`](tutorial-files/count-words.cwl), which does the same as
the task, and writes the result to the file `counts.txt`.

### 6. Choose a WES service

1. Open **Workflows** in the sidebar.
2. Choose the WES service that you got access to in **Select WES Instance**
   (see [Choose a service](krini.md#choose-a-service)). Choose only a
   service that you trust: Krini sends it your token.
3. Point at the info icon next to the service and check that it supports
   the workflow type `CWL` in the version `v1.0`.

If no WES service that you can use runs CWL `v1.0`, stop after part 1 and
ask the operators for access to one that does: the steps below work only
with CWL `v1.0`.

### 7. Start the workflow

1. Select **Create Workflow**.
2. Fill in the form (see [Run a workflow](krini.md#run-a-workflow) for all
   fields):

    | Field | Value |
    |---|---|
    | **Workflow URL** | `https://raw.githubusercontent.com/elixir-cloud-aai/docs/main/docs/researchers/tutorial-files/count-words.cwl` |
    | **Workflow Type** | `CWL` |
    | **Workflow Type Version** | `v1.0` |
    | **Workflow Parameters (JSON)** | The content of [`count-words.json`](tutorial-files/count-words.json), shown below |

    ```json
    {
      "text": {
        "class": "File",
        "location": "https://raw.githubusercontent.com/elixir-cloud-aai/docs/main/LICENSE"
      }
    }
    ```

3. Select **Submit Run**.

**Check:** Krini shows the run ID. Note it.

### 8. Follow the run

1. Open **Workflows** again. Your run is in the list with its state (see
   [Follow your workflow runs](krini.md#follow-your-workflow-runs)).
2. Wait until the state is `COMPLETE`.

### 9. Read the result

!!! warning "No run details in Krini yet"
    **View Details** doesn't open anything in Krini yet
    ([krini#66](https://github.com/elixir-cloud-aai/krini/issues/66)), so
    this step needs a terminal.

Read the details and outputs of the run from the WES service, with your
access token, as [Read the details and outputs of a
run](krini.md#read-the-details-and-outputs-of-a-run) describes: copy your
token in Krini, look up the API endpoint of the service, and call it with
`curl` and your run ID.

**Result:** in the answer, `outputs` lists the file `counts.txt` with its
address. Where the file is, and how you download it, depends on the service,
e.g., in a bucket of its object storage. Its content is the same as in step
5, without the file name:

```text
      121      1066      7048
```

## 10. Clean up

- Log out of Krini (see [Log in](krini.md#log-in)).
- In the terminal, end the session in which you pasted your token, or remove
  it with `unset TOKEN`.

## Where to go next

- Run your own task or workflow: the [Krini user guide](krini.md) explains
  all fields, and [GA4GH TES][ga4gh-tes] and [GA4GH WES][ga4gh-wes] the
  APIs.
- Do the same from your terminal: [Tutorial: Your First Run from the Command
  Line](tutorial-cli.md).
- Run a workflow on the TES services of several Nodes: [Run Workflows
  Across Nodes](federated-workflows.md).

## How this tutorial was tested

The workflow [`count-words.cwl`](tutorial-files/count-words.cwl) ran with
`cwltool` and Docker on one computer, with
[`count-words.json`](tutorial-files/count-words.json), and gave the result
shown in step 9. The values of the forms follow the [Krini user
guide](krini.md) and the source code of Krini at commit `c81a259`. The steps
have not yet been run against a deployed Krini and deployed TES and WES
services, and not yet by someone who didn't write them. If you follow this
tutorial, please tell us what didn't work: in the
[Discussions][elixir-on-cloud-forum] or in an issue in the [docs
repository](https://github.com/elixir-cloud-aai/docs/issues).

[krini-repo]: <https://github.com/elixir-cloud-aai/krini>
