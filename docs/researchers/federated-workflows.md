# Run Workflows Across Nodes

This page shows how to run a Snakemake workflow on the TES services of
several Nodes, with the demonstrator `demo-tes-hybrid-cloud`. The workflow
splits into steps that a [GA4GH Task Execution Service][ga4gh-tes] (TES) runs
as tasks. The demonstrator runs it on each TES service in turn, and then on
all of them together through the [proTES](https://protes.readthedocs.io/en/latest/)
gateway, which forwards each task to one of the TES services.

The demonstrator runs with the current products: its CI runs it end to end
against proTES 0.6.0 and two Funnel instances. There is no public deployment
with a guaranteed uptime: try it on your computer first, then run it on your
own services, or write to [cloud-service@elixir-europe.org][elixir-on-cloud-email].
See [Demos](../demos/index.md) for the state of all demos.

!!! note "Cited version"
    Publications cite the release
    [1.0.0](https://github.com/elixir-cloud-aai/demo-tes-hybrid-cloud/releases/tag/1.0.0)
    ([10.5281/zenodo.17038656](https://doi.org/10.5281/zenodo.17038656)),
    which was built for the services of 2023. The steps below follow the
    default branch, which runs with the current products; check out the tag
    `1.0.0` only to reproduce the cited version.

## Try it out locally

The directory `local` of the [repository][elixir-cloud-demo-smk] runs all
services on one machine with Docker Compose: two Funnel instances, proTES in
front of them with a stand-in identity provider, and an S3 service. You need
Docker with Compose and access to the internet. From a clone of the
repository:

```bash
docker compose -f local/compose.yaml run --build --rm demo
```

The run ends with `PASSED: the demo ran end to end`. The section "Try it out
locally" of the README has the details and the commands to remove the setup
afterwards. All credentials of the setup are dummy values: use it for tests
only.

## Run it on your services

You need:

- Git, and Conda or Mamba (the README lists all requirements);
- the addresses of one or more TES services (see [Start
  Here](index.md#before-you-start)), and the credentials of the Funnel
  services among them;
- the address of a proTES gateway in front of these services, and an access
  token for it (see [Using the
  APIs](../partners-and-developers/apis.md#2-get-an-access-token));
- an S3 bucket that the TES services can write to, and its credentials. The
  workflow writes its results there.

Then follow the README of the [repository][elixir-cloud-demo-smk]: install
the Conda environment, create the files `.tes_instances` and `.env` as its
section "Create configuration files" shows, and run the notebook
`demo.ipynb`. The notebook runs the workflow on each TES service in turn, and
then through the gateway, and sends each service only its own credentials.
The file `.env` holds passwords and a token: never commit or share it.

proTES sends each task to one of its TES services at random by default; the
operator of the gateway can enable [routing by distance to the
data](https://protes.readthedocs.io/en/latest/plugins/#routing-by-distance-to-the-data-opt-in).

## Use your own workflow

Snakemake, Nextflow and `cwl-tes` can send the tasks of any workflow to a TES
service. See [Run workflows through
TES](../partners-and-developers/ga4gh-standards.md#run-workflows-through-tes).
The CWL demonstrator that this one was adapted from is
[retired](../demos/index.md#retired-demos).
