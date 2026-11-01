# CWL-WES

[CWL-WES](https://github.com/elixir-cloud-aai/cwl-wes) is a [GA4GH
WES][ga4gh-wes] service for workflows in the Common Workflow Language
(CWL). It breaks a workflow into tasks and sends them to a [GA4GH
TES][ga4gh-tes] service, such as [TESK](tesk.md) or [Funnel](funnel.md).

## Role in the deployment

CWL-WES lets users run CWL workflows on a TES service of a Node. Its
development is in the beta stage.

## Docs

CWL-WES has no separate docs site. Use these:

- [README](https://github.com/elixir-cloud-aai/cwl-wes#readme)
- [Helm chart for Kubernetes](https://github.com/elixir-cloud-aai/cwl-wes/tree/dev/deployment)

!!! warning "Under construction"
    It is not documented yet which TES service the ELIXIR On-Cloud's
    CWL-WES uses.
