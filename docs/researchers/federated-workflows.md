# Run Workflows Across Nodes

This page shows how to run a Snakemake workflow on the TES services of
several Nodes, with the demonstrator `demo-tes-hybrid-cloud`. The workflow
splits into steps that a [GA4GH Task Execution Service][ga4gh-tes] (TES) runs
as tasks. The demonstrator runs it on each TES service in turn, and then on
all of them together through the [proTES](https://protes.readthedocs.io/en/latest/)
gateway, which forwards each task to one of the TES services.

!!! warning "Outdated demonstrator"
    The demonstrator dates from 2023 and was not updated for the current
    products: its README lists the versions that it was built for, e.g., the
    proTES image `elixircloud/protes:20230218`. The steps below include what
    differs today (see [Differences to the
    README](#differences-to-the-readme)). There is no public deployment with
    a guaranteed uptime, either: deploy the services yourself or write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email]. See
    [Demos](../demos/index.md) for the state of all demos.

## What you need

- Git, Conda or Mamba, and [JupyterLab](https://jupyterlab.readthedocs.io/)
  (the README lists all requirements).
- The addresses of one or more TES services (see [Start
  Here](index.md#before-you-start)), and the credentials of the Funnel
  services among them.
- The address of a proTES gateway in front of these services, and an access
  token for it (see [Using the
  APIs](../partners-and-developers/apis.md#2-get-an-access-token)).
- An S3 bucket that the TES services can write to, and its credentials. The
  workflow writes its results there.

## Steps

1. Clone the [repository][elixir-cloud-demo-smk] and install the
   requirements as its README describes, with Snakemake 7. Instead of the
   `py-tes` commit of the README, install `py-tes` 1.1.4 or later:

    ```bash
    pip uninstall -y py-tes
    pip install "py-tes>=1.1.4"
    ```

2. In `wf-federated/config.yaml`, check that each of the URLs under `urls`
   still resolves, and replace those that don't with the URL of any small
   image file. The workflow downloads each of them in a task of its own.
3. Create two files in the repository, as the section "Create
   configuration files" of the README shows. The README also asks for a
   file `.inputs`, which the notebook doesn't read.
    - `.tes_instances`: the name and the URL of each TES service, one per
      line;
    - `.env`: the variables below, each as a line `export NAME=value`, so
      that Snakemake, which the notebook starts, gets them. It holds
      passwords and a token: never commit or share it, and make only you
      able to read it (`chmod 600 .env`).

    | Variable | Value |
    |---|---|
    | `FUNNEL_SERVER_USER`, `FUNNEL_SERVER_PASSWORD` | The credentials of the Funnel services. |
    | `TES_GATEWAY` | The address of the proTES gateway. |
    | `TES_TOKEN` | The access token for the proTES gateway. Snakemake 7 sends it as a bearer token (see [Differences to the README](#differences-to-the-readme)). |
    | `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY` | The credentials of the S3 bucket. |
    | `ENDPOINT_URL` | The address of the S3 service. |
    | `BUCKET_PATH` | The bucket, and optionally a path in it, for the results. |

4. Start the notebook:

    ```bash
    jupyter-lab demo.ipynb
    ```

5. Run the cells of the notebook in order. It lists the TES services, runs
   the workflow on each of them, and then runs it through the gateway, which
   forwards each task to one of the TES services. The notebook runs Bash
   (`bash_kernel`, from the `environment.yml`), and Snakemake inherits the
   environment of its cells. Before the cell that uses the gateway, add a
   cell with `unset FUNNEL_SERVER_USER FUNNEL_SERVER_PASSWORD` (see below).

The notebook has the details of each step.

## Differences to the README

The README was written for the products of 2023. The changes below follow
from the docs and the code of the products; they have not been run end to
end yet. Today:

- **Access token:** proTES 0.3.0 and later require an access token for all
  task requests, and don't accept Basic credentials. Snakemake 7 sends the
  token of `TES_TOKEN` through `py-tes`, but the `py-tes` commit that the
  README installs replaces it with Basic credentials, even if none are set.
  Install `py-tes` 1.1.4 or later instead (`pip install "py-tes>=1.1.4"`),
  which sends the token as long as no Basic credentials are set, and unset
  the credentials of the Funnel services before the run through the gateway,
  as in the steps above.
- **Results in S3:** the workflow reads the S3 settings from the
  environment, but the README's `.env` doesn't list them. Add them, as above.
- **Routing by distance:** the notebook expects proTES to send each task to
  the TES service closest to its input data. Since proTES 0.5.0, proTES routes
  tasks in random order by default; the operator of the gateway enables
  routing by distance (see [Routing by distance to the
  data](https://protes.readthedocs.io/en/latest/plugins/#routing-by-distance-to-the-data-opt-in)).
  Without it, the workflow runs as well, on TES services chosen at random.
- **TES services of the gateway:** proTES 0.4.0 and later list them in
  `custom.tes.backends` instead of `tes.service_list` (see the [upgrade
  steps](https://protes.readthedocs.io/en/latest/upgrading/)).
- **Snakemake:** the demonstrator needs Snakemake 7 (`--tes`), as its
  `environment.yml` sets. Snakemake 8 and later send tasks to TES with the
  [TES executor
  plugin](https://github.com/snakemake/snakemake-executor-plugin-tes)
  instead, and read remote files with storage plugins.

## Use your own workflow

Snakemake, Nextflow and `cwl-tes` can send the tasks of any workflow to a TES
service. See [Run workflows through
TES](../partners-and-developers/ga4gh-standards.md#run-workflows-through-tes).
The CWL demonstrator that this one was adapted from is
[retired](../demos/index.md#retired-demos).
