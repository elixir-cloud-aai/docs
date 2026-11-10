# Using the Cloud Registry UI

## Synopsis

The [Cloud Registry UI][cr-ui-repo] is the front end of the ELIXIR On-Cloud
[Cloud Registry][elixir-cloud-registry], at
<https://registry.elixir-on.cloud/>. This page says what is specific to this
deployment: how you log in, who has which rights, and whom to ask. For how
the UI works, see its [user guide][cr-ui-user-guide]; for the policies of the
registry (verification, labels, sync), see [Using the
Cloud Registry](using-cloud-registry.md).

For anything this page doesn't answer, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email].

## Overview

| What | Value |
|---|---|
| Front end | <https://registry.elixir-on.cloud/> |
| API base URL | <https://elixir-on.cloud/ga4gh/registry/v1> |
| Login provider | [LS Login][ls-login], the only one |
| Admins | members of the LS Login group `ECP_CLN:ADMIN`, in admin mode |
| Help | [cloud-service@elixir-europe.org][elixir-on-cloud-email] |

## Browsing without logging in

Anyone can browse the services and service types without logging in. See
[Browsing and searching][cr-ui-browsing].

## Logging in

To register services and manage your own, log in with
[LS Login][ls-login]: select **Log in** in the top bar, then LS Login. This
deployment offers no other login provider. You need an LS Login account:
to get one, see the [LS Login and registration guide][ls-login-guide]. See
[Logging in][cr-ui-logging-in] for sessions and logging out.

Owners share services with others by their user ID, which the UI shows in
the menu at the bottom of the sidebar (see [Your user ID][cr-ui-user-id]).

## Rights

| Who | Can |
|---|---|
| Anyone | browse services and service types |
| Logged-in users | register up to 20 services; only admins add service types here |
| Maintainers of a service | edit it |
| Owners of a service | edit and delete it, and manage access to it (see [Access and permissions][cr-ui-access]) |
| Admins, in admin mode | everything, e.g. verify services and approve service types (see [Admin mode][cr-ui-admin-mode]) |

Roles on a service come from its owners: as the one who registers a
service, you become its owner, and can give other users or groups a role on
it. To get a role on a service that someone else registered, ask its
owners.

The only group that grants rights across the registry is the LS Login group
`ECP_CLN:ADMIN`: its members are the admins. Admins start in user mode, and
act as admins only after switching to admin mode in the top bar. To ask about
admin rights, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email].

## Getting help

- **Questions about this deployment,** e.g. rights, service types to add, or
  services that stay out of sync: write to
  [cloud-service@elixir-europe.org][elixir-on-cloud-email].
- **Problems with LS Login itself,** e.g. your account: see the [LS
  Login][ls-login] pages.
- **Bugs in the UI:** open an issue in the [Cloud Registry UI
  repository][cr-ui-repo].

[cr-ui-access]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/access/>
[cr-ui-admin-mode]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/admin-mode/>
[cr-ui-browsing]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/browsing/>
[cr-ui-logging-in]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/#logging-in>
[cr-ui-repo]: <https://github.com/elixir-cloud-aai/cloud-registry-ui>
[cr-ui-user-guide]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/>
[cr-ui-user-id]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/#your-user-id>
[ls-login]: <https://www.lifescience-ri.eu/life-science-login/>
[ls-login-guide]: <https://www.lifescience-ri.eu/ls-login-and-registration-guide/>
