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

## Notes for the deployment

- Poiesis's service info can't be set yet
  ([JaeAeich/poiesis#112](https://github.com/JaeAeich/poiesis/issues/112)):
  it describes the project, not your Node. Register it by hand (see [Manual
  entry, the fallback](../service-info.md#manual-entry-the-fallback)).

- Poiesis reads the inputs of tasks from, and writes their outputs to, S3
  and HTTP(S) URLs, but not FTP (see [Usage][poiesis-usage] in its docs). A
  Node with Poiesis needs an S3 server, e.g., MinIO (see [Deploy
  storage](../onboarding.md#2-deploy-storage)).
- Poiesis validates access tokens of one OIDC issuer, but doesn't check the
  groups of a user yet: the check for the LS Login group `ECP_CLN`, which the
  policy of the federation requires, is tracked in
  [generic-issues#21][gi-21].

!!! warning "Under construction"
    Which Nodes of the ELIXIR On-Cloud run Poiesis is recorded with the
    configuration of the gateway, in [generic-issues#31][gi-31].

[poiesis-usage]: <https://poiesis.jaeaeich.com/docs/usage/usage.html>
[gi-21]: <https://github.com/elixir-cloud-aai/generic-issues/issues/21>
[gi-31]: <https://github.com/elixir-cloud-aai/generic-issues/issues/31>
