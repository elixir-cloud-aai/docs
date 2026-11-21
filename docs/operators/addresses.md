---
last_verified: 2026-11-21
---

# Central Addresses

The central services of the ELIXIR On-Cloud deployment answer at names
under `elixir-on.cloud`. A name there is only for a central service with a
front end that follows the deployment's design, or for a central endpoint
that others must configure, such as the NVFlare hub. The services of the
Nodes keep their Nodes' addresses: there are no central names for them, and
the only central TES service is the gateway.

As of November 2026:

| Service | Address | What it is | Hosted at | Docs |
|---|---|---|---|---|
| Landing page | <https://elixir-on.cloud/> | The website of the deployment: Nodes, funders and news | BIH | [landing-page repository](https://github.com/elixir-cloud-aai/landing-page) |
| Portal (Krini) | <https://portal.elixir-on.cloud/> | Runs TES tasks in the browser, on services from the Cloud Registry | CSC Rahti | [Use Krini](../researchers/krini.md), [Krini docs](https://krini.readthedocs.io/) |
| Cloud Registry | <https://registry.elixir-on.cloud/> (UI); API at `https://elixir-on.cloud/ga4gh/registry/v1` | The list of the deployment's services ([GA4GH Service Registry][ga4gh-service-registry]) | BIH | [Cloud Registry](cloud-registry.md), [Cloud Registry docs](https://cloud-registry.readthedocs.io/) |
| Documentation Hub | <https://docs.elixir-on.cloud/> | These docs | Read the Docs | [docs repository](https://github.com/elixir-cloud-aai/docs) |
| TES gateway (proTES) | TES API at `https://gateway-tes.elixir-on.cloud/ga4gh/tes/v1` | Forwards TES tasks to the TES services behind it | CSC Rahti | [proTES](services/protes.md), [proTES docs](https://protes.readthedocs.io/) |
| Pubgrade | <https://upgrade.elixir-on.cloud/ui/> (API docs) | Upgrades deployments when new images are published | CSC Rahti | [Pubgrade docs](https://pubgrade.readthedocs.io/) |
| NVFlare hub | `flare-wes.elixir-on.cloud:30002` (the federated learning port, the only one open) | The NVIDIA FLARE server that the sites' clients connect to; the sites get the address in their start kits | CSC Rahti | [NVFlare Testbed](../demos/nvflare-wes-testbed.md), [testbed docs](https://nvflare-wes-testbed.readthedocs.io/) |

The old addresses on CSC Rahti keep working as second names, so that
registry entries, Node configurations and old links don't break:
`protes.rahtiapp.fi` for the TES gateway, `pubgrade.rahtiapp.fi` for
Pubgrade and `krini.rahtiapp.fi` for the portal.

Services without a front end of their own, such as the TES gateway and
Pubgrade, will show a static service page at their address
([foca#812](https://github.com/elixir-cloud-aai/foca/issues/812)); until
then, their hosts serve only their APIs. The WES gateway (proWES), the tool
registry (TRS-Filer) and the data registry (DRS-Filer) get central names
later, after their service pages.
