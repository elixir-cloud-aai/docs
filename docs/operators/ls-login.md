---
last_verified: null
---

# LS Login

[LS Login](https://lifescience-ri.eu/ls-login/) (Life Science Login) is the
identity provider of the ELIXIR On-Cloud: the [Cloud Registry](cloud-registry.md) trusts it only. This
page shows how to connect three services to LS Login: JupyterHub, HedgeDoc
and MinIO.

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
proTES, through the LS Login group `ECP_CLN:EOC-Compute`: proTES maps it
to its `user` role, and `ECP_CLN:ADMIN` to `admin`. Researchers apply with
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
