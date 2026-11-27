---
last_verified: 2026-11-26
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
  Node with Poiesis needs an S3 server, for example, MinIO (see [Deploy
  storage](../onboarding.md#2-deploy-storage)).
- Poiesis validates access tokens of OIDC issuers: 0.2.0 of one, under
  `auth.oidc.*`, without checking the groups of a user. The default branch
  takes several issuers (`auth.issuers[]`), each with a rule for a claim
  such as the groups (`requiredClaim`), and can ask a decision service
  (OpenID AuthZEN, `authz.decisionService.*`), such as tes-authz. The
  policy of the federation lets only members of the LS Login group
  `ECP_CLN:EOC-Compute` run jobs: list that group alone in the rule. The
  check on our deployments is tracked in [generic-issues#21][gi-21].
- The default branch can also issue API keys (`poi_…`) for clients that
  can't refresh access tokens (`auth.apiKeys.*`; the issuer's
  `keyMinting` lists the clients whose tokens may mint them). A key
  carries its owner's claims as of minting, until it expires (see [API
  keys][poiesis-api-keys] in its docs). We use them for smoke tests.
- We recommend `name: Poiesis` and the organization that hosts the
  service, for example, `CSC – IT Center for Science` (see [Names and
  organizations](../service-info.md#names-and-organizations)).

## In the ELIXIR On-Cloud

As of 26 November 2026, where and how Poiesis runs may change:

| Node | TES API | Status |
|---|---|---|
| Czech Republic (CZ), at CERIT-SC | `https://poiesis.dyn.cloud.e-infra.cz/ga4gh/tes/v1` | default branch; service info with the ID `cz.e-infra.cloud.dyn.poiesis`, environment `test`; jobs only with an access token; not behind the gateway, not in the registry yet |
| Finland (FI), on Rahti at CSC | `https://poiesis.rahtiapp.fi/ga4gh/tes/v1` | default branch at `fc72419` since 26 November 2026; service info with the ID `fi.rahtiapp.poiesis`, name `Poiesis`, organization `CSC – IT Center for Science`, environment `test`; LS Login tokens of `ECP_CLN:EOC-Compute` members only, checked through tes-authz; API keys on; not behind the gateway, not in the registry yet |

Poiesis joins the TES services of the [gateway](protes.md) once
[generic-issues#21][gi-21] is done. Find the
current entries in the [Cloud Registry][elixir-cloud-registry].

[poiesis-020-auth]: <https://github.com/JaeAeich/poiesis/blob/v0.2.0/docs/app/docs/deploy/authentication.md>
[poiesis-020-deploy]: <https://github.com/JaeAeich/poiesis/blob/v0.2.0/docs/app/docs/deploy/deploying-poiesis.md>
[poiesis-api-keys]: <https://poiesis.jaeaeich.com/docs/concepts/api-keys.html>
[poiesis-storage]: <https://poiesis.jaeaeich.com/docs/start/what-is-poiesis.html#storage-protocols>
[gi-21]: <https://github.com/elixir-cloud-aai/generic-issues/issues/21>
