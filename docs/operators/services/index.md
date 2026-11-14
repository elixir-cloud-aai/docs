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
| [CWL-WES](cwlwes.md) | [GA4GH WES][ga4gh-wes] | Runs CWL workflows on a TES service. |
| [proWES](prowes.md) | [GA4GH WES][ga4gh-wes] | Gateway in front of several WES services. |
| [DRS-Filer](drsfiler.md) | [GA4GH DRS][ga4gh-drs] | Serves data objects. |
| [TRS-Filer](trsfiler.md) | [GA4GH TRS][ga4gh-trs] | Serves tools and workflows. |

Also see the [Cloud Registry](../cloud-registry.md), where services are
registered, and [LS Login](../ls-login.md) for the log in of users.
