# GA4GH Standards

ELIXIR On-Cloud is a [Driver Project][ga4gh-dps] of the [GA4GH][ga4gh]. Its
services implement the APIs of the [GA4GH Cloud Workstream][ga4gh-cloud-ws].
This page lists them, the versions that the stack implements and the workflow
engines that can use them. The specifications define what each API does: read
them, not this page, for the details.

## APIs and versions

| API | Current version | In the stack | Docs |
| --- | --- | --- | --- |
| [TES][ga4gh-tes], for tasks | [1.1.0](https://ga4gh.github.io/task-execution-schemas/) | proTES (1.0), [TESK][tesk] (1.0), [Funnel][funnel] (not stated in its docs) | [proTES](https://protes.readthedocs.io/en/latest/), [TESK](https://tesk.readthedocs.io/en/latest/) |
| [WES][ga4gh-wes], for workflows | [1.1.0](https://ga4gh.github.io/workflow-execution-service-schemas/) | [proWES](https://github.com/elixir-cloud-aai/proWES) (1.0.1), [CWL-WES](https://github.com/elixir-cloud-aai/cwl-WES) (1.0.0) | see the READMEs |
| [DRS][ga4gh-drs], for data | [1.5.0](https://ga4gh.github.io/data-repository-service-schemas/) | [DRS-Filer](https://github.com/elixir-cloud-aai/drs-filer) (1.1.0) | see the README |
| [TRS][ga4gh-trs], for tools and workflows | [2.0.1](https://ga4gh.github.io/tool-registry-service-schemas/) | [TRS-Filer](https://github.com/elixir-cloud-aai/trs-filer) (2.0.1) | [TRS-Filer](https://trs-filer.readthedocs.io/en/latest/) |
| [Service Registry][ga4gh-service-registry], for finding services | [1.0.0](https://github.com/ga4gh-discovery/ga4gh-service-registry) | [Cloud Registry](https://github.com/elixir-cloud-aai/cloud-registry) (1.0.0) | [Cloud Registry](https://cloud-registry.readthedocs.io/en/latest/) |

The versions in brackets are the versions of the specification that each
product implements, as of November 2026. Check the product's docs for the
current state. Some products deviate from the specification in details: the
docs of the product list the deviations (for example, see the [Cloud Registry
API](https://cloud-registry.readthedocs.io/en/latest/api/#deviations-from-the-ga4gh-specification)).

!!! note "Do your clients support a newer version?"
    Several products implement an older version than the current one. Send
    requests that the version in the table accepts, and read the service
    info of a service (`GET /service-info`) to see what it reports.

## Run workflows through TES

Workflow engines can send their tasks to a TES service instead of running
them on the local machine. This helps if a workflow has steps that need a
GPU or many cores, or if the data must stay at the site where it is stored.

1. Choose a TES service: see [Using the APIs](apis.md).
2. Get an access token: see [Using the APIs](apis.md#2-get-an-access-token).
3. Configure your workflow engine to use the TES service and the token.

The engines below support TES. Each one's docs describe the configuration.

- **Snakemake** uses the [TES executor
  plugin](https://github.com/snakemake/snakemake-executor-plugin-tes). A
  [demo workflow][elixir-cloud-demo-smk] for Snakemake 7, which had TES
  support built in, is available: see [Run Workflows Across
  Nodes](../researchers/federated-workflows.md).
- **Nextflow** uses the [`nf-ga4gh`
  plugin](https://github.com/nextflow-io/nf-ga4gh). Set `plugins { id
  'nf-ga4gh' }` and `process.executor = 'tes'` in `nextflow.config`.
- **cwl-tes** runs CWL workflows with a TES backend: see [cwl-tes][cwl-tes].
  Its [demo of 2023][elixir-cloud-demo-cwl] is
  [retired](../demos/index.md#retired-demos).

For the researcher's view, see [Researchers](../researchers/index.md).
