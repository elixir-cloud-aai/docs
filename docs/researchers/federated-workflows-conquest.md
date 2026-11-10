# Federate Workflows with Conquest

[Conquest][conquest] is a [GA4GH WES][ga4gh-wes] and [TES][ga4gh-tes]
service. It runs Nextflow, Snakemake and WDL workflows, and sends each task
of a workflow to its own Kubernetes cluster or to a remote TES service, such
as Funnel or TESK, at another site. This page describes how that works and
which workflows, workflow engines and TES services were tested together.

!!! warning "Draft"
    This page is a first draft, and it describes test deployments: three
    single-node clusters in one OpenStack project, connected over plain
    HTTP, with no authentication. Conquest is not a service of the ELIXIR
    On-Cloud deployment, and no Node runs it yet. To try it, deploy it
    yourself from its [repository][conquest], or write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email].

## How it works

| Part | Service | Role |
|---|---|---|
| Workflow API | Conquest (WES) | Accepts runs of Nextflow, Snakemake and WDL workflows, and starts one workflow engine per run in its own Kubernetes cluster. |
| Task API | Conquest (TES) | Accepts the tasks of the engines. Decides where each task runs, and submits it there. |
| Local compute | Kubernetes | Runs the tasks that stay at the site of Conquest. |
| Remote compute | Funnel, TESK | TES services at other sites, which run the tasks that Conquest sends them. |
| Storage | S3, for example SeaweedFS or MinIO | Holds the inputs, intermediate files and results of a run. |
| Storage gateway | Conquest | Gives remote TES services access to the files of a task, without S3 credentials. |

### The call chain

```text
client ── WES run ──▶ Conquest WES ──▶ workflow engine (Kubernetes Job)
                                            │ TES task
                                            ▼
                                      Conquest TES ── route ──┬─▶ Kubernetes (local)
                                                              ├─▶ Funnel (remote)
                                                              └─▶ TESK (remote)
remote task ── HTTP GET/PUT ──▶ Conquest storage gateway ── 307 ──▶ presigned S3 URL
```

1. A client submits a run (`POST /ga4gh/wes/v1/runs`): the workflow's
   repository and revision, its parameters, and tags.
2. Conquest starts the workflow engine as a Kubernetes Job. The engine
   talks to Conquest's own TES API through a plugin: `nf-ga4gh` for
   Nextflow, a TES executor plugin for Snakemake and a container backend
   for miniwdl (WDL).
3. For each step of the workflow, the engine creates a TES task. Conquest
   stores it and answers at once.
4. A dispatcher decides where the task runs and submits it there. The
   decision follows the operator's rules (see [Route tasks](#route-tasks)).
   A task that may only run locally, for example because it uses a shared
   file system, stays in Kubernetes.
5. A task for a remote TES service is translated for it: the S3 URLs of its
   inputs and outputs become URLs of the storage gateway, and fields that
   the service doesn't support are adapted or left out.
6. The remote service downloads the inputs, runs the task and uploads the
   outputs through the gateway. The gateway checks that the task may read or
   write each file, and redirects the request to an S3 URL that it signs
   for that file. The remote service never gets S3 credentials.
7. Conquest follows the state of every task, local or remote, and reports it
   to the engine, which carries on with the next steps. When the run ends,
   its results are in Conquest's S3 bucket, where WES lists them.

## Route tasks

The operator of Conquest configures the remote TES services and the rules
that send tasks to them. A rule matches tasks by workflow engine, task name
and run tags, and lists the services to try in order:

```yaml
endpoints:
  - name: funnel-a
    url: https://funnel.example.org/v1
    s3_url_style: gateway
    data_classes: [unclassified]
routing:
  rules:
    - name: align-remotely
      match:
        engines: [nextflow]
        run_tags: {federate: "1"}
        task_names: ["*:BWAMEM1_MEM (*"]
      backends: [funnel-a, local]
```

A task goes to the first service in the list that can take it: a service
receives only the data classes that it lists (run tag
`conquest.data_class`), and only tasks whose resources and TES features it
supports. If a service refuses a task, the next one is tried; a task that
matches no rule runs locally. The route of every task is stored with it and
shown in its TES logs.

Researchers choose rules with the tags of their runs, and can ask for
services with the tag `conquest.tes_backend`, if the operator allows it.
The rules decide where tasks may run; Conquest does not yet balance the load
between services.

## What was tested

### Workflow engines

| Workflow type | Engine | Versions | Connection to Conquest's TES API |
|---|---|---|---|
| Nextflow (DSL2) | Nextflow | 25.04.3, 25.10.4 | `nf-ga4gh` 1.3.0, 1.4.0 |
| Snakemake | Snakemake | 9.17.3 | Conquest's TES executor plugin |
| WDL 1.0 | miniwdl | 1.12.1 | Conquest's container backend plugin |

### Workflows

| Workflow | Type | Version | Data |
|---|---|---|---|
| [nf-core/sarek](https://nf-co.re/sarek) | Nextflow | 3.8.1 (`4bd2948f`) | `test` profile; and GIAB HG002, Illumina NovaSeq PCR-free 35x, chromosome 20 (9.5 million read pairs) on GRCh38 |
| [nf-core/methylseq](https://nf-co.re/methylseq) | Nextflow | 4.2.0 (`5aa56467`) | `test` profile |
| [broadinstitute/viral-pipelines](https://github.com/broadinstitute/viral-pipelines) `assemble_refbased` | WDL | `125237d4` | Ebola test reads of the repository; and six SARS-CoV-2 ARTIC v3 runs from ENA (PRJEB45515, PRJEB48985) |
| [snakemake-workflows/rna-seq-star-deseq2](https://github.com/snakemake-workflows/rna-seq-star-deseq2) | Snakemake | `b9617cfe` | Yeast RNA-seq, STB5 overexpression against control, 8 runs from ENA (PRJEB30262) |

### TES services

| Service | Implementation | Version | Notes |
|---|---|---|---|
| Local | Conquest's Kubernetes backend | Conquest `master`, up to `2afe95c` | Kubernetes 1.33 (Talos 1.10) |
| Remote | [Funnel][funnel] | `develop` at `a3be3b20`, with [calypr/funnel#1488](https://github.com/calypr/funnel/pull/1488) | Kubernetes compute backend. No S3 credentials: files only through the storage gateway |
| Remote | [TESK][tesk] | TESK API and tesk-core from [tesk-api#133](https://github.com/elixir-cloud-aai/tesk-api/pull/133) and [tesk-core#134](https://github.com/elixir-cloud-aai/tesk-core/pull/134), based on 1.2.0 and 0.11.0; TESK chart from `dev` | TES 1.1 outputs (`path_prefix`). Earlier, TESK API 1.1.0 with tesk-core 0.10.6 ran as a TES 1.0 service and could take only tasks without wildcard outputs |
| Storage | [SeaweedFS](https://github.com/seaweedfs/seaweedfs) S3 | 4.52 | Conquest's bucket |

### Results

Each workflow ran twice: with its tasks split across Kubernetes, Funnel and
TESK, and with all tasks in Kubernetes. The results were compared.

| Workflow and data | Tasks: local / Funnel / TESK | Result |
|---|---|---|
| sarek, HG002 chromosome 20 | 6 / 24 / 4 | Variant calls identical to the local run. Against the GIAB v4.2.1 benchmark: SNP F1 0.991 (HaplotypeCaller) and 0.994 (Strelka2), indel F1 0.990 and 0.991 |
| sarek, `test` profile | 0 / 0 / 23; 6 / 14 / 3 | Variant records identical to the local run |
| methylseq, `test` profile | 21 / 7 / 1 | Methylation calls byte-identical to the local run |
| viral-pipelines, SARS-CoV-2 | 6 / 4 / 3 per sample | Consensus genomes identical to the local runs. Lineages B.1 and A.1 for the three Saudi samples; the Austrian submissions have read 2 identical to read 1 and fail QC |
| rna-seq-star-deseq2, yeast | 11 / 73 / 16 | Count matrix and DESeq2 results byte-identical to the local run; STB5 is 26-fold higher in the overexpression strain |

## Known limitations

- **Shared file systems:** tasks of runs that use a shared file system stay
  local. Workflows that read files they don't declare, such as
  [zavolanlab/zarp](https://github.com/zavolanlab/zarp), need one.
- **Inputs from other storage:** a task whose inputs or outputs are outside
  Conquest's bucket stays local. Nextflow copies remote inputs (HTTPS, FTP)
  into the bucket first, so its tasks can still be federated.
- **TES 1.0 services:** tasks with wildcard outputs, which most nf-core
  processes have, can't be sent to them.
- **Load:** the rules decide where tasks run; Conquest doesn't know how busy
  a service is.
- **Security of the tests:** the tests had no authentication and used plain
  HTTP. Conquest supports bearer, basic and OAuth 2.0 client credentials for
  remote services, but they were tested in unit tests only.
- **Poiesis:** [Poiesis](../operators/services/poiesis.md) was tested
  directly, not yet through Conquest.

## Where to go next

- The [Conquest repository][conquest], with the configuration of routing and
  of the storage gateway in its README.
- The TES services: [Funnel](../operators/services/funnel.md) and
  [TESK](../operators/services/tesk.md).
- Workflow engines that send their tasks to a TES service: [Run workflows
  through TES](../partners-and-developers/ga4gh-standards.md#run-workflows-through-tes).
- Questions: the [Discussions][elixir-on-cloud-forum] or the [About](../about.md)
  page.
