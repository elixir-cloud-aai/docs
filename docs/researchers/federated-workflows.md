# Run Workflows Across Nodes

This page shows how to run a Snakemake workflow on the TES services of
several Nodes, with the demonstrator `demo-tes-hybrid-cloud`. The workflow
splits into steps that a [GA4GH Task Execution Service][ga4gh-tes] (TES) runs
as tasks. The demonstrator runs it on each TES service in turn, and then on
all of them together through the [proTES](https://protes.readthedocs.io/en/latest/)
gateway, which forwards each task to one of the TES services.

!!! warning "Under construction"
    The demonstrator dates from 2023 and was not updated for the current
    products. Its README lists the versions that it was built for: for
    example, the proTES image `elixircloud/protes:20230218`. proTES 0.4.0
    configures its TES services differently (`custom.tes.backends` instead
    of `tes.service_list`: see the [upgrade
    steps](https://protes.readthedocs.io/en/latest/upgrading/)). There is no
    public deployment with a guaranteed uptime, either. Until both are
    documented, deploy the services yourself or write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email].

## What you need

- Git, Conda or Mamba, and [JupyterLab](https://jupyterlab.readthedocs.io/)
  (the README lists all requirements).
- The addresses of one or more TES services (see [Start
  Here](index.md#before-you-start)), and the credentials of the Funnel
  services among them.
- The address of a proTES gateway in front of these services.
- Input files that the TES services can download from a URL.

## Steps

1. Clone the [repository][elixir-cloud-demo-smk] and install the
   requirements as its README describes. This includes a `py-tes` version
   from a specific commit.
2. Create three files in the repository, as the section "Create
   configuration files" of the README shows:
    - `.tes_instances`: the name and the URL of each TES service, one per
      line;
    - `.inputs`: the location and the URL of each input file, and one line
      `workflow` with the input of the workflow;
    - `.env`: `FUNNEL_SERVER_USER` and `FUNNEL_SERVER_PASSWORD` for Funnel
      services, and `TES_GATEWAY`, the address of the proTES gateway.
3. Start the notebook:

    ```bash
    jupyter-lab demo.ipynb
    ```

4. Run the cells of the notebook in order. It lists the TES services, runs
   the workflow on each of them, and then runs it through the gateway, which
   forwards each task to one of the TES services.

The notebook has the details of each step. To follow the same idea with CWL
workflows, see the [CWL demonstrator][elixir-cloud-demo-cwl].

## Use your own workflow

Snakemake, Nextflow and `cwl-tes` can send the tasks of any workflow to a TES
service. See [Run workflows through
TES](../partners-and-developers/ga4gh-standards.md#run-workflows-through-tes).
