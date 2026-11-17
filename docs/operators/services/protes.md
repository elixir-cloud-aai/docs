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
(see below).

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
| Address | <https://protes.rahtiapp.fi/>, TES API at `/ga4gh/tes/v1` |
| Version | proTES 0.6.0 |
| Access | LS Login access tokens of members of the group `ECP_CLN:EOC-Compute`, issued to a client that it accepts, such as Krini's (see [Researchers](../../researchers/index.md#before-you-start)) |
| TES services | the TESK of the Finnish Node, listed in its configuration |
| Discovery in the Cloud Registry | off |

A Node's TES service is added to the configuration when its admins ask for
it and the service requires LS Login tokens (see [Get added behind the
gateway](../node-onboarding-tutorial.md#7-get-added-behind-the-gateway)).
The service info of proTES (`GET /ga4gh/tes/v1/service-info`) lists the TES
services that it uses. The rest of its configuration, such as its plugins
and how it authenticates at its TES services, is tracked in
[generic-issues#31][gi-31].

[gi-31]: <https://github.com/elixir-cloud-aai/generic-issues/issues/31>
