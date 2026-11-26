---
last_verified: null
---

# WESkit

[WESkit](https://gitlab.com/one-touch-pipeline/weskit/api) is a [GA4GH
WES][ga4gh-wes] service. It runs Snakemake and Nextflow workflows on its
host or on a cluster, such as Slurm or LSF, and logs users in with OpenID
Connect, e.g., LS Login.

## Role in the deployment

WESkit is a WES service for Nodes that offer workflow runs, not only
tasks. It is the workflow service of SPE4HD, the secure processing
environment (SPE) of ELIXIR Compute WP3, at the Berlin Institute of Health
at Charité (see [WESkit at BIH](#weskit-at-bih) below). After you deploy
it, register it in the [Cloud Registry][elixir-cloud-registry] with a WES
type (see [Onboarding](../onboarding.md)). End every upgrade or change of
it by checking that sync updated its entry (see [After a deployment or an
upgrade](../using-cloud-registry.md#after-a-deployment-or-an-upgrade)).

The ELIXIR On-Cloud has no WES gateway yet ([proWES](prowes.md) is being
revived), so users send their runs to each WES service directly.

## Docs

- [WESkit docs](https://gitlab.com/one-touch-pipeline/weskit/documentation)
- [Admin guide](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/README.md),
  with [Configuration](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/configuration.md)
  and [Authentication](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/login.md)
- [SPE4HD](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/spe4hd.md):
  how to set up an SPE like the one at BIH
- [Deployment repository](https://gitlab.com/one-touch-pipeline/weskit/deployment),
  with the template of the config file, `weskit_config/config.yaml`

## Notes for the deployment

These notes are for WESkit 1.0.0 and the config template of its deployment
repository.

### Service info

WESkit serves its service info at `<host>/ga4gh/wes/v1/service-info`, also
with login on, as the registry needs. It takes most fields from
`static_service_info` in its config file. The template's values describe
no deployment, and some of them fail the import of the registry. Set these
fields (see the [checklist](../service-info.md#checklist)):

| Field | Template or default | Set it to | Why |
|---|---|---|---|
| `id` | `org.weskit.service` | your host in reverse domain notation, e.g., `org.example.weskit` | The same for every deployment that keeps it; sync pins it. |
| `name` | `WESkit` | keep it | We recommend the name of the implementation only: no host, country, "test" or cluster names, which other fields say (see [Names and organizations](../service-info.md#names-and-organizations)). |
| `description` | empty | what the service offers, to whom, and which data it may hold | Users choose services by it. |
| `organization` | `Organization`, `https://example.org` | the name and URL of the institution that hosts the service, as it writes them, e.g., `My University`, `https://example.org/` | The registry lists the host of each service. |
| `type` | `org.ga4gh`, `wes`, `1.1.0` | keep it | The registry's types are a controlled, case-sensitive vocabulary. WESkit implements WES 1.1.0. |
| `version` | `dev-4.1.0` | the WESkit version that you run, e.g., `1.0.0` | Change it with every upgrade, so that sync shows it. |
| `environment` | `unknown` (not in the template) | `prod` or `test` | The registry refuses other values. |
| `contact_url` | `mailto:your@email.de` | your support address, e.g., `mailto:wes@example.org` | Shown in the registry and clients. |
| `documentation_url` | WESkit's wiki | the page for the users of your instance | It should say how to get access. |
| `auth_instructions_url` | `https://somewhere.org` | the page that says how to get an access token | A field of WES; clients show it. |

WESkit takes `supported_wes_versions`, `workflow_type_versions` and the
engine parameters from its code and config, not from
`static_service_info`. The registry ignores `createdAt`, `updatedAt` and
`tags`.

Then check the endpoint as in [Check before you
import](../service-info.md#check-before-you-import), with the base URL of
WESkit, e.g., `https://wes.example.org/ga4gh/wes/v1`. If a web portal
redirects the old address of your instance to a new one, register the new
one: the import follows no redirects.

### Login

Set `login.enabled: true` and the `jwt` options of the config file as in
[Authentication](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/login.md),
with the issuer and keys of LS Login and your service's client (see [LS
Login](../ls-login.md)). WESkit then requires a token for every endpoint of
runs, and shows each user only their own runs. It checks the token's
signature, issuer and audience, not the user's groups: who may use your
instance is up to how you register and run it at LS Login.

## WESkit at BIH

!!! warning "Being set up"
    This instance is being prepared as a service of the ELIXIR On-Cloud.
    Its access process isn't documented yet. Until then, write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email].

The Berlin Institute of Health at Charité (BIH) runs WESkit as the
workflow service of SPE4HD, the reference SPE of ELIXIR Compute WP3
(milestone M3.5). Its web portal offers demo workflows on simulated data.

| | |
|---|---|
| Name | WESkit |
| Host organization | Berlin Institute of Health at Charité (BIH) |
| Address | [weskit.bihealth.org](https://weskit.bihealth.org/), the web portal; the WES API is at `/ga4gh/wes/v1` on the same host. `spe4hd.weskit.bihealth.org` redirects to it. |
| Login | LS Login |
| Data | Simulated data only: the portal says "Do not upload real or personal data". |
| Access | Not documented yet (see above). |
| Registry | Among the [deployed services](index.md#deployed-services); as of 26 November 2026, its entry has the name and organization of its service info. |
