# proWES

!!! warning "Being revived"
    The [proWES](https://github.com/elixir-cloud-aai/proWES) repository is
    being revived since 2026-11-16, after it had been archived. The
    ELIXIR On-Cloud doesn't run proWES yet. This page and the docs of
    proWES follow with the revival.

[proWES](https://github.com/elixir-cloud-aai/proWES) is a gateway for
[GA4GH WES][ga4gh-wes] services. It receives workflow requests, applies
middleware (plugins) and forwards each request to one of the WES services
that it knows.

## Role in the deployment

proWES is planned to sit in front of the WES services of the Nodes, as
[proTES](protes.md) does for their TES services.

## Docs

proWES has no separate docs site yet. Use these:

- [README](https://github.com/elixir-cloud-aai/proWES#readme)
- [Helm chart for Kubernetes](https://github.com/elixir-cloud-aai/proWES/tree/dev/deployment)
