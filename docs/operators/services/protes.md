---
last_verified: 2026-11-18
---

# proTES

[proTES](https://github.com/elixir-cloud-aai/proTES) is a gateway for
[GA4GH TES][ga4gh-tes] services. It receives task requests, applies
middleware (plugins) and forwards each task to one of the TES services that
it knows.

## Role in the deployment

proTES sits in front of the Nodes' TES services: clients send their tasks
to proTES, and proTES distributes them to the Nodes. It can read
the verified TES services of a [Cloud Registry][elixir-cloud-registry], so
that a new Node is used once it is registered and verified; the ELIXIR
On-Cloud's proTES lists its TES services in its configuration instead
(see below). Register a proTES that you deploy in the Cloud Registry like
any other TES service, and end every upgrade or change of it by updating
its entry, or checking that sync did (see [After a deployment or an
upgrade](../using-cloud-registry.md#after-a-deployment-or-an-upgrade)).

## Docs

- [proTES docs](https://protes.readthedocs.io/)
- [Deployment (Helm chart)](https://protes.readthedocs.io/en/latest/deployment/)
- [Configuration, including the discovery of TES services in a Cloud
  Registry](https://protes.readthedocs.io/en/latest/configuration/)
- [Plugins](https://protes.readthedocs.io/en/latest/plugins/)

## In the ELIXIR On-Cloud

As of November 2026:

| What | Value |
|---|---|
| Address | TES API at `https://gateway-tes.elixir-on.cloud/ga4gh/tes/v1` (the host itself has no page); the old address `protes.rahtiapp.fi` keeps working |
| Version | proTES 0.6.0 |
| Access | LS Login access tokens of members of the group `ECP_CLN:EOC-Compute`, issued to a client that it accepts, such as Krini's (see [Researchers](../../researchers/index.md#before-you-start)). Members of `ECP_CLN:ADMIN` can't create tasks: admins who run tasks join `ECP_CLN:EOC-Compute` (see the role `admin` below) |
| LS Login client | client ID `7c0c1fc0-e8ca-47d6-a9b2-bdc843961146`, issuer `https://login.aai.lifescience-ri.eu/oidc/`: a TES service behind proTES lists this client ID and accepts it as audience (see [Access control for compute](../policies.md#access-control-for-compute)) |
| Environment | `test`; its service info calls it "ELIXIR On-Cloud TES Gateway" |
| TES services | listed in its configuration and in the `backends` of its service info: the TESK of the FI Node, at CSC (`https://tesk.rahtiapp.fi`), and the TESK of the CZ Node, at CERIT-SC (`https://tesk.dyn.cloud.e-infra.cz`); proTES calls both with an LS Login token of its own client since 26 November 2026 ([generic-issues#111][gi-111]) |
| Discovery in the Cloud Registry | off |

A Node's TES service is added to the configuration when its admins ask for
it and the service requires LS Login tokens (see [Get added behind the
gateway](../node-onboarding-tutorial.md#7-get-added-behind-the-gateway)).
The service info of proTES (`GET /ga4gh/tes/v1/service-info`) lists the TES
services that it uses.

### Configuration

The effective configuration of the ELIXIR On-Cloud's proTES, as of
18 November 2026, of 25 November 2026 for the role `admin`, and of
26 November 2026 for its TES services (see
[Access control in the proTES docs](https://protes.readthedocs.io/en/v0.6.0/access-control/) for what the
roles may do):

| Setting | Value |
|---|---|
| Deployment | Helm chart `protes-0.6.0.tgz` of the [v0.6.0 release](https://github.com/elixir-cloud-aai/proTES/releases/tag/v0.6.0) on CSC's Rahti, image `elixircloud/protes:0.6.0` pinned by digest, with MongoDB 7.0 and RabbitMQ 4.3 from the chart |
| Token issuer | LS Login only: `https://login.aai.lifescience-ri.eu/oidc/` |
| Audience | the LS Login clients of Krini and of the Cloud Registry UI |
| Groups | read from LS Login's userinfo endpoint, claim `eduperson_entitlement` |
| Role `user` | `urn:geant:lifescience-ri.eu:group:elixir:ECP_CLN:EOC-Compute#aai.lifescience-ri.eu`: create tasks, list their own, list and read the plugins |
| Role `admin` | `urn:geant:lifescience-ri.eu:group:elixir:ECP_CLN:ADMIN#aai.lifescience-ri.eu`: the permissions API (`/admin/access-control/permissions`, on the public address) and the provenance of all tasks. Since 25 November 2026, no added rule gives it the rights of `user`: only members of `ECP_CLN:EOC-Compute` may create tasks (see [Access control for compute](../policies.md#access-control-for-compute)), so admins who run tasks join `ECP_CLN:EOC-Compute` |
| Other tokens | valid tokens without either group get `403 Forbidden` on tasks and plugins; the service info is public |
| Own tasks | only the user who created a task can read and cancel it; admins can read the provenance of any task, not the task |
| TES services | since 26 November 2026: the TESK of the FI Node at `https://tesk.rahtiapp.fi` and the TESK of the CZ Node at `https://tesk.dyn.cloud.e-infra.cz`, both with `auth: client_credentials` (a token of proTES' own LS Login client, client ID above) |
| Plugins | none configured (the service info lists no capabilities) |

LS Login releases only the groups assigned to the client's facility, so a
new client that should reach proTES needs `ECP_CLN:EOC-Compute` (and
`ECP_CLN:ADMIN`, for the role `admin`) assigned to its facility and its
client ID added to the audience (see [LS Login](../ls-login.md)).

The mapping matches the subgroup values, not the parent group `ECP_CLN`:
members of a subgroup carry the parent value only if the parent group is
assigned to the facility of the token's client, too
([generic-issues#46][gi-46]). Members of other `ECP_CLN` subgroups get no
role.

proTES has an LS Login client of its own (client ID above). Since
26 November 2026, it sends a token of that client (OAuth 2.0 client
credentials) to both TESKs, which require LS Login tokens
([generic-issues#111][gi-111], [generic-issues#138][gi-138]).

[gi-138]: <https://github.com/elixir-cloud-aai/generic-issues/issues/138>

[gi-46]: <https://github.com/elixir-cloud-aai/generic-issues/issues/46>
[gi-111]: <https://github.com/elixir-cloud-aai/generic-issues/issues/111>
