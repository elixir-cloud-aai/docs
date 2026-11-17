---
last_verified: null
---

# Services

These are the services that a Node can run in the ELIXIR On-Cloud. Each
page says what the service is, what role it has in the deployment and where
its own docs are. The install steps are in the docs of each service, not
here.

## TES services

Every Node runs one of these in front of its cluster (see
[Onboarding](../onboarding.md)).

| Service | Standard | Runs on |
|---|---|---|
| [TESK](tesk.md) | [GA4GH TES][ga4gh-tes] | Kubernetes, OpenShift |
| [Poiesis](poiesis.md) | [GA4GH TES][ga4gh-tes] | Kubernetes |
| [Funnel](funnel.md) | [GA4GH TES][ga4gh-tes] | HPC or HTC (Slurm, OpenPBS) |

## Other services

| Service | Standard | Role |
|---|---|---|
| [proTES](protes.md) | [GA4GH TES][ga4gh-tes] | Gateway in front of several TES services. |
| [proWES](prowes.md) | [GA4GH WES][ga4gh-wes] | Gateway in front of several WES services. Being revived, not deployed yet. |
| [DRS-Filer](drsfiler.md) | [GA4GH DRS][ga4gh-drs] | Serves data objects. Being revived, not deployed yet. |
| [TRS-Filer](trsfiler.md) | [GA4GH TRS][ga4gh-trs] | Serves tools and workflows. |

Also see the [Cloud Registry](../cloud-registry.md), where services are
registered, and [LS Login](../ls-login.md) for the log in of users. The
registry lists the services that run in the deployment, with their
addresses and the versions of the APIs that they report.

## Deployed services

The services registered in the [Cloud Registry](../cloud-registry.md) for
production use. This table is generated from the registry each time the
docs are built; services for testing are in the registry too.

<!-- registry:services -->

The registry doesn't record how a service is accessed (with a token or
publicly); see the page of each service.
