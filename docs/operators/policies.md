---
last_verified: null
---

# Policies and Requirements

## Synopsis

This page collects what the operator of a service in the ELIXIR On-Cloud
must and should do: how users log in, who may run tasks, how services are
registered and described, how they are secured and upgraded, which data
they may hold, and whom to contact. **Must** marks a requirement, **should**
a recommendation. Each section links to the page with the details and the
steps.

The requirements apply to every service that a Node runs in the
federation: TES and WES services of compute Nodes, and the storage and TRS
services of data centres (see [Who can join](index.md#who-can-join)).
Requirements specific to data nodes, e.g., for DRS services, are not
written down yet.

--8<-- "includes/scope.md"

## Authentication

- Your service **must** require [LS Login](ls-login.md) access tokens for
  every endpoint except `GET /service-info`: no anonymous access. The
  issuer of LS Login is `https://login.aai.lifescience-ri.eu/oidc/`.
- `GET /service-info` **must** stay public: it answers without a token
  (see [Prepare Your Service Info](service-info.md#checklist)).
- Register **one LS Login client for each service**, keep its client
  secret in a secret store, never in a repository, and move it to the
  production environment of LS Login in time (see [Register your
  service](ls-login.md#register-your-service) and [Test and
  production](ls-login.md#test-and-production)). The LS Login [Terms of
  Use for Service Providers][ls-login-terms] apply to your service.

## Access control for compute

These rules apply to the TES and WES services of a Node. This page says
"tasks" for both: the tasks of a TES service and the runs of a WES
service.

- **Only members of the LS Login group `elixir:ECP_CLN:EOC-Compute` may
  create tasks.** LS Login releases the membership as the
  `eduperson_entitlement` value
  `urn:geant:lifescience-ri.eu:group:elixir:ECP_CLN:EOC-Compute#aai.lifescience-ri.eu`.
  The group is required only to create tasks. The parent group `ECP_CLN`
  grants nothing. A token without the group gets `403 Forbidden` when it
  creates a task. Researchers apply for the group as described in [Compute
  access](ls-login.md#compute-access).
- **The creator of a task is its sole owner**, identified by the issuer
  and the subject of the token. The owner may use all other operations on
  their own tasks (get, list, cancel), also after their membership in the
  group was revoked.
- **Listing tasks shows only the caller's own tasks.** There is no admin
  view of other users' tasks, not even a list.
- **Service clients**, such as the [gateway](services/protes.md): your
  service recognises a service client by the issuer and its `client_id`,
  from an explicit allow list, and accepts as audience (`aud`) that
  client's own client ID. A listed client stands in for the
  `EOC-Compute` group when it creates tasks and, as their creator, owns
  them: it may get, list and cancel its own tasks, and nothing beyond, no
  other users' tasks and no admin rights. The client ID of the gateway
  is on its [service page](services/protes.md#in-the-elixir-on-cloud);
  ask the [admins][elixir-on-cloud-email] for any other client IDs to
  list (see [Get added behind the
  gateway](node-onboarding-tutorial.md#7-get-added-behind-the-gateway)).

How far each TES product can enforce these rules today, and how to
configure it, is in [Enable LS Login and ECP_CLN
access](node-onboarding-tutorial.md#3-enable-ls-login-and-ecp_cln-access)
of the Node tutorial. Ask the [admins][elixir-on-cloud-email] before you
join with a product that can't enforce them.

## Registry entry

- Register each GA4GH API service that your Node offers to the federation,
  e.g., TES, WES or TRS services, in the [Cloud
  Registry][elixir-cloud-registry]. The registry lists GA4GH API services,
  not infrastructure such as [Pubgrade][pubgrade] or its sidecars.
- **Register by importing the service's service info, and keep sync on**,
  so that the entry follows your service. Enter the values by hand only as
  the [fallback](service-info.md#manual-entry-the-fallback). See [Using
  the Cloud Registry](using-cloud-registry.md#registering-a-service).
- **The entry is yours.** Whoever registers a service owns its entry and
  is responsible for it: keeping it correct, and correcting it. The admins
  don't edit other operators' entries.
- **End every upgrade, move or change of your service by updating its
  entry, or by checking that sync did** (see [After a deployment or an
  upgrade](using-cloud-registry.md#after-a-deployment-or-an-upgrade)).
- Ask the [admins][elixir-on-cloud-email] to verify your entry, and again
  after you changed its URL or API type, which removes the verification.
  What they check is in [What the admins
  check](using-cloud-registry.md#what-the-admins-check).

## Service info

Your service's `GET /service-info` describes it to the registry and to
users. It **must** follow the base `Service` model of the [GA4GH service
info specification][ga4gh-service-info]: the import of the registry needs
`id`, `name`, `type`, `organization` and `version`. It also **must** pass
the rules of this deployment, which the registry publishes in its own
service info (see [The rules of this
deployment](service-info.md#the-rules-of-this-deployment)). In short:

- the endpoint answers without a token, without redirects, at an `https`
  URL with a valid certificate and public addresses only;
- `id` is unique and stable, in reverse domain notation, not the default
  of your product;
- `organization` names your Node, not the product's project;
- `environment` is `prod` for a production service or `test` for a test
  service;
- `type` is one of the registered types, exactly as registered: types are
  compared as written;
- `contactUrl` says where users get support.

Go through the [checklist](service-info.md#checklist) before you register,
and see [Setting it per product](service-info.md#setting-it-per-product)
for products whose service info can't be set yet.

## Addresses and TLS

- Your services **must** answer at `https` URLs with a valid certificate
  for the host: the Cloud Registry accepts `https` URLs only.
- The services of a Node keep the Node's addresses: names under
  `elixir-on.cloud` are for central services only (see [Central
  Addresses](addresses.md)).
- An FTP server for the files of tasks **must** require FTP over TLS
  (FTPS; see [vsftpd (FTP)](onboarding.md#vsftpd-ftp)).

## Security

- Keep secrets, such as client secrets and storage credentials, out of
  repositories and out of values files that you commit: pass them at
  deploy time, e.g., from a secret store (see [LS Login](ls-login.md)).
- Before you install a release, you **should** check that its release
  workflow built and signed it, as the tutorials show for the charts of
  TESK and TRS-Filer (see [Install TESK](node-onboarding-tutorial.md#install-tesk)
  and [Download and check the
  chart](data-centre-onboarding-tutorial.md#download-and-check-the-chart)).
- You **should** scan the images of your services for known
  vulnerabilities, and upgrade when a scan finds a critical or high
  vulnerability that a fix exists for.
- Everyone who may create tasks on a TES service can run any image with
  any command on your cluster: read the security notes in the docs of your
  product, e.g., the [security implications][tesk-api-claim-security] of
  tesk-api.
- A TRS-Filer without authentication **must** allow writes (`POST`, `PUT`,
  `DELETE`) only from trusted clients (see [Restrict
  writes](data-centre-onboarding-tutorial.md#restrict-writes)).
- Report security problems of ELIXIR On-Cloud software privately, as its
  [security policy][security-policy] describes, not in public issues.

## Upgrades

- Upgrade your services with the upgrade notes of each product, e.g., those
  of [TESK][tesk-upgrading], and end each upgrade with the [registry
  step](#registry-entry) above.
- **Optional:** [Pubgrade-Sidecar][sidecar-docs] rolls out new releases of
  a service when the central Pubgrade notifies it. Install it as described
  in [Automatic upgrades with
  Pubgrade-Sidecar](node-onboarding-tutorial.md#8-optional-automatic-upgrades-with-pubgrade-sidecar),
  and ask the [admins][elixir-on-cloud-email] to subscribe it.

## Data

- **The ELIXIR On-Cloud is a sandbox for demos and tests with synthetic or
  public data, not for personal or other sensitive data.** This applies to
  the tasks, inputs, outputs, tools and workflows that your services hold
  for the federation.
- For the background of working with sensitive data, i.e., legal
  frameworks, Secure Processing Environments (SPEs) and the ways to reach
  data, see [Sensitive Data](../partners-and-developers/sensitive-data.md).
  For analyses of encrypted files through the gateway, see [Crypt4GH with
  proTES](../researchers/crypt4gh-with-protes.md).

## Support and contact

- Write to the admins at [cloud-service@elixir-europe.org][elixir-on-cloud-email]
  before you start, and tell them about each new service: they answer your
  questions and verify your entry.
- When you join, you **should** give the admins a security contact: an
  e-mail address at which they can reach you about security problems of
  your services.
- Give your users a place to get support: the `contactUrl` of your service
  info.
- Ask questions in the [Q&A forum][elixir-on-cloud-forum].

## Onboarding steps

1. Read this page, and write to the [admins][elixir-on-cloud-email],
   with a security contact.
2. Follow [Onboarding](onboarding.md), or step by step [Tutorial: Onboard a
   Node](node-onboarding-tutorial.md) for compute and [Tutorial: Onboard a
   Data Centre](data-centre-onboarding-tutorial.md) for storage, tools and
   workflows.
3. Set up authentication and access control as [above](#authentication).
4. [Prepare the service info](service-info.md), register the service by
   import with sync on, and ask for verification.
5. To join the gateway, agree with the admins how it authenticates at your
   service (see [Get added behind the
   gateway](node-onboarding-tutorial.md#7-get-added-behind-the-gateway)).
6. Keep the service and its registry entry up to date.

[ga4gh-service-info]: <https://github.com/ga4gh-discovery/ga4gh-service-info>
[ls-login-terms]: <https://www.lifescience-ri.eu/terms-of-use-for-service-providers/>
[pubgrade]: <https://github.com/elixir-cloud-aai/Pubgrade>
[security-policy]: <https://github.com/elixir-cloud-aai/.github/blob/main/SECURITY.md>
[sidecar-docs]: <https://pubgrade.readthedocs.io/en/latest/sidecar/>
[tesk-api-claim-security]: <https://tesk.readthedocs.io/en/latest/tesk-api/access-control/#security-implications>
[tesk-upgrading]: <https://tesk.readthedocs.io/en/latest/upgrading/>
