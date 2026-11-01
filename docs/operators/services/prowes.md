# proWES

[proWES](https://github.com/elixir-cloud-aai/proWES) is a gateway for
[GA4GH WES][ga4gh-wes] services. It receives workflow requests, applies
middleware (plugins) and forwards each request to one of the WES services
that it knows.

## Role in the deployment

proWES sits in front of WES services, for example [CWL-WES](cwlwes.md).

## Docs

proWES has no separate docs site. Use these:

- [README](https://github.com/elixir-cloud-aai/proWES#readme)
- [Helm chart for Kubernetes](https://github.com/elixir-cloud-aai/proWES/tree/dev/deployment)

!!! warning "Under construction"
    The address of the ELIXIR On-Cloud's proWES and the WES services that it
    uses are not documented yet.
