---
last_verified: 2026-11-17
---

# Poiesis

[Poiesis](https://github.com/JaeAeich/poiesis) is a [GA4GH TES][ga4gh-tes]
service for Kubernetes. It runs each task in its own pod.

## Role in the deployment

Poiesis is a TES service for Nodes with a Kubernetes cluster, next to
[TESK](tesk.md). After you deploy it, register it in the [Cloud
Registry][elixir-cloud-registry] (see [Onboarding](../onboarding.md)). End
every upgrade or change of it by updating its entry, which has no sync (see
[After a deployment or an
upgrade](../using-cloud-registry.md#after-a-deployment-or-an-upgrade)).

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
  and HTTP(S) URLs, but not FTP (see [Filer protocols][poiesis-filer] in
  its docs). A
  Node with Poiesis needs an S3 server, e.g., MinIO (see [Deploy
  storage](../onboarding.md#2-deploy-storage)).
- Poiesis validates access tokens of one OIDC issuer, but doesn't check the
  groups of a user yet: the check for the LS Login group `ECP_CLN`, which the
  policy of the federation requires, is tracked in
  [generic-issues#21][gi-21].

## In the ELIXIR On-Cloud

As of November 2026, where and how Poiesis runs may change:

| Node | Address | Status |
|---|---|---|
| Czech Republic (CZ) | <https://poiesis.dyn.cloud.e-infra.cz/> | doesn't answer: its TES API returns the error page "503 Service not available"; not behind the gateway, not in the registry |
| Finland (FI) | none | not part of the deployment yet |

Poiesis joins the TES services of the [gateway](protes.md) once it checks
the groups of LS Login tokens ([generic-issues#21][gi-21]). Find the
current entries in the [Cloud Registry][elixir-cloud-registry].

[poiesis-filer]: <https://poiesis.jaeaeich.com/docs/intro/poiesis.html#filer-protocols>
[gi-21]: <https://github.com/elixir-cloud-aai/generic-issues/issues/21>
