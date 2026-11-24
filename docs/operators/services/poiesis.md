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

- [Poiesis docs](https://poiesis.jaeaeich.com/), for its default branch
  `dev`: [Deploy](https://poiesis.jaeaeich.com/deploy.html),
  [Quickstart](https://poiesis.jaeaeich.com/docs/start/quickstart.html),
  [Authentication](https://poiesis.jaeaeich.com/docs/concepts/authentication.html)
  and the [Helm values](https://poiesis.jaeaeich.com/docs/reference/helm-values.html).
- The docs of the latest release, 0.2.0, are in its repository:
  [Deploying Poiesis][poiesis-020-deploy] and
  [Authentication][poiesis-020-auth].

## Notes for the deployment

- Poiesis 0.2.0 can't set its service info: it describes the project, not
  your Node. Register it by hand (see [Manual entry, the
  fallback](../service-info.md#manual-entry-the-fallback)). The default
  branch sets it with the Helm values `serviceInfo.*`
  ([JaeAeich/poiesis#112](https://github.com/JaeAeich/poiesis/issues/112)).

- Poiesis reads the inputs of tasks from, and writes their outputs to, S3
  and HTTP(S) URLs; 0.2.0 doesn't support FTP, while the default branch
  also supports FTP(S) (see [Storage
  protocols][poiesis-storage] in its docs). A deployment lists the
  protocols it supports in the field `storage` of its service info. A
  Node with Poiesis needs an S3 server, e.g., MinIO (see [Deploy
  storage](../onboarding.md#2-deploy-storage)).
- Poiesis validates access tokens of OIDC issuers: 0.2.0 of one, under
  `auth.oidc.*`, without checking the groups of a user. The default branch
  takes several issuers (`auth.issuers[]`), each with a rule for a claim
  such as the groups (`requiredClaim`), and can ask a decision service
  (OpenID AuthZEN, `authz.decisionService.*`), such as tes-authz. The check
  for the LS Login group `ECP_CLN:EOC-Compute`, which the policy of the
  federation requires, is tracked in [generic-issues#21][gi-21]: since
  21 November 2026, the FI Poiesis checks the groups of LS Login tokens
  through tes-authz.

## In the ELIXIR On-Cloud

As of 24 November 2026, where and how Poiesis runs may change:

| Node | TES API | Status |
|---|---|---|
| Czech Republic (CZ), at CERIT-SC | `https://poiesis.dyn.cloud.e-infra.cz/ga4gh/tes/v1` | answers: service info with the ID `cz.e-infra.cloud.dyn.poiesis`, environment `test`; tasks only with an access token; not behind the gateway, not in the registry yet |
| Finland (FI), on Rahti at CSC | `https://poiesis.rahtiapp.fi/ga4gh/tes/v1` | answers: the project's default service info (ID `org.ga4gh.poiesis`); tasks only with an access token; not behind the gateway, not in the registry |

Poiesis joins the TES services of the [gateway](protes.md) once
[generic-issues#21][gi-21] is done. Find the
current entries in the [Cloud Registry][elixir-cloud-registry].

[poiesis-020-auth]: <https://github.com/JaeAeich/poiesis/blob/v0.2.0/docs/app/docs/deploy/authentication.md>
[poiesis-020-deploy]: <https://github.com/JaeAeich/poiesis/blob/v0.2.0/docs/app/docs/deploy/deploying-poiesis.md>
[poiesis-storage]: <https://poiesis.jaeaeich.com/docs/start/what-is-poiesis.html#storage-protocols>
[gi-21]: <https://github.com/elixir-cloud-aai/generic-issues/issues/21>
