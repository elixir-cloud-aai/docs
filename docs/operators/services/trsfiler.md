---
last_verified: 2026-11-25
---

# TRS-Filer

[TRS-Filer](https://github.com/elixir-cloud-aai/trs-filer) is a lightweight
implementation of the [GA4GH TRS][ga4gh-trs] API. It serves tools and
workflows.

## Role in the deployment

TRS-Filer is the TRS implementation of the ELIXIR On-Cloud project. Use it
to offer tools and workflows through the TRS API. After you deploy it,
register it in the [Cloud Registry][elixir-cloud-registry], and end every
upgrade or change of it by checking that sync updated its entry (see [After
a deployment or an
upgrade](../using-cloud-registry.md#after-a-deployment-or-an-upgrade)).

## Docs

- [TRS-Filer docs](https://trs-filer.readthedocs.io/)
- [Deployment (Helm chart)](https://trs-filer.readthedocs.io/en/latest/deployment/)
- [Tutorial: Onboard a Data Centre](../data-centre-onboarding-tutorial.md):
  deploy, register and verify TRS-Filer as a data centre of the federation

## In the ELIXIR On-Cloud

As of November 2026:

| What | Value |
|---|---|
| Address | <https://trs-filer.rahtiapp.fi/ga4gh/trs/v2> |
| Version | A development build after the release 0.5.0, with TRS 2.0.2 (0.5.0 reports TRS 2.0.1 and has no authentication); its service info gives the exact version |
| Environment | `test` |
| Reads | public, without a token |
| Writes | with LS Login access tokens, under the same access rules as the [Cloud Registry](../using-cloud-registry.md) |

List its tools and workflows, and read its service info:

```bash
curl -fsS "https://trs-filer.rahtiapp.fi/ga4gh/trs/v2/tools"
curl -fsS "https://trs-filer.rahtiapp.fi/ga4gh/trs/v2/service-info"
```
