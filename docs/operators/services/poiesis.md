# Poiesis

[Poiesis](https://github.com/JaeAeich/poiesis) is a [GA4GH TES][ga4gh-tes]
service for Kubernetes. It runs each task in its own pod.

## Role in the deployment

Poiesis is a TES service for Nodes with a Kubernetes cluster, next to
[TESK](tesk.md). After you deploy it, register it in the [Cloud
Registry][elixir-cloud-registry] (see [Onboarding](../onboarding.md)).

## Docs

- [Poiesis docs](https://poiesis.jaeaeich.com/)
- [Deploying Poiesis](https://poiesis.jaeaeich.com/docs/deploy/deploying-poiesis.html)
- [Authentication](https://poiesis.jaeaeich.com/docs/deploy/authentication.html)

!!! warning "Under construction"
    It is not documented yet how Poiesis is used in the ELIXIR On-Cloud
    (for example, which Nodes run it, and with which storage).
