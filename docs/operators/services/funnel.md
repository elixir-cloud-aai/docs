# Funnel

[Funnel](https://github.com/calypr/funnel) is a [GA4GH TES][ga4gh-tes]
service. It runs tasks on a cluster through a backend, such as Slurm.

## Role in the deployment

Funnel is the TES service for Nodes with an HPC or HTC cluster. After you
deploy it, register it in the [Cloud Registry][elixir-cloud-registry] (see
[Onboarding](../onboarding.md)).

## Docs

- [Funnel docs](https://calypr.org/tools/funnel)
- [Funnel repository](https://github.com/calypr/funnel)

## Notes for the deployment

- The ELIXIR On-Cloud documents Funnel with Slurm only. For other
  backends, see the Funnel docs.
- Place the `funnel` binary on a server that has access to Slurm.
- Put the config file on the same server. [This file][funnel-config-slurm]
  is a starting point.
- If everything works, Funnel listens on port `8080`.
- Funnel's service info can't be set yet
  ([calypr/funnel#1493](https://github.com/calypr/funnel/issues/1493)), and
  this deployment refuses its environment, `development`: register it by
  hand (see [Manual entry, the
  fallback](../service-info.md#manual-entry-the-fallback)).
