# GA4GH Standards

ELIXIR On-Cloud is a [Driver Project][ga4gh-dps] of the [GA4GH][ga4gh]. Its
services implement the APIs of the [GA4GH Cloud Workstream][ga4gh-cloud-ws].
This page lists them, the versions that the stack implements and the workflow
engines that can use them. The specifications define what each API does: read
them, not this page, for the details.

## APIs and versions

The table lists, for each product, the version of the specification that it
implements and the current release of the specification. Each version links
to its source: the API specification (or the commit of the specification)
that the product's default branch builds on, and the release page of the
specification. Checked in November 2026.

| Product | API | Implemented version | Current version | Docs |
| --- | --- | --- | --- | --- |
| [proTES](https://github.com/elixir-cloud-aai/proTES) | [TES][ga4gh-tes], for tasks | [1.1.0](https://github.com/elixir-cloud-aai/proTES/blob/dev/pro_tes/api/20221114.117cd92.task_execution_service.openapi.yaml) | [1.1.0](https://github.com/ga4gh/task-execution-schemas/releases/tag/v1.1) | [proTES](https://protes.readthedocs.io/en/latest/) |
| [TESK][tesk] | [TES][ga4gh-tes], for tasks | [1.0.0](https://github.com/ga4gh/task-execution-schemas/blob/cafac9c47fddfa512e844c96ee4bcb2fb63d90c6/openapi/task_execution_service.openapi.yaml) (submodule of [tesk-api](https://github.com/elixir-cloud-aai/tesk-api)) | [1.1.0](https://github.com/ga4gh/task-execution-schemas/releases/tag/v1.1) | [TESK](https://tesk.readthedocs.io/en/latest/) |
| [Funnel][funnel] | [TES][ga4gh-tes], for tasks | 1.1.0 and later changes: not stated as a release; [its submodule](https://github.com/calypr/funnel/tree/develop/api/tes) points to a commit after 1.1.0 | [1.1.0](https://github.com/ga4gh/task-execution-schemas/releases/tag/v1.1) | [Funnel][funnel] |
| [proWES](https://github.com/elixir-cloud-aai/proWES) | [WES][ga4gh-wes], for workflows | [1.0.1](https://github.com/elixir-cloud-aai/proWES/blob/dev/pro_wes/api/20201124.tag_1_0_1.workflow_execution_service.openapi.yaml) | [1.1.0](https://github.com/ga4gh/workflow-execution-service-schemas/releases/tag/1.1.0) | see the README |
| [CWL-WES](https://github.com/elixir-cloud-aai/cwl-WES) | [WES][ga4gh-wes], for workflows | [1.0.0](https://github.com/elixir-cloud-aai/cwl-WES/blob/dev/cwl_wes/api/20181010.be85140.workflow_execution_service.swagger.yaml) | [1.1.0](https://github.com/ga4gh/workflow-execution-service-schemas/releases/tag/1.1.0) | see the README |
| [DRS-Filer](https://github.com/elixir-cloud-aai/drs-filer) | [DRS][ga4gh-drs], for data | [1.1.0](https://github.com/elixir-cloud-aai/drs-filer/blob/dev/drs_filer/api/20200622.383121d.data_repository_service.swagger.yaml) | [1.5.0](https://github.com/ga4gh/data-repository-service-schemas/releases/tag/drs-1.5.0) | see the README |
| [TRS-Filer](https://github.com/elixir-cloud-aai/trs-filer) | [TRS][ga4gh-trs], for tools and workflows | [2.0.2](https://github.com/elixir-cloud-aai/trs-filer/blob/dev/trs_filer/api/20250902.4854e2f.openapi.yaml) | [2.0.2](https://github.com/ga4gh/tool-registry-service-schemas/releases/tag/2.0.2) | [TRS-Filer](https://trs-filer.readthedocs.io/en/latest/) |
| [Cloud Registry](https://github.com/elixir-cloud-aai/cloud-registry) | [Service Registry][ga4gh-service-registry], for finding services | [1.0.0](https://github.com/elixir-cloud-aai/cloud-registry/blob/dev/cloud_registry/api/20201108.e0358db.openapi.yaml) | [1.0.0](https://github.com/ga4gh-discovery/ga4gh-service-registry/releases/tag/1.0.0) | [Cloud Registry](https://cloud-registry.readthedocs.io/en/latest/) |

Notes on the table:

- **TRS-Filer:** its specification file states `2.1.0`, but it is the
  specification of the TRS release 2.0.2 (commit `4854e2f`); TRS 2.1.0 is
  not released.
- **Funnel:** [Funnel][funnel] (now in the `calypr` organisation) doesn't
  state a TES release. It builds on a commit of the TES repository after
  1.1.0, whose specification file states `1.1.0`.
- **TESK:** the TES API is implemented by tesk-api, which includes the TES
  specification as a Git submodule.

Check the product's docs for the current state. Some products deviate from
the specification in details: the docs of the product list the deviations
(for example, see the [Cloud Registry
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
