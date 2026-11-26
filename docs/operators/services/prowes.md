---
last_verified: 2026-11-25
---

# proWES

!!! warning "Being revived"
    The [proWES](https://github.com/elixir-cloud-aai/proWES) repository is
    being revived since 2026-11-16, after it had been archived. It has no
    release yet, and the ELIXIR On-Cloud doesn't run it yet. This page
    follows with the revival.

[proWES](https://github.com/elixir-cloud-aai/proWES) is a gateway for
[GA4GH WES][ga4gh-wes] services. It receives workflow requests, applies
middleware (plugins) and forwards each request to one of the WES services
that it knows.

## Role in the deployment

proWES is planned to sit in front of the WES services of the Nodes, as
[proTES](protes.md) does for their TES services.

## Docs

- [proWES docs](https://prowes.readthedocs.io/)
- [Deployment](https://prowes.readthedocs.io/en/latest/deployment/)
- [proWES repository](https://github.com/elixir-cloud-aai/proWES)
