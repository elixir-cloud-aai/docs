# Using the Cloud Registry

## Synopsis

The [Cloud Registry][elixir-cloud-registry] lists the services of the ELIXIR
On-Cloud. This page is for its users: operators who look up, register and
maintain services. It states the ELIXIR On-Cloud policies; for how the
registry works in general, it links the [Cloud Registry
documentation][cr-docs]. If you run the registry itself, see [Cloud
Registry](cloud-registry.md).

!!! info "Last checked against Cloud Registry v1.0.0rc2 and Cloud Registry UI v1.0.0-rc2"
    Importing, syncing, the labels and the notifications came with these
    releases. Links to the UI's documentation point to the deployed
    release, 1.0.0-rc2. Links to the Cloud Registry documentation point to
    its latest version, which may be ahead of the deployed release.

For anything this page doesn't answer, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email].

## Looking up services

Anyone can browse the [front end][elixir-cloud-registry] or read the API at
`https://elixir-on.cloud/ga4gh/registry/v1`, without logging in. See
[Browsing][cr-ui-browsing] in the UI's documentation, and the [API
documentation][cr-api].

Two labels describe an entry: whether it is [verified](#verified-services)
and whether it is [synced](#labels). They don't appear in the GA4GH endpoints:
clients read them separately, and match them to the services as described in
[Synced services][cr-synced].

**Verified and synced doesn't mean trusted: you decide whom you trust.**
Clients on the safe side use only services that are both verified and synced.

## Registering a service

**Import from the service info endpoint, and keep sync on: it is the way to
register a service.** First, [prepare your service info](service-info.md),
so that the import passes the rules of this deployment. Then give the
address of the endpoint, check the values that the registry reads from it,
and register them. You need an [LS Login](ls-login.md) account. See
[Importing service info][cr-import] for the details and the limits.

**We strongly recommend that you make your service info endpoint public,** as
it tells people how to get access to your service. The registry can only read
public service info: it never sends a token.

Keep sync on, so that the entry follows your service. Entries without sync can
drift from what the service says.

Scripts use `POST /services/import`, which stores nothing, then `POST /services`
with the returned values, then `PUT /services/<id>/sync` to turn on sync. They
need a token of an LS Login client that the registry accepts: write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email] to have yours added.

The rules of this deployment apply to the service info too: `https`
addresses, the environments `prod` and `test`, and API types that admins have
added. [Prepare your service
info](service-info.md#the-rules-of-this-deployment) shows how to read them
from the registry.

**Enter the values by hand only as a fallback:** for services whose service
info can't be set yet (Funnel, Poiesis and TESP API), isn't public, or for a
quick test with other values. Manual entries have no sync, and can drift. See
[Manual entry, the fallback](service-info.md#manual-entry-the-fallback).

To register a TES service of your Node, follow [Onboarding](onboarding.md).

## Verified services

**Verified means that the registry knows and trusts the original registrators
of the service.** It says nothing about the service as it is now.

**A service without publicly readable service info will never be verified
here,** as drift can't be avoided.

Admins verify services; you can't verify your own. Changing the URL or the API
type of a service removes its verification: ask again after such a change. See
[Verified services][cr-verified].

### What the admins check

The registry leaves the checks to each deployment. Before they verify an entry
of the ELIXIR On-Cloud, the admins check with you, its owner, that:

- **They know you:** you run the service, or act for those who do.
- **The values are right:** the URL, the API type and the organization of the
  entry are those of your service, and the URL starts with `https`.
- **The service is live:** it answers at its URL, and its service info is
  public, with sync on (see above).
- **The service isn't open to anyone:** it accepts requests only from the
  users that the policy of the federation allows, e.g., for a TES service,
  members of the LS Login group `ECP_CLN` (see [Enable LS Login and ECP_CLN
  access](node-onboarding-tutorial.md#3-enable-ls-login-and-ecp_cln-access)),
  and from the gateway.

To ask for verification, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email] with the address of
your entry.

### Who uses the verified entries

- **proTES**, the gateway, when it discovers its TES services in a Cloud
  Registry: it uses verified entries only (see [Get added behind the
  gateway](node-onboarding-tutorial.md#7-get-added-behind-the-gateway)).
  Whether the ELIXIR On-Cloud's proTES discovers its TES services this way,
  or lists them in its configuration, is tracked in
  [generic-issues#31][gi-31].
- **Users**, who check the label before they trust a service. Krini and the
  CLI don't show it: they list verified and unverified services alike (see
  [Krini](../researchers/krini.md) and the [CLI](../researchers/cli.md)).

## Labels

An entry is in one of three states:

| Label | Meaning | What to do |
|---|---|---|
| none | A manual entry, which may have drifted from what the service says. | If you maintain it: make the service info public and turn on sync. |
| `synced` | The registry recently read the service info and applied it. | Nothing. |
| `out-of-sync` | The last sync failed, or none succeeded in time. The entry keeps its last values. | See [below](#out-of-sync-reasons). |

The registry syncs each service regularly; `GET /service-info` of the registry
gives the interval. Owners, maintainers and admins can sync a service at once by
repeating `PUT /services/<id>/sync`, and turn it off with `DELETE`.

While sync is on:

- Sync overrides your changes to the values that come from the service info,
  so change them in the service info. See [Synced services][cr-synced] for which
  values these are.
- The URL of the entry can't change. To move a service, turn sync off first
  (changing the URL removes the verification), or import it anew.

### Out-of-sync reasons

| Reason | What it means | What to do |
|---|---|---|
| `unreachable` | The registry couldn't fetch the service info, also after retries: the service is down, requires a token, redirects, or the response is too large or too slow. | Bring the service back, or make its service info public, without redirects. |
| `address not allowed` | The host resolves to an address that isn't public. The registry reads only public service info. | Publish the service at a public address. |
| `invalid service info` | The service info doesn't pass the checks of a registration, e.g., it has an environment other than `prod` and `test`. | Correct the service info. |
| `identity mismatch` | The service info has another `id` than when sync was turned on, or another API type (`type.group` or `type.artifact`) than the entry. | Take this seriously, and check what your address serves. If a new `id` is right, turn sync off and on again. For another API type, register a new entry. |
| `version awaiting approval` | The API type in the service info is new, and waits for the approval of an admin. The entry stays listed with its old values. | Wait: the next sync after the approval applies it. |
| `version not allowed` | The API type in the service info isn't registered, and only admins may add it. | Ask the [admins][elixir-on-cloud-email] to add it. |
| `unused types limit reached` | The user who registered the service, or the service, if an admin registered it, has added as many unused types as allowed. | Ask the [admins][elixir-on-cloud-email]. |

Which of the three reasons about API types you see depends on who may add
types. This deployment lets only admins add them, so expect `version not
allowed` when you release a new API version: ask for it in time.

`out-of-sync` without a reason means that syncs aren't running, which you can't
fix: tell the [admins][elixir-on-cloud-email].

## Notifications

After you log in, a bell in the front end shows what needs your attention:

- **Users with a role on a service** see when it is out of sync, with the
  reasons above, or `no recent sync` if syncs aren't running.
- **Admins, in admin mode,** also see services and types that wait for approval,
  and services whose environment or URL scheme is no longer allowed.

Nobody gets an email: notifications only appear when you look. Fixing the problem
ends a notification. You can also dismiss it, which dismisses it for everyone
with a role on that service; it comes back if the problem ends and returns, or
its reason changes. See [Notifications][cr-notifications].

## Maintaining a service

- **Roles:** as the one who registers a service, you become its owner, and can
  share it with others. See [Access control][cr-access-control].
- **Your own limit:** you can register up to 20 services; admins aren't limited.
- **Changing what the entry says:** with sync on, change your service info. See
  [Labels](#labels).
- **Admin mode:** in the UI, admins act as admins only in admin mode. See [Admin
  mode][cr-admin-mode].

The [user guide of the UI][cr-ui-user-guide] covers registering, editing and
sharing services step by step; [Using the Cloud Registry
UI](using-cloud-registry-ui.md) adds what applies to this deployment.

[cr-access-control]: <https://cloud-registry.readthedocs.io/en/latest/access-control/>
[cr-admin-mode]: <https://cloud-registry.readthedocs.io/en/latest/access-control/#admin-mode>
[cr-api]: <https://cloud-registry.readthedocs.io/en/latest/api/>
[cr-docs]: <https://cloud-registry.readthedocs.io/en/latest/>
[cr-import]: <https://cloud-registry.readthedocs.io/en/latest/api/#importing-service-info>
[cr-notifications]: <https://cloud-registry.readthedocs.io/en/latest/api/#notifications>
[cr-synced]: <https://cloud-registry.readthedocs.io/en/latest/api/#synced-services>
[cr-ui-browsing]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/browsing/>
[cr-ui-user-guide]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/>
[cr-verified]: <https://cloud-registry.readthedocs.io/en/latest/api/#verified-services>
[gi-31]: <https://github.com/elixir-cloud-aai/generic-issues/issues/31>
