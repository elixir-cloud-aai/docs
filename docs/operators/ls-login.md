---
last_verified: null
---

# LS Login

[LS Login](https://lifescience-ri.eu/ls-login/) (Life Science Login) is the
identity provider of the ELIXIR On-Cloud: the [Cloud Registry](cloud-registry.md) trusts it only. This
page shows how to register a service, how LS Login releases group
memberships to it (see [Groups and facilities](#groups-and-facilities)),
and how to connect three services to LS Login: JupyterHub, HedgeDoc and
MinIO.

For the registration of a service, and for everything else about LS Login,
see the [LS Login docs](https://lifescience-ri.eu/registering-integrating-and-managing-your-service/).

## Register your service

Do this once for each service:

1. Register the service in LS Login (see the [LS Login
   docs](https://lifescience-ri.eu/registering-integrating-and-managing-your-service/)).
2. Open the [SPREG tool](https://services.aai.lifescience-ri.eu/spreg).
3. On the SAML/OIDC page, add the redirect URI of your service (see the
   sections below). LS Login compares the URI exactly: the host name alone
   is not enough.
4. On the same page, copy the client ID and the client secret.
5. Keep the client secret in a secret store, never in a repository.

Use one LS Login client for each service.

### Test and production

LS Login keeps a new service in its test environment for at most 30 days.
If its owner takes no action within another 14 days, LS Login deactivates
the service (the LS Login team, December 2025). Move a service to
production in time, as described in the [LS Login
docs](https://lifescience-ri.eu/registering-integrating-and-managing-your-service/).

The terms that apply to a registered service:

- [Terms of Use for Service
  Providers](https://www.lifescience-ri.eu/terms-of-use-for-service-providers/);
- the [LS AAI service level
  declaration](https://docs.google.com/document/d/17IoouL1vaY7TYCb7BrK_LFMtDYMv61SY0gZRxKoAIJQ/edit?usp=sharing),
  which says what services that depend on LS Login can expect of it.

Both are linked, with the other policies, from the [LS Login
page](https://lifescience-ri.eu/ls-login/).

## Groups and facilities

Services of the ELIXIR On-Cloud that map LS Login groups to roles, such as
the [Cloud Registry](cloud-registry.md#admins), proTES and TESK (see
[Onboard a Node](node-onboarding-tutorial.md#tesk)), see only the groups
that LS Login releases to them. A user who is a member of a group but gets
`403 Forbidden` from such a service usually lacks the release, not the
membership.

### How LS Login releases groups

LS Login keeps its users, groups and services in Perun:

- A **virtual organisation** (VO) holds groups, e.g., `example_vo` with
  the group `example_group`.
- A **facility** represents a client (a registered service) in Perun.
- A **resource** connects a facility with a VO. Groups of the VO are
  assigned to the resource.

LS Login puts a group into the user's entitlements **only if the group is
assigned to a resource on the facility of the client that requested the
token**. Membership alone is not enough: the same user gets a group from
one client and not from another (see Perun's
[Entitlements](https://perunaai.atlassian.net/wiki/spaces/PERUN/pages/209813518/Entitlements)).

### Which client needs the groups

Assign the groups to the facility of the client that users log in to: the
portal or front end that starts tasks or registers services. Services that
only validate the tokens of that client (APIs such as proTES, TESK or the
Cloud Registry) see the groups of that client; they don't need the groups
on a facility of their own. A client that only gets tokens for a service
itself (client credentials), with no users, needs no groups.

Assign only the groups that the services map to roles, e.g.,
`example_vo:example_group:admins` for admins, not every group of the VO.

With [token exchange](../demos/token-exchange-testbed.md), the LS Login
team says that the entitlements are computed for the client that calls the
exchange. Which groups a service at the end of such a chain sees is still
being tested.

### Users outside the groups

To let anyone with an LS Login account log in to a client, not only the
members of its groups, the LS Login team recommends a second resource on
the client's facility, for the Lifescience VO, with the VO's members group
assigned. Users outside the mapped groups can then log in, and services
answer them with `403 Forbidden`, so that a portal can tell them how to get
access.

### Assigning groups

1. In Perun, open the facility of the client and [create a
   resource](https://perunaai.atlassian.net/wiki/spaces/PERUN/pages/670400518/Create+and+remove+a+resource)
   for the VO that holds the groups.
2. Assign the groups to the resource (see [How to assign a group(s) to a
   resource](https://perunaai.atlassian.net/wiki/spaces/PERUN/pages/212828196/How+to+assign+a+group+s+to+a+resource)).
   This takes the role TrustedFacilityAdmin within the VO (see [Perun roles
   and their
   rights](https://perunaai.atlassian.net/wiki/spaces/PERUN/pages/1760100400/Perun+roles+and+their+rights)):
   being able to create the resource is not enough, and the button "Next"
   under "Assign groups" stays greyed out. If the VO's admins don't grant
   the role, send them links to the resource and to the groups, and ask
   them to assign the groups and confirm.
3. Check that the groups are listed among the resource's assigned groups.
4. Log in to the client with an account that is a member of a group, and
   read the released value (see [Reading the entitlement
   values](#reading-the-entitlement-values)).

### Reading the entitlement values

Group entitlements have this form (see Perun's [Group
entitlement](https://perunaai.atlassian.net/wiki/spaces/PERUN/pages/350879786/Group+entitlement)):

```text
urn:geant:lifescience-ri.eu:group:<vo>[:<group>[:<subgroup>]...]#aai.lifescience-ri.eu
```

For the group `example_group` of the VO `example_vo`:

```text
urn:geant:lifescience-ri.eu:group:example_vo:example_group#aai.lifescience-ri.eu
```

Group names are URL-encoded, and the value changes when a group is renamed
or moved. Services must match the exact value: don't guess it, read it
from a token of the client.

LS Login releases the values **in the user info only, not in the access
token**, in the claim `eduperson_entitlement`, and only if the client
requested the scope `eduperson_entitlement` at login. The client's
registration must allow that scope. To read the values, call the user info
endpoint with an access token of the client. Read the token into a
variable, so that it stays out of the shell history, and pass the header
via standard input, so that it stays out of process listings:

```bash
read -rs TOKEN
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl -fsS -H @- \
  --connect-timeout 10 --max-time 30 \
  https://login.aai.lifescience-ri.eu/oidc/userinfo
```

Handle tokens like passwords: never paste them into websites, tickets or
chats.

### How services read the groups

Services fetch the user info of each token and map its values to roles:

- FOCA-based services, such as the Cloud Registry and proTES, add the claim
  from the user info with `security.auth.userinfo_claims`, read it with
  `security.access_control.claim_groups` and map values to roles with
  `security.access_control.group_mapping` (see [Cloud
  Registry](cloud-registry.md#identity-provider)).
- TESK reads one claim of the user info and accepts the listed values (see
  [Onboard a Node](node-onboarding-tutorial.md#tesk)). Whether TESK accepts
  LS Login tokens this way has not been verified yet (see the gaps listed
  there).

### Checklist for a 403

If a user gets `403 Forbidden` from a service that maps groups:

1. **Membership:** is the user a member of the group in Perun?
2. **Release:** is the group assigned to a resource on the facility of the
   client that the user logged in with (the token's `aud`), not of another
   client? For an exchanged token, check the facility of the client that
   called the exchange (see [Which client needs the
   groups](#which-client-needs-the-groups)).
3. **Scope:** did the client request `eduperson_entitlement`, and does the
   user info of the token list the group (see [Reading the entitlement
   values](#reading-the-entitlement-values))?
4. **Value:** does the service map exactly the value in the user info,
   including the VO, the group path and `#aai.lifescience-ri.eu`?
5. **Caching:** services may cache the user info for some minutes (the
   Cloud Registry for 5): a change applies after that, or with a new token.

## JupyterHub

To deploy JupyterHub in the de.NBI Cloud, see this
[tutorial](https://cloud.denbi.de/wiki/Tutorials/JupyterHub/).

1. Register the redirect URI `https://{yourdomain}/hub/oauth_callback`.
   Replace `{yourdomain}` with your host name.
2. Add this to the `config.yaml` of the Helm chart (see the [Zero to
   JupyterHub docs](https://z2jh.jupyter.org/en/stable/administrator/authentication.html)):

```yaml
hub:
  config:
    Authenticator:
      allowed_users: # Only these LS Login users can log in
        - USER
      admin_users:
        - ADMIN # A user name that is an admin
    GenericOAuthenticator:
      client_id: # The client ID from SPREG
      client_secret: # The client secret from SPREG
      login_service: LS LOGIN
      oauth_callback_url: https://{yourdomain}/hub/oauth_callback
      authorize_url: https://login.aai.lifescience-ri.eu/oidc/authorize
      token_url: https://login.aai.lifescience-ri.eu/oidc/token
      userdata_url: https://login.aai.lifescience-ri.eu/oidc/userinfo
      username_claim: preferred_username # Newer versions
      username_key: preferred_username # Deprecated in newer versions
      scope:
        - openid
        - email
        - profile
    JupyterHub:
      authenticator_class: generic-oauth
cull:
  enabled: false
```

`allow_all: true` would let every LS Login user in. Keep the list of allowed
users instead. Do not put the client secret into a values file that you
commit: pass it at deploy time, for example from a secret store.

## HedgeDoc

HedgeDoc reads its settings from environment variables. These steps assume
that HedgeDoc is deployed already, for example with this [Helm
chart](https://github.com/CSCfi/helm-charts/tree/main/charts/hedgedoc).

1. Register the redirect URI of your HedgeDoc in SPREG (see the [HedgeDoc
   docs](https://docs.hedgedoc.org/configuration/#oauth2-login)).
2. Add these environment variables to the deployment:

```yaml
- name: CMD_OAUTH2_USER_PROFILE_URL
  value: https://login.aai.lifescience-ri.eu/oidc/userinfo
- name: CMD_OAUTH2_USER_PROFILE_USERNAME_ATTR
  value: preferred_username
- name: CMD_OAUTH2_USER_PROFILE_DISPLAY_NAME_ATTR
  value: name
- name: CMD_OAUTH2_USER_PROFILE_EMAIL_ATTR
  value: email
- name: CMD_OAUTH2_TOKEN_URL
  value: https://login.aai.lifescience-ri.eu/oidc/token
- name: CMD_OAUTH2_AUTHORIZATION_URL
  value: https://login.aai.lifescience-ri.eu/oidc/authorize
- name: CMD_OAUTH2_CLIENT_ID
  value: _REPLACE BY CLIENT ID_
- name: CMD_OAUTH2_CLIENT_SECRET
  value: _REPLACE BY CLIENT SECRET_
- name: CMD_OAUTH2_PROVIDERNAME
  value: ELIXIR On-Cloud
- name: CMD_OAUTH2_SCOPE
  value: openid email profile
```

## MinIO

You can turn on LS Login in the MinIO console (OIDC settings) or with
environment variables (see the [MinIO
docs](https://min.io/docs/minio/linux/operations/external-iam/configure-openid-external-identity-management.html)):

```sh
export MINIO_IDENTITY_OPENID_CONFIG_URL="https://login.aai.lifescience-ri.eu/oidc/.well-known/openid-configuration"
export MINIO_IDENTITY_OPENID_CLIENT_ID="<ID of the LS Login service>"
export MINIO_IDENTITY_OPENID_CLIENT_SECRET="<Secret of the LS Login service>"
export MINIO_IDENTITY_OPENID_DISPLAY_NAME="<Label of the login button, e.g., LS Login>"
export MINIO_IDENTITY_OPENID_SCOPES="<Scopes to request, e.g., openid,email,profile>"
export MINIO_IDENTITY_OPENID_ROLE_POLICY="<Policy for LS Login users, e.g., readonly>"
export MINIO_IDENTITY_OPENID_CLAIM_USERINFO="on"
```

MinIO has two ways to authorize users with OIDC (see the [MinIO
docs](https://min.io/docs/minio/linux/administration/identity-access-management/oidc-access-management.html#minio-external-identity-management-openid)).
Use the RolePolicy flow: MinIO assigns each LS Login user to one or more
policies. A policy can limit access to a bucket, for example to the members
of an LS Login group (see [policy-based access
control](https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html#tag-based-policy-conditions)).

This policy gives the listed users, identified by their `preferred_username`
claim, read access to the bucket `sensitive`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::sensitive",
                "arn:aws:s3:::sensitive/*"
            ],
            "Condition": {
                "StringEquals": {
                    "jwt:preferred_username": [
                        "ELIXIR_USERNAME"
                    ]
                }
            }
        }
    ]
}
```

## Compute access

Researchers get access to the compute services of the deployment, such as
proTES, through the LS Login group `ECP_CLN:EOC-Compute`: only its
members may create jobs, i.e., TES tasks and WES workflow runs (see
[Access control for compute](policies.md#access-control-for-compute)).
proTES maps it to its `user` role, and `ECP_CLN:ADMIN` to `admin`, which
is for administration, not for running jobs: admins who run jobs join
`ECP_CLN:EOC-Compute` too. Researchers apply with
the group's application form in Perun (see [Apply for compute
access](../researchers/index.md#apply-for-compute-access)); the members of
`ECP_CLN:ADMIN` approve or reject the applications.

LS Login releases the group only to clients whose Perun facility has it
assigned to a resource, as described under "Groups and facilities" on this
page. `ECP_CLN:EOC-Compute` is assigned to the facility of Krini, so
tokens that users get from Krini carry it.

### How approvals work

- **The form** asks for the applicant's affiliation (prefilled from the
  identity provider, when it releases one) and the reason for access; both
  are required. Applications are approved by hand.
- **ELIXIR membership:** `ECP_CLN:EOC-Compute` is a group of the `elixir`
  virtual organisation. Applicants who aren't members of it yet apply for
  both at once; the group application can be approved only once the
  organisation membership is (see Perun's [Creating and managing an
  application
  form](https://perunaai.atlassian.net/wiki/spaces/PERUN/pages/791609384/Creating+and+managing+an+application+form)).
- **Who approves:** the group `ECP_CLN:ADMIN` holds a manager role on
  `ECP_CLN:EOC-Compute`, so its members get an e-mail for each new
  application. They review it in Perun, under the group's
  **Applications**, and approve or reject it (see Perun's [Adding a member
  via application
  approval](https://perunaai.atlassian.net/wiki/spaces/PERUN/pages/1757675526/Adding+a+member+via+application+approval)).
  The role belongs to the group, so admins lose it when they leave
  `ECP_CLN:ADMIN`.
- **What applicants get:** e-mails when their application was received,
  approved or rejected. After the approval, they log in again: tokens
  issued before it don't carry the group.
- **Before approving,** check that the reason fits the deployment: a
  sandbox for demos and tests with synthetic or public data, not for
  personal or other sensitive data.
