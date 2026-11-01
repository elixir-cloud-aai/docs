# proTES

[proTES](https://github.com/elixir-cloud-aai/proTES) is a gateway for
[GA4GH TES][ga4gh-tes] services. It receives task requests, applies
middleware (plugins) and forwards each task to one of the TES services that
it knows.

## Role in the deployment

proTES sits in front of the Nodes' TES services: clients send their tasks
to proTES, and proTES distributes them to the Nodes. It can read
the verified TES services of a [Cloud Registry][elixir-cloud-registry], so
that a new Node is used once it is registered and verified.

## Docs

- [proTES docs](https://protes.readthedocs.io/)
- [Deployment (Helm chart)](https://protes.readthedocs.io/en/latest/deployment/)
- [Configuration, including the discovery of TES services in a Cloud
  Registry](https://protes.readthedocs.io/en/latest/configuration/)
- [Plugins](https://protes.readthedocs.io/en/latest/plugins/)

!!! warning "Under construction"
    The address of the ELIXIR On-Cloud's proTES, its plugins and the
    registry that it reads are not documented yet.
