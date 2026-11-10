# Cloud Registry

## Synopsis

[Cloud Registry][cr-repo] is the ELIXIR On-Cloud implementation of the
[GA4GH Service Registry API][ga4gh-service-registry]. Operators of services
register them, become their owners and can share them with others; admins
verify them. Anyone can browse the registry.

This page describes the **ELIXIR On-Cloud deployment** at
<https://registry.elixir-on.cloud/>. It is an addendum to the Cloud Registry
documentation, which covers everything that is not specific to this
deployment.

This page is for the admins who run the registry. To register the TES
service of your Node, see [Onboarding](onboarding.md); to look up, register
and maintain services, see [Using the Cloud
Registry](using-cloud-registry.md).

Product documentation:

- [Deployment][cr-deployment] (the Helm chart; in the repository:
  [`deployment/README.md`][cr-deployment-readme])
- [Upgrading][cr-upgrading]: [From 1.0.0rc1][cr-upgrading-1.0.0rc1], and
  from earlier versions on the same page
- [Configuration][cr-configuration], [Access control][cr-access-control]
  and [Operations][cr-operations]
- [Release notes of 1.0.0rc2][cr-release-notes]
- The front end's [operator guide][cr-ui-operator-guide], [upgrade
  notes][cr-ui-upgrading-1.0.0-rc2] and [release notes of
  1.0.0-rc2][cr-ui-release-notes] (see [Front end](#front-end))

!!! info "Last checked against Cloud Registry v1.0.0rc2 and Cloud Registry UI v1.0.0-rc2"
    For a later release, read its release notes and upgrade steps first,
    then update the version in the links and commands of this page (the
    chart URL, the images and the links to the documentation). The
    registry spells its pre-releases the PEP 440 way (`1.0.0rc2`, tag
    `v1.0.0rc2`), its chart and the UI the SemVer way (`1.0.0-rc2`, tag
    `v1.0.0-rc2` of the UI).

For anything this page doesn't answer, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email].

## Overview

| What | Value |
|---|---|
| Front end ([Cloud Registry UI][cr-ui-repo]) | <https://registry.elixir-on.cloud/> |
| API base URL | <https://elixir-on.cloud/ga4gh/registry/v1> |
| API documentation (Swagger UI) | <https://elixir-on.cloud/ga4gh/registry/v1/ui/> |
| Identity provider | [LS Login][ls-login], issuer `https://login.aai.lifescience-ri.eu/oidc/` |
| Admins | members of the LS Login group `ECP_CLN:ADMIN`, in admin mode (see [Admins](#admins)) |
| Helm chart | `cloud-registry-1.0.0-rc2.tgz` of the [v1.0.0rc2 release][cr-release] (deploys the image `docker.io/elixircloud/cloud-registry:1.0.0rc2`) |
| Front end image | `docker.io/elixircloud/cloud-registry-ui:1.0.0-rc2` of the [v1.0.0-rc2 release][cr-ui-release] (see [UI version](#ui-version)) |
| Database | MongoDB 7.0, deployed by the chart |

The API's base path is `/ga4gh/registry/v1` (not
`/ga4gh/service-registry/v1`). The front end and the API are served on
different host names: the front end calls the API from the user's browser,
at the API URL configured in the front end's deployment.

## Replacing the deployment before 0.4.0 (one-time)

!!! danger "Redeploy with a fresh install and an empty database"
    Do not migrate the data of the deployment before 0.4.0. That version
    (Helm chart 2, FOCA 0.12) accepted tokens of **any** issuer and had no
    ownership checks: anyone with any OpenID Connect token could create,
    change or delete entries, so its data can't be trusted. Services stored
    before 0.4.0 would also have no owner, so only admins could manage them.

Follow [From versions before 0.4.0][cr-upgrading-0.4.0]; for this
deployment:

1. Export the registered services, as a reference for their operators (the
   list is public). Continue only if the number of services looks right:

    ```bash
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services \
      > services-before-0.4.0.json
    jq length services-before-0.4.0.json
    ```

2. Note how the old release serves TLS (a `tls` section and cert-manager
   annotations in its Ingress, or none if TLS is terminated in front of the
   cluster), to configure the new one the same way (see [Values
   file](#values-file)):

    ```bash
    kubectl get ingress -n <namespace> -o yaml
    ```

3. Find and uninstall the old release. Uninstalling deletes its MongoDB
   volume (the claim `mongodb`) and the data; check that the claim is gone,
   and delete it by hand if it isn't:

    ```bash
    helm ls -n <namespace>
    helm uninstall <release> -n <namespace>
    kubectl get pvc -n <namespace>
    ```

    If the volume's reclaim policy is `Retain`, deleting the claim keeps the
    PersistentVolume and its data: delete it too (`kubectl get pv` lists it
    as `Released`; `kubectl delete pv <name>`), and its storage, if the
    storage isn't deleted with it.

4. Install v1.0.0rc2 (see [Installation](#installation)). Then ask the
   operators of the exported services to register them again (e.g., in the
   front end, by importing their service info), so that they become their
   owners; admins verify them (see [Verified
   services][cr-verified-services]).

## Upgrading from 1.0.0rc1

!!! warning "1.0.0rc2 starts with an empty database"
    Data is not kept, and there is no migration: 1.0.0rc2 stores the fields
    that the registry adds in camelCase, and refuses to start on data or
    indexes of any earlier version, naming the collections. Services,
    service types, roles, invitations and verifications are registered
    again after the upgrade.

Follow [From 1.0.0rc1][cr-upgrading-1.0.0rc1], the chart's notes [To app
version 1.0.0rc2][cr-chart-1.0.0rc2] and the UI's [upgrade
notes][cr-ui-upgrading-1.0.0-rc2]. **Upgrade the registry first, then the
front end, in the same maintenance window, with the front end stopped
while the registry is upgraded:** the front end of 1.0.0-rc2 doesn't work
with the registry of 1.0.0rc1 (it would give roles to the wrong users), and
the front end of 1.0.0-rc1 can't read the registry of 1.0.0rc2 (see the
UI's [Compatibility][cr-ui-compatibility]). For this deployment:

1. **Login settings, before the upgrade:** register the front end's login
   page, `https://registry.elixir-on.cloud/auth/login`, as a post-logout
   redirect URI of its LS Login client (see [Registering the front end with
   LS Login](#registering-the-front-end-with-ls-login)). From 1.0.0-rc2,
   logging out also ends the session at LS Login, which lists an
   `end_session_endpoint` in its [discovery document][ls-login-discovery];
   without the URI, LS Login may show an error after logging out. The
   issuer in `LOGIN_PROVIDERS` and `LOGIN_REDIRECT_URI` must be `https`
   URLs, as they are in [Settings](#settings); the front end refuses to
   start otherwise.
2. **Export what is registered**, as a reference for registering it again
   (the lists are public). Roles and invitations aren't public, so owners
   share their services again after the upgrade:

    ```bash
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services \
      > services-1.0.0rc1.json
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services/types \
      > service-types-1.0.0rc1.json
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/verifications \
      > verifications-1.0.0rc1.json
    jq length services-1.0.0rc1.json
    ```

3. **Back up the database of 1.0.0rc1** (see [Backups](#backups)), e.g.,
   with a dump by the CronJob, and check that it arrived. Going back to
   1.0.0rc1 needs its database as it was:

    ```bash
    kubectl create job --from=cronjob/cloud-registry-backup backup-before-1.0.0rc2 -n <namespace>
    kubectl logs job/backup-before-1.0.0rc2 -n <namespace> --all-containers
    ```

4. **Stop the front end** for the whole upgrade:

    ```bash
    kubectl scale deploy/cloud-registry-ui --replicas=0 -n <namespace>
    ```

5. **Empty the database:** scale the app to 0 replicas, wait until its pods
   are gone, and drop the database `serviceStore`, as the [chart's
   notes][cr-chart-1.0.0rc2] show. Dropping the database keeps its users,
   so the Secret with the MongoDB credentials stays valid:

    ```bash
    kubectl scale deploy/cloud-registry --replicas=0 -n <namespace>
    kubectl wait --for=delete pod -n <namespace> --timeout=120s \
      -l app.kubernetes.io/instance=cloud-registry,app.kubernetes.io/component=app
    kubectl exec deploy/cloud-registry-mongodb -n <namespace> -- sh -c 'mongosh serviceStore --quiet \
      -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" \
      --authenticationDatabase admin --eval "db.dropDatabase()"'
    ```

6. **Values file:** nothing must change. It gives no
   `config.security.access_control.policies`, so the new rules of imports,
   syncs and notifications, and the moved rule `owners-change-permissions`,
   apply as they are. The environment of its service info, `prod`, is one
   of the allowed environments, `[prod, test]`, as 1.0.0rc2 checks on
   startup. The new settings keep their defaults (see [Service info import
   and sync](#service-info-import-and-sync), [Notifications](#notifications)
   and [Invitations](#invitations)).
7. **Outgoing connections:** the registry now fetches service info from
   public addresses, when users import it and for syncs. If the cluster
   restricts the connections of the namespace's pods, allow the app's pods
   to connect to public addresses on port 443, as for LS Login (see
   [Network policies](#network-policies)); otherwise, imports fail and
   synced services become `out-of-sync`.
8. Download and verify the chart and the image of v1.0.0rc2 (see
   [Verifying the chart and the
   image](#verifying-the-chart-and-the-image)), upgrade with the verified
   chart file (see [Upgrades](#upgrades); `helm upgrade` restores the
   replicas of the values file), and wait for the app:

    ```bash
    helm upgrade cloud-registry ./cloud-registry-1.0.0-rc2.tgz \
      -n <namespace> -f values-prod.yaml
    kubectl rollout status deploy/cloud-registry -n <namespace>
    ```

9. **Front end:** deploy the release image of v1.0.0-rc2, verified and
   pinned by its digest (see [Verifying the UI
   image](#verifying-the-ui-image)), with the same settings (see
   [Settings](#settings); the two new ones keep their defaults), and wait
   for it. The manifest restores the 2 replicas (see [Running the front
   end](#running-the-front-end)):

    ```bash
    kubectl apply -f deployment-cloud-registry-ui.yaml
    kubectl rollout status deploy/cloud-registry-ui -n <namespace>
    ```

    The session cookies have new names (`__Host-…`), so users who were
    logged in log in once more.
10. **Register again:** admins add the service types, in admin mode (see
    [Service types](#service-types)), and verify services as they are
    registered again; ask the operators of the exported services to
    register them again, by importing their service info, with sync on
    (see [Using the Cloud Registry](using-cloud-registry.md)), and to share
    them again.

Then go through the [checks](#checks-after-installing).

API clients and scripts must follow the API of 1.0.0rc2 in the same
upgrade: the fields and query parameters that the registry adds are in
camelCase (e.g., `registrationRules`, `adminAvailable`, `verifiedAt`,
`userId`), and roles of users move to
`/services/<id>/permissions/users/<user-id>`, without aliases (see [From
1.0.0rc1][cr-upgrading-1.0.0rc1] for all names). Log checks and alerts that
rely on request paths must follow too: from FOCA 0.22, the logs name routes
(e.g., `/ga4gh/registry/v1/services/{serviceId}`) instead of paths.

**Going back** to 1.0.0rc1 needs its database, as it was: roll the registry
and the front end back together, and restore the backup of step 3 (see
[Testing a restore](#testing-a-restore)).

## Upgrading from 0.6.0

These steps lead to 1.0.0rc1, which keeps the data. 1.0.0rc2 needs a fresh
database from any earlier version, so to go from 0.6.0 to 1.0.0rc2, follow
[Upgrading from 1.0.0rc1](#upgrading-from-100rc1) instead, with the front
end of 1.0.0-rc2 replacing one built from a branch (see step 7 below for
the settings that changed).

Data is kept. Follow [From 0.6.0][cr-upgrading-0.6.0] and the chart's notes
[To app version 1.0.0rc1][cr-chart-1.0.0rc1]. **Upgrade the registry first,
then the front end**, in the same maintenance window: the front end of
1.0.0-rc1 goes with the registry of 1.0.0rc1, and uses its invitations and
limit of services once the registry has them (see the UI's [upgrade
notes][cr-ui-upgrading-1.0.0-rc1]). For this deployment:

1. **Services per user:** the values file below limits users other than
   admins to 20 services each (see [Services per
   user](#services-per-user)), not to the default of 50. The app counts
   each user's services on its first start, so check the counts right
   after the upgrade, with the command of the [chart's
   notes][cr-chart-1.0.0rc1], with `20` instead of `50`. Users at or above
   the limit keep their services, but can't register more until they are
   below it. Services that admins registered before the upgrade count for
   the admin; if an admin registered many (e.g., imported them), make them
   count for nobody, as described in [From 0.6.0][cr-upgrading-0.6.0].
2. **Policies:** the values file below neither gives
   `config.security.access_control.policies` nor changes the owners'
   rules, so the new rules of invitations apply as they are (see
   [Invitations](#invitations)). If yours gives the policies as a list or
   restricts `owners-change-permissions`, change them as the [chart's
   notes][cr-chart-1.0.0rc1] say.
3. **Organization fields:** registrations and updates with organization
   fields other than `name` and `url` are now rejected. Before upgrading,
   list the services that have others, and tell their owners, or clean
   them up as described in [Stored
   services][cr-upgrading-stored-services]. The public list leaves out
   pending services; the app warns of all such services, pending ones
   included, on startup (see [Checks](#checks-after-installing)):

    ```bash
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services \
      | jq '[.[] | select(.organization // {} | keys - ["name", "url"] | length > 0) | .id]'
    ```

4. **Image name:** the chart's default image is now fully qualified
   (`docker.io/elixircloud/cloud-registry`). The values file below sets no
   `cloudRegistry.image`; if the cluster has image allow-lists, admission
   policies or registry mirror rules that match the short name
   `elixircloud/cloud-registry`, adapt them before upgrading.
5. **Replicas:** the chart can now run several pods of the app; the values
   file below sets `cloudRegistry.replicas: 2` (see
   [Replicas](#replicas)).
6. Download and verify the chart and the image of v1.0.0rc1 (see
   [Verifying the chart and the
   image](#verifying-the-chart-and-the-image)), upgrade with the verified
   chart file (see [Upgrades](#upgrades)), and wait for the app. Then
   restart it once, so that services that pods of 0.6.0 registered,
   updated or deleted during the rollout are counted correctly. Pods of
   0.6.0 apply neither the limit of services nor the check of organization
   fields, so writes during the rollout can bypass both; to rule that out,
   scale the app to 0 replicas before upgrading instead (`helm upgrade`
   restores the replicas of the values file), at the cost of a short
   downtime:

    ```bash
    kubectl rollout status deploy/cloud-registry -n <namespace>
    kubectl rollout restart deployment/cloud-registry -n <namespace>
    kubectl rollout status deploy/cloud-registry -n <namespace>
    ```

7. **Front end:** replace the front end built from a branch (`ai` or
   `ai-post-deploy`) with the release image of v1.0.0-rc1 (see [UI
   version](#ui-version)), following the UI's [upgrade
   notes][cr-ui-upgrading]:

    - **Image:** `docker.io/elixircloud/cloud-registry-ui:1.0.0-rc1`,
      verified and pinned by its digest (see [Verifying the UI
      image](#verifying-the-ui-image)).
    - **Login settings:** the front end reads only `LOGIN_PROVIDERS` and
      `LOGIN_REDIRECT_URI` (see [Settings](#settings)). If its Secret
      still has `LS_LOGIN_URL` and `OIDC_*`, move their values into these
      as the [UI's upgrade notes][cr-ui-upgrading-login] show: the client
      ID and secret into `LOGIN_PROVIDERS`, with the issuer
      `https://login.aai.lifescience-ri.eu/oidc/`, and
      `OIDC_REDIRECT_URI` into `LOGIN_REDIRECT_URI` (same value). The
      front end stops at start if it finds only the old variables; next to
      `LOGIN_PROVIDERS`, it ignores them with a warning. Remove them, so
      that no stale client secret stays in the deployment.
    - **Audience:** the client ID in `LOGIN_PROVIDERS` must be in the
      registry's `config.security.auth.audience` (see
      [Audience](#audience)). Keeping the front end's LS Login client
      changes nothing; if you register a new client for it, add its ID to
      the audience and upgrade the registry before switching the front
      end, or every create, update and delete fails with `401`.
    - **Settings that are gone:** remove `NEXT_PUBLIC_SERVICE_ENVIRONMENTS`
      and `NEXT_PUBLIC_SERVICE_URL_SCHEMES`; the front end now reads the
      allowed environments and URL schemes from the registry (see
      [Service environments](#service-environments)). It ignores them,
      with a warning on start.
    - **Build arguments:** the release image holds no settings; pass them
      all when the container starts (see [Settings](#settings)).

    Then go through the [checks](#checks-after-installing).

## Upgrading from 0.4.0 or 0.5.0

As for 0.6.0, these steps lead to 1.0.0rc1; to go to 1.0.0rc2, which needs a
fresh database from any earlier version, follow [Upgrading from
1.0.0rc1](#upgrading-from-100rc1) instead.

Data is kept. Upgrade one release at a time, never directly to 1.0.0rc1:
from 0.4.0 to 0.5.0, then to 0.6.0, then to 1.0.0rc1 (see [Upgrading from
0.6.0](#upgrading-from-060)), each time with the chart of that release
(see [Upgrades](#upgrades)). Follow the registry's guides [From
0.4.0][cr-upgrading-0.4.0-to-0.5.0] and [From 0.5.0][cr-upgrading-0.5.0]
and the chart's notes [To app version 0.5.0][cr-chart-0.5.0] and [To app
version 0.6.0][cr-chart-0.6.0]. The values file below is for 1.0.0rc2,
and sets nothing that 1.0.0rc1 doesn't know: leave out what the earlier
releases don't know (`config.custom.access_control.max_services_per_user` and
`config.security.access_control.opt_in_roles` for 0.5.0,
`max_services_per_user` and `cloudRegistry.replicas` for 0.6.0; 0.6.0
refuses to start with keys of `config.custom` that it doesn't know). For
this deployment:

- **To 0.5.0:** before upgrading, check the environments of the stored
  services (see [Service environments](#service-environments)), and set up
  the rate limits (see [Rate limits](#rate-limits)). After the rollout,
  restart the app once, so that it stores the types of the services that
  pods of 0.4.0 registered during it (`kubectl rollout restart
  deployment/cloud-registry -n <namespace>`). Keep the mode `controlled` of
  service types; set `moderated` only after the restart.
- **To 0.6.0:** admins act as admins only in admin mode from 0.6.0 (see
  [Admin mode](#admin-mode)). Revoke rules that grant the role `admin` via
  the permissions API, and add the users to the admin group instead (see
  [Admins](#admins)). A front end from the branch `ai` has no admin mode
  switch: to keep its admins able to act as admins until the front end of
  v1.0.0-rc1 is deployed, set `config.security.access_control.opt_in_roles:
  []` for this step, and remove it in the upgrade to 1.0.0rc1.

## Version

Install the chart attached to the release (downloaded by its versioned URL
and verified, see below), and set
neither `cloudRegistry.tag` nor a tag in `cloudRegistry.image`: the chart
then deploys the image of its release (see [Image][cr-image] and
[Installation][cr-installation]). Don't deploy the moving image tags `latest`
or `dev`, nor the chart from the repository's `deployment` folder (which
deploys `dev`): a restart of a pod could then start another version than the
one the config was written for.

### Verifying the chart and the image

**Verify the signatures of the chart and the image before every install and
upgrade**, and install the chart file that you verified (see [Verifying
images and charts][cr-verifying]). The registry holds the URLs to which
clients send their users' access tokens, so a tampered chart or image would
expose them; the checks prove that both were built by the release workflow
of the Cloud Registry repository for the release tag. With the [GitHub
CLI][gh-cli] (or the `cosign` commands of the linked section), for
1.0.0rc2, whose chart file is spelled `1.0.0-rc2`:

```bash
gh release download v1.0.0rc2 --repo elixir-cloud-aai/cloud-registry \
  --pattern 'cloud-registry-1.0.0-rc2.tgz*'
gh attestation verify cloud-registry-1.0.0-rc2.tgz \
  --repo elixir-cloud-aai/cloud-registry \
  --signer-workflow elixir-cloud-aai/cloud-registry/.github/workflows/release.yml \
  --source-ref refs/tags/v1.0.0rc2
gh attestation verify oci://docker.io/elixircloud/cloud-registry:1.0.0rc2 \
  --repo elixir-cloud-aai/cloud-registry \
  --signer-workflow elixir-cloud-aai/cloud-registry/.github/workflows/release.yml \
  --source-ref refs/tags/v1.0.0rc2
```

Don't install if a check fails. `--source-ref` checks that the workflow ran
for the release tag, not for another branch.

### MongoDB and the nodes' kernels

The chart pins MongoDB 7.0 (`mongodb.image: docker.io/library/mongo:7.0`);
keep it. MongoDB 8.0 refuses to start on Linux kernels 6.19 to 7.0.13
([SERVER-121912][mongodb-server-121912]), so before moving to MongoDB 8.x,
check the kernels of all nodes that MongoDB may run on:

```bash
kubectl get nodes -o custom-columns=NODE:.metadata.name,KERNEL:.status.nodeInfo.kernelVersion
```

This covers only the current nodes: nodes added later (e.g., by an
autoscaler) need compatible kernels too. MongoDB upgrades go one major version at a time, and
binaries can't be downgraded (see [Version][cr-mongodb-version]).

## Configuration

### Identity provider

The deployment trusts **LS Login** only. Its endpoints and supported scopes
and claims are listed in its [discovery document][ls-login-discovery].

| Setting | Value | Why |
|---|---|---|
| `config.security.auth.issuers` | `["https://login.aai.lifescience-ri.eu/oidc/"]` | the `iss` claim of LS Login tokens (with the trailing slash) |
| `config.security.auth.audience` | the client IDs of all front ends, one client each (see [Audience](#audience)) | LS Login sets `aud` to the client that the user logged in with |
| `config.security.auth.userinfo_claims` | `["eduperson_entitlement", "name"]` | LS Login releases groups and names via its user info endpoint, not in access tokens |
| `config.security.access_control.claim_groups` | `eduperson_entitlement` | the claim with the user's group memberships |
| `config.security.access_control.group_mapping` | the admin group mapped to `admin` (see [Admins](#admins)) | required: the app refuses to start without admins |

LS Login releases `eduperson_entitlement` only if the client requested the
scope of the same name when the user logged in. **Front ends must request the
scopes `openid profile eduperson_entitlement`** (`profile` for `name`), and
their client registration in LS Login must allow them; otherwise, admins act
as ordinary users and roles of groups don't apply. LS Login access tokens are
JWTs as per RFC 9068 (`typ: at+jwt`), as the registry requires.

The public reads (`GET /services`, `GET /services/types` and the
verifications) accept an optional token: with one, they apply that user's
visibility rules, e.g., show the user's pending types and services. Invalid
or expired tokens are rejected with `401`, so that the front end logs the
user in again; if LS Login can't be reached, such reads are served as
anonymous (see [Authentication][cr-ac-authentication]).

### Audience

The registry accepts tokens only for the client IDs in
`config.security.auth.audience`. Set it to the LS Login client IDs of
**all** apps that send tokens to the registry: the production front end, plus
any other front end (e.g., a preview deployment) or client for scripts that
should be able to register services. Without the front end's client ID,
logging in works, but every create, update and delete fails with
`401 Unauthorized`.

**Register one LS Login client per front end**: the registry UI, Krini and
the dashboard each have their own client, and each client ID is listed in
the audience. Each front end then has its own client secret and redirect
URIs: a secret that must be replaced, or a retired front end, affects only
its own client, which can be replaced or removed without touching the
others.

```yaml title="values-prod.yaml"
config:
  security:
    auth:
      audience:
        - "<client ID of the registry UI>"
        - "<client ID of Krini>"
        - "<client ID of the dashboard>"
```

Client IDs are not listed here. To obtain them:

- ask the maintainers of the front end's deployment (the client ID it is
  configured with), or the administrators of the client in [LS
  Login][ls-login];
- or decode the payload of an access token issued to that client and read
  its `aud` claim. Handle tokens like passwords: decode them locally, and
  never paste them into websites, tickets or chats.

### Admins

Members of this LS Login group are admins of the registry: in [admin
mode](#admin-mode), they can do everything, including registering services
with chosen identifiers, changing the identifiers of services and verifying
services (see [Admins][cr-admins]). Only groups make users admins: rules
can't grant the role `admin` (see [Making users admins][cr-making-admins]).

```text
urn:geant:lifescience-ri.eu:group:elixir:ECP_CLN:ADMIN#aai.lifescience-ri.eu
```

It is a value of the user's `eduperson_entitlement` claim. To see the groups
that LS Login releases for a user, call its user info endpoint with an
access token of that user, e.g., one issued to the front end. Read the token
into a variable, so that it stays out of the shell history, and pass the
header via standard input, so that it stays out of process listings:

```bash
read -rs TOKEN
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl -fsS -H @- \
  https://login.aai.lifescience-ri.eu/oidc/userinfo
```

The response lists the groups in `eduperson_entitlement` (if the token's
scopes allow it). Group changes reach the registry within 5 minutes, as it
caches the user info per token (see [Group membership
changes][cr-group-membership-changes]).

### Admin mode

Admins act as admins only in **admin mode**: in requests with the header
`X-Request-Roles: admin`; their other requests have the rights of other
users (see [Admin mode][cr-admin-mode]). In the front end, admins switch
between "User mode" and "Admin mode" in the top bar, and start in user
mode (see [Admin mode][cr-ui-admin-mode] in the UI's documentation). Scripts
send the header with each request that needs admin rights.

The deployment keeps the opt-in of the base config
(`config.security.access_control.opt_in_roles: [admin]`): the values file
sets nothing for it. All releases of the front end have the switch (see [UI
version](#ui-version)).

### Service environments

**Allow the environments `prod` and `test` only**, rather than the four
defaults (`prod`, `test`, `dev` and `staging`, as suggested by the GA4GH
specification): the TES network has production and test nodes only, and
two unambiguous choices keep the filters by environment useful.
Registrations with other values are rejected with `400 Bad Request` (see
[Service environments][cr-service-environments]):

```yaml title="values-prod.yaml"
config:
  custom:
    endpoints:
      services:
        environments: [prod, test]
```

The front end reads the allowed environments from the registry's service
info and offers only these, so there is nothing to set in it (see
[Registry][cr-ui-registry-settings]). Before setting this on a running
deployment, check the environments of the stored services (the list of
services is public, so no access to the database is needed; `null` means
services without one):

```bash
curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services \
  | jq '[.[].environment] | unique'
```

Services with other values are still served, but can only be updated with
`prod` or `test`, and the app warns of them on startup. Users can still
register and edit services until the change, so check again right before
it.

### Service URL schemes

**Keep the default: service URLs must be `https` URLs**
(`config.custom.endpoints.services.url_schemes`, default `[https]`; see
[Service URL schemes][cr-service-url-schemes]). Clients send access tokens
to the registered URLs, which must not travel unencrypted. The values file
sets nothing for it, and the front end reads the allowed schemes from the
registry's service info.

### Service types

Service types are stored, and `config.custom.access_control.service_types`
sets who may add them (see [Service types][cr-service-types-config]):
`open` (the default, any logged-in user), `controlled` (admins only) or
`moderated` (any logged-in user, but types of users other than admins, and
the services that have them, are pending until an admin approves them).

**Set the mode `controlled`.** The registry is primarily for the services of
the ECP TES network and the central services, not for arbitrary services, so
admins curate the list of types; open it up (`moderated`) only once enough
people bring good reasons for other types:

```yaml title="values-prod.yaml"
config:
  custom:
    access_control:
      service_types: controlled
```

Other users can then register services only with registered types:
registering a service with another type fails with `400 Bad Request`, and
`POST /ga4gh/registry/v1/services/types` with `403 Forbidden`. Admins add
types in admin mode, in the front end ("Service Types", "Add service type")
or with that request. Add the types of the TES network and the central
services before announcing the registry; the types of services that are
already registered are registered too.

**Leave `config.custom.access_control.max_unused_service_types` at its
default** (`10`): it limits how many types that no service has users other
than admins may add, and with `controlled`, they can't add any (see
[Service types][cr-service-types-config]). Admins remove unwanted types
that no service has (`DELETE /ga4gh/registry/v1/services/types`).

### Services per user

**Let users other than admins register at most 20 services each**
(`config.custom.access_control.max_services_per_user`, default `50`; see
[Services per user][cr-services-per-user]).
The limit bounds what a single account can fill the registry with; the rate
limits (see [Rate limits](#rate-limits)) slow down accounts created at
will.
Further registrations fail with `409 Conflict`; services that admins
register in admin mode count for nobody.

```yaml title="values-prod.yaml"
config:
  custom:
    access_control:
      max_services_per_user: 20
```

It is a config value, changed with a `helm upgrade` at any time. Lowering
it never removes services: users above the limit keep theirs, and can only
register more once they are below it. The front end shows the limit when it
refuses a registration (see [Limit on registered
services][cr-ui-services-limit]).

### Invitations

Owners can invite users to their services by link, in the front end or
via the API (see [Invitations][cr-invitations]). **Keep the defaults**
(`config.custom.access_control.invitations`: invitations are valid for
7 days, `expiry_days`, and a service may have 20 that haven't expired,
`max_per_service`): the values file sets nothing for them.

From 1.0.0rc2, invitations have an optional label that says who they are
for, and expired invitations that weren't accepted are kept for 30 days
(`keep_expired_days`, also a default), so that owners see who needs a new
link. With these defaults, an invitation that expires unaccepted keeps its
label, which may name a person, and who created it and when, for up to 37
days after it was created (7 before 1.0.0rc2). **Check this against the
deployment's privacy statement**; `keep_expired_days: 0` removes
invitations when they expire, as before. The front end requires a label
for new invitations by default (see [Settings](#settings)).

### Service info import and sync

Users import the values of a registration from the service info of their
service, and keep the entry in sync with it; both are the recommended way
to register services here (see [Using the Cloud
Registry](using-cloud-registry.md)). **Keep the defaults**
(`config.custom.endpoints.services.service_info`; see [Service info
import][cr-service-info-import] and [Service info
sync][cr-service-info-sync]): the values file sets nothing for them.

- **Import:** from public addresses only (`private_networks: []`): only
  public service info can be imported or synced, never with a token; each
  user, admins too, may have service info fetched 30 times
  per hour (`fetches_per_hour`), and gets `429 Too Many Requests` above.
- **Sync:** on (`sync: true`), every 24 hours per service
  (`sync_interval_hours`). Each worker of the app runs a background thread
  that syncs the services that are due; the replicas share the work
  through the database, without any setup.

The registry connects to the services directly: proxy settings of the
environment (e.g., `HTTPS_PROXY`) don't apply, so the app's pods need
connections to public addresses on port 443 (see [Network
policies](#network-policies)). Fetches take up to 10 seconds, so keep the
timeouts of the ingress (and of any proxy in front of it) above that. The
default CORS settings let the front end read `Retry-After` after
`429 Too Many Requests`; the values file doesn't change them.

### Notifications

From 1.0.0rc2, `GET /notifications` tells logged-in users what needs their
attention: users with a role on a service see when it is out of sync, and
admins, in admin mode, also see services and service types that wait for
approval, and services whose environment or URL scheme is no longer
allowed (see [Notifications][cr-notifications]). The front end shows them
in a bell in the top bar. There is nothing to set: they are computed from
the stored data, and nobody gets an email.

### Values file

Keep the values file in the infrastructure repository of the deployment, not
in the Cloud Registry repository. Secrets never go into it, as `config` ends
up in a ConfigMap; the MongoDB credentials are referenced by the name of a
Secret. The service info keeps the identifier
`ELIXIR_CLOUD_SERVICE_REGISTRY_1`, so that clients still recognize the
registry, and sets all fields that describe the deployment (see [Service
info][cr-service-info]). It collects the recommended settings of the
sections above and below, for 1.0.0rc2. The ingress controller's settings (rate limits, blocking
`/admin/`) depend on the controller and come on top (see [Exposing the
API](#exposing-the-api) and [Rate limits](#rate-limits)).

```yaml title="values-prod.yaml"
# Public host name of the API (not of the front end)
hostName: elixir-on.cloud

# No `cloudRegistry.tag`: the chart deploys the image of its release
cloudRegistry:
  # The release's tag doesn't move, so pulling on every start isn't needed
  imagePullPolicy: IfNotPresent
  ingress:
    https:
      # As noted for the old release (step 2 of the one-time replacement):
      # true to serve HTTPS with a certificate from cert-manager, false if
      # TLS is terminated in front of the cluster
      enabled: true
  # Only the ingress controller may connect (see "Network policies")
  networkPolicy:
    enabled: true
    ingressFrom:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: <namespace of the ingress controller>
      podSelector:
        matchLabels:
          app.kubernetes.io/name: <name label of its pods>
  # 2 pods, with a PodDisruptionBudget (see "Replicas"); no `gunicorn`:
  # the defaults (1 worker, 4 threads) fit
  replicas: 2

config:
  security:
    auth:
      issuers: ["https://login.aai.lifescience-ri.eu/oidc/"]
      # REQUIRED: replace with the LS Login client IDs of the front ends,
      # one client per front end (the chart accepts any non-empty value;
      # see "Audience")
      audience:
        - "<client ID of the registry UI>"
        - "<client ID of Krini>"
        - "<client ID of the dashboard>"
      userinfo_claims: ["eduperson_entitlement", "name"]
    access_control:
      claim_groups: eduperson_entitlement
      group_mapping:
        # Quoted, as it contains `#`
        "urn:geant:lifescience-ri.eu:group:elixir:ECP_CLN:ADMIN#aai.lifescience-ri.eu": admin
  custom:
    endpoints:
      services:
        # See "Service environments"; `url_schemes` keeps its default,
        # `[https]` (see "Service URL schemes"), and `service_info` its
        # defaults (see "Service info import and sync")
        environments: [prod, test]
    access_control:
      # Only admins add service types (see "Service types");
      # `max_unused_service_types` keeps its default
      service_types: controlled
      # See "Services per user"; `invitations` keeps its defaults (see
      # "Invitations", and check `keep_expired_days` against the privacy
      # statement)
      max_services_per_user: 20
  service_info:
    service:
      id: ELIXIR_CLOUD_SERVICE_REGISTRY_1
      name: ELIXIR On-Cloud Service Registry
      description: Registry of GA4GH and other web services of ELIXIR On-Cloud.
      organization:
        name: ELIXIR On-Cloud
        url: https://elixir-on.cloud/
      contactUrl: mailto:cloud-service@elixir-europe.org
      environment: prod

mongodb:
  auth:
    # Created before installing (see "Installation")
    existingSecret: cloud-registry-mongodb-credentials
```

### Exposing the API

The chart routes all paths of `hostName` to the app, including FOCA's
permissions API for admins in admin mode (`/admin/access-control/`; see
[Ingress][cr-ingress] and [TLS][cr-tls]). **Block `/admin/`, so that only
`/ga4gh/registry/v1/` is reachable from outside.** Admins of this deployment
come from the LS Login group (see [Admins](#admins)), not from the
permissions API, and the front end needs nothing under `/admin/`, so
blocking it only removes what nobody needs to reach.

Either way below works with the values file above; pick the one that the
cluster allows:

- **Without the chart's Ingress (any ingress controller):** disable the
  chart's Ingress and Route, and route only `/ga4gh/registry/v1/` to the
  app's Service (`cloud-registry`, port `http`) with an Ingress (or
  HTTPRoute) of your own. This is also the way to go if `elixir-on.cloud`
  serves other apps too:

    ```yaml title="values-prod.yaml"
    cloudRegistry:
      ingress:
        enabled: false
      route:
        enabled: false
    ```

    ```yaml title="ingress-cloud-registry.yaml"
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: cloud-registry-api
      namespace: <namespace>
      annotations:
        # As `cloudRegistry.ingress.https` would set them; leave them and
        # `tls` out if TLS is terminated in front of the cluster
        cert-manager.io/cluster-issuer: letsencrypt-prod
        kubernetes.io/tls-acme: "true"
        # The controller's settings, e.g., the rate limits (see "Rate limits")
    spec:
      ingressClassName: <Ingress class>
      rules:
      - host: elixir-on.cloud
        http:
          paths:
          - path: /ga4gh/registry/v1/
            pathType: Prefix
            backend:
              service:
                name: cloud-registry
                port:
                  name: http
      tls:
      - hosts: [elixir-on.cloud]
        secretName: cloud-registry-api-tls
    ```

    Apply it with `kubectl apply -f ingress-cloud-registry.yaml` and keep it
    in the infrastructure repository next to the values file.

- **With the chart's Ingress:** block `/admin/` at the proxy in front of the
  cluster, or in the ingress controller. *Example for ingress-nginx*, which
  needs snippet annotations to be allowed by the controller
  (`allow-snippet-annotations: "true"` and, from controller 1.12,
  `annotations-risk-level: Critical` in its ConfigMap; many clusters refuse
  them, as they let anyone who may create Ingresses change the controller's
  configuration):

    ```yaml title="values-prod.yaml"
    cloudRegistry:
      ingress:
        annotations:
          # Applies to the whole host, also to other apps on it
          nginx.ingress.kubernetes.io/server-snippet: |
            location /admin/ { return 404; }
    ```

The first way is the stricter one: an allow list of the API's base path,
while the second blocks only `/admin/`. Check it from outside the cluster
(see [Checks](#checks-after-installing)): `/admin/` must not reach the
app.

If the API moves to another host name, change `hostName` and the API URL in
the front end's deployment together, keeping the base path
`/ga4gh/registry/v1`.

Pass encoded slashes (`%2F`) in the API's paths on as they are, in the
ingress and in any proxy in front of it: the front end sends user IDs and
groups with slashes, e.g., IDs namespaced by issuer, that way, and a proxy
that decodes or refuses them makes the registry store another ID (see
[Behind a reverse proxy][cr-ui-reverse-proxy] in the UI's documentation,
and [Checks](#checks-after-installing)).

### Rate limits

**Limit the request rate per client IP address at the ingress: write
requests (`POST`, `PUT`, `DELETE`) to 10 per minute with a small burst, all
requests to 300 per minute.** The registry limits how many service types
and services each account adds, but not how often anyone
writes, and anyone can create LS Login accounts (see [Rate
limits][cr-rate-limits]). Registering a few services takes far fewer
writes; 300 requests per minute leave room for the front end, which sends
several reads per page. The controller must see the clients' addresses, not
those of a proxy in front of the cluster (e.g., with `use-forwarded-headers`
or the PROXY protocol); otherwise, all requests count for the proxy.

*Example for ingress-nginx.* The annotations limit all requests;
annotations can't tell methods apart, so the limit of writes needs a
`limit_req` zone keyed by the client address for writes only, in the
controller's ConfigMap (set by the cluster's admins), and a snippet
annotation that applies it (snippets must be allowed, see [Exposing the
API](#exposing-the-api)):

```yaml title="ConfigMap of ingress-nginx (data)"
http-snippet: |
  map $request_method $cloud_registry_writer {
    default "";
    POST $binary_remote_addr;
    PUT $binary_remote_addr;
    DELETE $binary_remote_addr;
  }
  limit_req_zone $cloud_registry_writer zone=cloud_registry_writes:10m rate=10r/m;
# Optional: answer excess requests with `429 Too Many Requests` (default: 503)
limit-req-status-code: "429"
```

```yaml title="values-prod.yaml"
cloudRegistry:
  ingress:
    annotations:
      # All requests: 300 per minute and client IP address, with a burst of
      # as many (the default multiplier, 5, would allow 1500 at once)
      nginx.ingress.kubernetes.io/limit-rpm: "300"
      nginx.ingress.kubernetes.io/limit-burst-multiplier: "1"
      # Writes: 10 per minute, a burst of 5 (requests with an empty key,
      # i.e., reads, aren't counted in this zone)
      nginx.ingress.kubernetes.io/configuration-snippet: |
        limit_req zone=cloud_registry_writes burst=5 nodelay;
```

Without the chart's Ingress, set the same annotations on your own Ingress
(`metadata.annotations` of `ingress-cloud-registry.yaml` in [Exposing the
API](#exposing-the-api)). With other controllers, use their own means, e.g.,
Traefik's `rateLimit` middleware on routes that match the methods, or the
rate limit policies of a Gateway implementation (see [Rate
limits][cr-rate-limits]).

### Network policies

MongoDB's NetworkPolicy is enabled by default: only the app's pods of the
release may connect. **Enable the app's NetworkPolicy too**
(`cloudRegistry.networkPolicy.enabled: true`, as in the values file), with
the cluster's ingress controller as the only peer
(`cloudRegistry.networkPolicy.ingressFrom`): the API is meant to be reached
through the ingress only, where TLS, the rate limits and the blocking of
`/admin/` apply, so other pods in the cluster shouldn't bypass them. Without
the controller in `ingressFrom`, the API becomes unreachable; rendering
fails if the policy is enabled without peers. The front end needs no entry,
as browsers call the API through the ingress. Find the controller's
namespace and pod labels with:

```bash
kubectl get ingressclass
kubectl get pods -A --show-labels | grep -Ei 'ingress|gateway|traefik'
```

Then set them as the peer, e.g.:

```yaml title="values-prod.yaml"
cloudRegistry:
  networkPolicy:
    enabled: true
    ingressFrom:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: <namespace of the ingress controller>
      podSelector:
        matchLabels:
          app.kubernetes.io/name: <name label of its pods>
```

See [Network policies][cr-network-policies] and FOCA's [NetworkPolicy
peers][foca-networkpolicy-peers] for the peers of common ingress
controllers and Gateways. The policies only take effect if the cluster's
network plugin enforces them.

These policies restrict the connections **to** the pods. From 1.0.0rc2, the
app also connects out, to fetch service info from public addresses (see
[Service info import and sync](#service-info-import-and-sync)), on top of
its connections to MongoDB and LS Login. The chart can restrict these too,
with an optional NetworkPolicy (`egressNetworkPolicy.enabled`, default
`false`; see [The app's connections][cr-apps-connections]): it lets the
app's pods connect only to DNS, the release's MongoDB and public addresses
on port 443. With its defaults, this covers the connections of this
deployment, as LS Login and the registered services are reached at public
`https` addresses; private addresses would need rules of their own
(`egressNetworkPolicy.to`). The values file doesn't enable it. The app
checks the addresses of service info itself either way.

### Replicas

**Run 2 replicas of the app, with the default Gunicorn settings**
(`cloudRegistry.replicas: 2`, as in the values file; 1 worker with 4
threads, `cloudRegistry.gunicorn`; see [Replicas][cr-replicas] and
[Server][cr-server]): with two pods, node drains, crashes and rolling
upgrades cause no downtime of the API, and the load is tiny, so more
workers or threads aren't needed. With more than one replica, the chart
adds a PodDisruptionBudget, so that node drains evict one pod at a time;
keep its default. MongoDB stays a single pod, so a drain of its node still
interrupts the API briefly.

The scheduler usually puts the two pods on different nodes, but doesn't
guarantee it; check where they run (see
[Checks](#checks-after-installing)). Set the number of replicas in the
values file only, not with `kubectl scale`: Helm manages the Deployment,
and a later upgrade or rollback sets it back without notice.

## Installation

1. Create the namespace, unless it exists:

    ```bash
    kubectl create namespace <namespace>
    ```

2. Create the Secret with the MongoDB credentials, with random passwords
   that are never written down. The Secret's keys are those of
   [Authentication][cr-authentication]; unlike the command there, this one
   (for Bash or Zsh) passes the passwords via a file descriptor rather than
   as arguments, so that they don't show up in process listings:

    ```bash
    kubectl create secret generic cloud-registry-mongodb-credentials -n <namespace> \
      --from-env-file=<(printf 'root-username=root\nroot-password=%s\nusername=cloud-registry\npassword=%s\n' \
        "$(openssl rand -hex 24)" "$(openssl rand -hex 24)")
    ```

    To check an existing Secret, list its keys without printing the values:

    ```bash
    kubectl get secrets -n <namespace>
    kubectl describe secret cloud-registry-mongodb-credentials -n <namespace>
    ```

3. Download and verify the chart and the image (see [Verifying the chart
   and the image](#verifying-the-chart-and-the-image)), then install the
   verified chart file, and wait for the app:

    ```bash
    helm install cloud-registry ./cloud-registry-1.0.0-rc2.tgz \
      -n <namespace> -f values-prod.yaml
    kubectl rollout status deploy/cloud-registry -n <namespace>
    ```

    Rendering fails if the issuer, the audience or the admin group is
    missing. Without the chart's Ingress, apply your own (see [Exposing the
    API](#exposing-the-api)).

4. Set up the backups, and test a restore once (see [Backups](#backups)).

5. Deploy the front end (see [Front end](#front-end)).

6. Add the service types of the TES network and the central services, in
   admin mode (see [Service types](#service-types)), before announcing the
   registry. The database starts empty: there are no service types,
   services or roles yet.

Admins can also list the registry among its own services, in admin mode,
from the front end's service info page (see [Listing the registry
itself][cr-listing-itself]); nothing changes until they do.

### Front end

The front end ([Cloud Registry UI][cr-ui-repo]) is a web app, served at
<https://registry.elixir-on.cloud/>. Anyone can browse the services in it;
logged-in users register services, edit and delete their own, and share
them with others (access management). Admins, in admin mode, also verify
services, change their identifiers, and approve new service types and the
services that are pending until their type is approved (see the UI's
[user guide][cr-ui-user-guide]).

#### UI version

UI versions follow the registry in major and minor version (see
[Compatibility][cr-ui-compatibility]): **deploy the UI v1.0.0-rc2 with
Cloud Registry 1.0.0rc2**, and upgrade the front end together with the
registry when its minor version changes. Deploy the registry first, then
the front end. Pre-releases may need a newer pre-release of the registry:
the UI 1.0.0-rc2 doesn't work with Cloud Registry 1.0.0rc1, although their
numbers match (see [Upgrading from 1.0.0rc1](#upgrading-from-100rc1)).

**Deploy the signed release image, pinned by its digest**
(`docker.io/elixircloud/cloud-registry-ui:1.0.0-rc2@sha256:<digest>`),
after verifying its signature (see [Verifying the UI
image](#verifying-the-ui-image)). A tag can be moved; the digest can't, so
pods restarted later run the verified image. Don't build the image
yourself, and don't deploy the moving tag `latest`.

Release images are production builds: they don't offer "Copy token to
Dashboard", which only development servers have (see [Copying the access
token][cr-ui-copy-token]). Don't deploy development builds.

#### Verifying the UI image

**Verify the image before every install and upgrade** (see [Verifying
images][cr-ui-verifying-images]). Look up the digest of the release's tag,
then verify that digest, so that what you deploy is what you verified:

```bash
docker buildx imagetools inspect docker.io/elixircloud/cloud-registry-ui:1.0.0-rc2
gh attestation verify oci://docker.io/elixircloud/cloud-registry-ui@sha256:<digest> \
  --repo elixir-cloud-aai/cloud-registry-ui \
  --signer-workflow elixir-cloud-aai/cloud-registry-ui/.github/workflows/release.yml \
  --source-ref refs/tags/v1.0.0-rc2
```

The first command prints the digest (`Digest: sha256:…`). Don't deploy if
the check fails. `--source-ref` checks that the release workflow ran for
the release tag, not for another branch or tag.

#### Registering the front end with LS Login

Register the front end with [LS Login][ls-login] as a service (an OpenID
Connect client) of its own, not shared with Krini or the dashboard (one
client per front end, see [Audience](#audience)):

- **Flow:** authorization code, with a client secret and PKCE (`S256`,
  which LS Login supports); the front end also sends a nonce and checks the
  ID token's issuer, audience and nonce.
- **Redirect URI:** `https://registry.elixir-on.cloud/auth/api/callback`.
  Use a separate client for local development, with
  `http://localhost:3000/auth/api/callback`.
- **Post-logout redirect URI:** `https://registry.elixir-on.cloud/auth/login`,
  the front end's login page. From 1.0.0-rc2, logging out also ends the
  session at LS Login, which sends the browser back there (see [Sessions
  and logout][cr-ui-sessions]).
- **Scopes:** `openid`, `profile`, `email` and `eduperson_entitlement` (see
  [Identity provider](#identity-provider)).

Add the client ID to the registry's audience (see [Audience](#audience)).
Keep the client secret in a secret store, never in a repository or in the
image. Configure only this one login provider (see [Login][cr-ui-login]).

#### Settings

Pass the settings as environment variables when the container starts; for
this deployment:

| Setting | Value |
|---|---|
| `NEXT_PUBLIC_CLOUD_REGISTRY_URL` (required) | `https://elixir-on.cloud/ga4gh/registry/v1` |
| `LOGIN_PROVIDERS` (required) | a JSON list with LS Login, including the client ID and secret (see below) |
| `LOGIN_REDIRECT_URI` (required) | `https://registry.elixir-on.cloud/auth/api/callback` |

The [LS Login example][cr-ui-login] in the UI's documentation shows the format of
`LOGIN_PROVIDERS`, with the scopes above; keep its `scopes`, or the
registry doesn't recognize admins:

```text
LOGIN_PROVIDERS=[{"id": "ls-login", "name": "LS Login", "logo": "/ls-login-grey-wide.jpg", "issuer": "https://login.aai.lifescience-ri.eu/oidc/", "clientId": "<client ID>", "clientSecret": "<client secret>", "scopes": ["openid", "profile", "email", "eduperson_entitlement"]}]
LOGIN_REDIRECT_URI=https://registry.elixir-on.cloud/auth/api/callback
```

The issuer and `LOGIN_REDIRECT_URI` must be `https` URLs: the front end
refuses to start otherwise. It authenticates its token requests with
`client_secret_post`, which LS Login lists in its discovery document, so
there is nothing to set for it.

Two settings of the access dialog are new in 1.0.0-rc2; this deployment
doesn't set them, so their defaults apply (see [Access
dialog][cr-ui-access-dialog]):

- `NEXT_PUBLIC_ACCESS_PAGE_SIZE` (default `5`): the entries per page of the
  tables of the **Manage access** dialog.
- `NEXT_PUBLIC_INVITATION_LABEL_REQUIRED` (default `true`): new invitations
  need a label that says who they are for; `false` makes it optional. Labels
  may name people, and the registry keeps them with the invitations (see
  [Invitations](#invitations)).

The settings `NEXT_PUBLIC_*` reach the browser, so they are public; the
login settings stay on the server. Keep the login settings in a Kubernetes
Secret and pass them with `envFrom` and a `secretRef`; set the settings
`NEXT_PUBLIC_*` in the Deployment's `env` (or a ConfigMap). With Docker, pass
them with `docker run --env-file`, from a file outside any repository
(`NAME=value` per line, values not quoted).

The front end takes the allowed environments and URL schemes of services
from the registry's service info (see [Registry][cr-ui-registry-settings]):
don't set `NEXT_PUBLIC_SERVICE_ENVIRONMENTS` or
`NEXT_PUBLIC_SERVICE_URL_SCHEMES`, which it ignores, with a warning on
start. Nor does it read `LS_LOGIN_URL` or `OIDC_*` (see [Upgrading from
0.6.0](#upgrading-from-060)).

The branding settings are optional, and their defaults are the ELIXIR
On-Cloud logos and the title "Cloud Registry". Logos given as paths must be the default logos in the
image's `public/` folder; give other logos as URLs (see
[Branding][cr-ui-branding]).

Missing or invalid settings stop the container, with a message that names
the setting (see the container's log, e.g., `kubectl logs`). Change
settings by restarting the container, without building the image again.

#### Running the front end

The UI has no Helm chart. Run the image as a Deployment with a Service on
port 3000 (`PORT`; the app listens on all IPv4 interfaces, set
`LISTEN_HOSTNAME`, e.g. to `::`, for IPv6), and route
`registry.elixir-on.cloud` to it with HTTPS: the login cookies are marked
`Secure`, so logging in fails over plain HTTP. Serve it at the address of
`LOGIN_REDIRECT_URI`: logging out is a `POST` that the app accepts only from
that origin (see [Sessions and logout][cr-ui-sessions]). The front end calls
the API from the user's browser, in admin mode with the header
`X-Request-Roles`; the registry accepts requests from any origin and with
any headers by default, so there is nothing to configure for it.

- **Health:** the image's health check (it requests the start page every 30
  seconds) only applies to Docker; Kubernetes ignores it. Give the
  Deployment HTTP probes on `/` and port 3000 instead (the start page
  answers with a redirect; probes count `2xx` and `3xx` as success).
- **Hardening:** run the container with a read-only root file system, as a
  non-root user, and without any capabilities, with an `emptyDir` on
  `/app/.next/cache`. The app runs as the unprivileged user `bun` and
  writes only to that folder, so it needs nothing more, and a compromised
  app can neither change its own code nor gain privileges. The image names
  its user (`bun`) rather than giving its ID, so set the ID (`1000`) too:
  otherwise, the kubelet can't check `runAsNonRoot` and refuses to start
  the container.
- **Replicas:** run 2 replicas, for the same reasons as the registry's (see
  [Replicas](#replicas)). The front end keeps the login state and the
  session in the browser's cookies (the login's state, PKCE verifier and
  nonce while logging in, then the tokens), not in the server, so any pod
  can serve any request, and no sticky sessions are needed.
- **Security headers:** the app sets its own Content Security Policy, with a
  nonce per request. Don't let the ingress or a proxy add a second one:
  browsers enforce both, and one without the nonce blocks the app's
  scripts (see [Registry][cr-ui-registry-settings]). Set
  `Strict-Transport-Security` in the ingress or the proxy: the app doesn't
  send it, as it doesn't know whether it is served over HTTPS (see [Behind a
  reverse proxy][cr-ui-reverse-proxy]).
- **Timeouts:** the app waits 30 seconds for each answer of the registry,
  and fetches of service info take up to 10 seconds (see
  [Timeouts][cr-ui-timeouts]).

For example (with the settings of [Settings](#settings) in the Secret
`cloud-registry-ui-login` and the ConfigMap `cloud-registry-ui-settings`):

```yaml title="deployment-cloud-registry-ui.yaml"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloud-registry-ui
  namespace: <namespace>
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: cloud-registry-ui
  template:
    metadata:
      labels:
        app.kubernetes.io/name: cloud-registry-ui
    spec:
      automountServiceAccountToken: false
      # Spread the pods over nodes, so that a node drain keeps one running
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: cloud-registry-ui
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
      containers:
      - name: cloud-registry-ui
        # The verified release image, pinned by its digest (see "UI version")
        image: docker.io/elixircloud/cloud-registry-ui:1.0.0-rc2@sha256:<digest>
        ports:
        - name: http
          containerPort: 3000
        envFrom:
        - configMapRef:
            name: cloud-registry-ui-settings
        - secretRef:
            name: cloud-registry-ui-login
        securityContext:
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
          capabilities:
            drop: [ALL]
        readinessProbe:
          httpGet:
            path: /
            port: http
        livenessProbe:
          httpGet:
            path: /
            port: http
        volumeMounts:
        - name: next-cache
          mountPath: /app/.next/cache
      volumes:
      - name: next-cache
        emptyDir: {}
```

Users stay logged in as long as their LS Login access token is valid, at
most 12 hours; the front end doesn't refresh tokens. Logging out ends the
session at LS Login too (see [Registering the front end with LS
Login](#registering-the-front-end-with-ls-login)). Logins that are in
progress while the front end is updated may fail once; users then log in
again.

After deploying, open the front end, log in with LS Login and check that
the list of services loads (it is empty after a fresh install); then go on with the [checks](#checks-after-installing)
below, which include logging in as an admin.

## Checks after installing

1. The service info shows version `1.0.0rc2` and the deployment's fields.
   Its registration rules (`registrationRules`) show the recommended
   settings: the environments `["prod", "test"]`, the URL schemes
   `["https"]`, the service types `controlled` (with
   `"maxUnusedServiceTypes": 0`, as only admins add types),
   `"maxServicesPerUser": 20` and the sync of service info
   (`"serviceInfoSync": {"enabled": true, "intervalHours": 24}`):

    ```bash
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/service-info
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/service-info \
      | jq .registrationRules
    ```

2. Reads are public; writes without a token are rejected with `401`:

    ```bash
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services
    curl -s -o /dev/null -w '%{http_code}\n' -X POST \
      https://elixir-on.cloud/ga4gh/registry/v1/services
    ```

3. The app logs the admin group on startup; the line must name the
   `ECP_CLN:ADMIN` group above. It also warns of stored services whose
   environment is not allowed; there should be no such warning:

    ```bash
    kubectl logs deploy/cloud-registry -n <namespace> | grep "mapped to the role 'admin'"
    kubectl logs deploy/cloud-registry -n <namespace> | grep "environments not allowed"
    ```

4. The stored service types are those that admins added (see
   [Installation](#installation)):

    ```bash
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services/types
    ```

5. An admin logs in to the front end and calls `GET /me` (see [Current
   user][cr-current-user]) with their access token, in admin mode (header
   `X-Request-Roles: admin`); the response must contain `"admin": true`.
   Without the header, it contains `"adminAvailable": true` and
   `"admin": false`. If `adminAvailable` is `false`, the token lacks the
   group (check the scopes and the user info, see [Admins](#admins)); if
   the request fails with `401`, the front end's client ID is missing in
   the audience.

    ```bash
    read -rs TOKEN
    printf 'Authorization: Bearer %s\nX-Request-Roles: admin\n' "$TOKEN" \
      | curl -fsS -H @- https://elixir-on.cloud/ga4gh/registry/v1/me
    ```

   In the front end, the admin sees the switch "User mode" / "Admin mode"
   in the top bar (see [Admin mode](#admin-mode)).

6. Register a test service in the front end, then delete it. Import the
   service info of a public service in the registration form (e.g., of a
   TES service to be registered), without registering it: the form fills
   in its values. If the import fails for a service whose service info is
   public, the app's pods can't connect out (see [Network
   policies](#network-policies)). Logged-in users see the notification
   bell in the top bar.

    On the test service, grant a role to a user ID with a slash (e.g.,
    `test/user`), check that **Current Access** lists exactly that ID, and
    remove it: otherwise, a proxy changes encoded slashes (see [Exposing
    the API](#exposing-the-api)).

7. From outside the cluster, `/admin/` doesn't reach the app (`403` or
   `404` from the proxy or the controller, not the app's `401`; see
   [Exposing the API](#exposing-the-api)):

    ```bash
    curl -s -o /dev/null -w '%{http_code}\n' \
      https://elixir-on.cloud/admin/access-control/
    ```

8. The rate limit of writes applies: of 20 quick `POST` requests without a
   token, the first ones get `401` from the app, the rest `429` (or `503`)
   from the ingress. This blocks writes from your address for a minute:

    ```bash
    for i in $(seq 20); do
      curl -s -o /dev/null -w '%{http_code} ' -X POST \
        https://elixir-on.cloud/ga4gh/registry/v1/services
    done; echo
    ```

9. Two pods of the app are ready, preferably on different nodes, and the
   PodDisruptionBudget exists (see [Replicas](#replicas)):

    ```bash
    kubectl get pods -n <namespace> -o wide
    kubectl get pdb -n <namespace>
    ```

10. The app's NetworkPolicy exists, and a pod in the release's namespace
    (not the ingress controller) can't connect to the app (the request
    times out, if the network plugin enforces NetworkPolicies):

    ```bash
    kubectl get networkpolicy -n <namespace>
    kubectl run np-check --rm -it --restart=Never -n <namespace> \
      --image=curlimages/curl -- curl -sS -m 5 http://cloud-registry/ga4gh/registry/v1/service-info
    ```

## Backups

The registry's data (services, their owners and roles, verifications) lives
only in MongoDB's volume, the claim `cloud-registry-mongodb` (see
[Persistence][cr-persistence]). **Back it up daily, to storage that doesn't
fail with the cluster, and test a restore once**:

- **If the storage provider offers volume snapshots, use them** for the
  claim: they need no extra job and no credentials. Schedule them with the
  provider's or the cluster's tools (e.g., a snapshot schedule of the
  storage, or Velero), and check that the snapshots are kept outside the
  cluster's own disks. Whether a snapshot class exists:

    ```bash
    kubectl get volumesnapshotclass
    ```

- **Otherwise, dump the database daily with `mongodump` to storage outside
  the cluster, and keep the dumps for 14 days**, e.g., with a CronJob (see
  below).

### Dumps with a CronJob

*Example*, for an S3-compatible bucket outside the cluster: `mongodump`
writes a compressed archive of the database `serviceStore` as the app user,
then [rclone][rclone] copies it to the bucket and deletes dumps older than 14
days. The bucket's credentials go in a Secret of their own
(`cloud-registry-backup-storage`, with the variables
`RCLONE_CONFIG_OFFSITE_TYPE=s3`, `RCLONE_CONFIG_OFFSITE_PROVIDER`,
`RCLONE_CONFIG_OFFSITE_ENDPOINT`, `RCLONE_CONFIG_OFFSITE_ACCESS_KEY_ID` and
`RCLONE_CONFIG_OFFSITE_SECRET_ACCESS_KEY`), created like the MongoDB Secret,
never in a file in a repository. A lifecycle rule of the bucket that
deletes objects after 14 days can replace the `rclone delete`, so that the
job needs no right to delete. Pin both images (e.g., by digest).

The chart's MongoDB is a single server without an oplog, so a dump is not a
point-in-time copy: writes during the dump (a few seconds for this small
database) may be in some collections and not in others. The app corrects
its service counters on startup after a restore; for exact point-in-time
copies, use volume snapshots.

```yaml title="backup-cloud-registry.yaml"
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cloud-registry-backup
  namespace: <namespace>
spec:
  schedule: "30 2 * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        metadata:
          labels:
            app.kubernetes.io/name: cloud-registry-backup
        spec:
          restartPolicy: Never
          automountServiceAccountToken: false
          securityContext:
            runAsNonRoot: true
            runAsUser: 999
            runAsGroup: 999
          initContainers:
          - name: dump
            image: docker.io/library/mongo:7.0
            env:
            - name: MONGO_USER
              valueFrom:
                secretKeyRef: {name: cloud-registry-mongodb-credentials, key: username}
            - name: MONGO_PASSWORD
              valueFrom:
                secretKeyRef: {name: cloud-registry-mongodb-credentials, key: password}
            command: [sh, -c]
            # The password goes into a config file, not into the arguments
            args:
            - |
              set -e
              printf 'password: "%s"\n' "$MONGO_PASSWORD" > /tmp/mongodump.yaml
              mongodump --config /tmp/mongodump.yaml \
                --host cloud-registry-mongodb --port 27017 \
                --username "$MONGO_USER" --authenticationDatabase serviceStore \
                --db serviceStore --gzip \
                --archive="/backup/cloud-registry-$(date -u +%Y%m%dT%H%M%SZ).archive.gz"
            securityContext:
              readOnlyRootFilesystem: true
              allowPrivilegeEscalation: false
              capabilities:
                drop: [ALL]
            volumeMounts:
            - {name: backup, mountPath: /backup}
            - {name: dump-tmp, mountPath: /tmp}
          containers:
          - name: upload
            image: docker.io/rclone/rclone:<version>
            envFrom:
            - secretRef:
                name: cloud-registry-backup-storage
            env:
            - {name: HOME, value: /tmp}
            command: [sh, -c]
            args:
            - |
              set -e
              rclone copy /backup offsite:<bucket>/cloud-registry/
              rclone delete --min-age 14d offsite:<bucket>/cloud-registry/
            securityContext:
              readOnlyRootFilesystem: true
              allowPrivilegeEscalation: false
              capabilities:
                drop: [ALL]
            volumeMounts:
            - {name: backup, mountPath: /backup}
            - {name: upload-tmp, mountPath: /tmp}
          volumes:
          - {name: backup, emptyDir: {}}
          # Separate scratch volumes: the uploader must not see the dump
          # container's password file
          - {name: dump-tmp, emptyDir: {}}
          - {name: upload-tmp, emptyDir: {}}
---
# MongoDB's NetworkPolicy lets only the app's pods connect: allow the job
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cloud-registry-mongodb-backup
  namespace: <namespace>
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: cloud-registry
      app.kubernetes.io/instance: cloud-registry
      app.kubernetes.io/component: mongodb
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: cloud-registry-backup
    ports:
    - {port: 27017, protocol: TCP}
```

Run it once by hand after applying it, and check that the dump arrives in
the bucket:

```bash
kubectl apply -f backup-cloud-registry.yaml
kubectl create job --from=cronjob/cloud-registry-backup backup-test -n <namespace>
kubectl logs job/backup-test -n <namespace> --all-containers
```

### Testing a restore

A backup that was never restored may not work. **Restore one once**, away
from the production database, and compare it with the live registry; the
numbers differ only by the services registered since, and by pending
services, which the public list leaves out:

- **A dump**, e.g., with Docker on a workstation, from a dump downloaded
  from the bucket:

    ```bash
    docker run -d --name cr-restore-test docker.io/library/mongo:7.0
    docker exec -i cr-restore-test mongorestore --gzip --archive \
      < cloud-registry-<timestamp>.archive.gz
    docker exec cr-restore-test mongosh --quiet \
      --eval 'db.getSiblingDB("serviceStore").services.countDocuments()'
    curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services | jq length
    docker rm -f cr-restore-test
    ```

- **A snapshot:** create a claim from it (`dataSource` of kind
  `VolumeSnapshot`, in the same namespace), start a test pod with
  `docker.io/library/mongo:7.0` on that claim (mounted at `/data/db`, as
  user 999), and count the services in it with `mongosh` as above, with the
  root user's credentials from the Secret (the snapshot holds the users of
  the production database). Delete the pod and the claim afterwards.

For a real restore, stop the app, restore the dump into the release's
MongoDB as the root user, replacing the collections (`--drop`), and start
the app again with the replicas of the values file (or, for a snapshot,
replace the claim with one created from it). The app corrects the counters
of services per user when it starts:

```bash
kubectl scale deploy/cloud-registry --replicas=0 -n <namespace>
# Waits until the app's pods are gone, so that none writes during the restore
kubectl wait --for=delete pod -n <namespace> --timeout=120s \
  -l app.kubernetes.io/instance=cloud-registry,app.kubernetes.io/component=app
# Starts the app again only if the restore succeeded
kubectl exec -i deploy/cloud-registry-mongodb -n <namespace> -- sh -c 'mongorestore \
  -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin --gzip --archive --drop' \
  < cloud-registry-<timestamp>.archive.gz \
  && kubectl scale deploy/cloud-registry --replicas=2 -n <namespace>
```

If the restore fails, keep the app stopped, and restore again (`--drop`
replaces the collections that the archive holds).

## Upgrades

Read the release notes and upgrade steps of the new release, change the
values file if needed, check that the last backup is recent (see
[Backups](#backups)), download and verify the chart and the image of that
release (see [Verifying the chart and the
image](#verifying-the-chart-and-the-image), with the new version), and
upgrade with the verified chart file (see [Upgrades][cr-upgrades]; the
chart file has the chart's version, e.g., `1.0.0-rc2` for the release
`v1.0.0rc2`):

```bash
helm upgrade cloud-registry ./cloud-registry-<chart version>.tgz \
  -n <namespace> -f values-prod.yaml
```

When the registry's minor version changes, upgrade the front end with it,
after the registry, to the UI release of the same minor version (see [UI
version](#ui-version) and the UI's [Updating a
deployment][cr-ui-updating]). Pre-releases can need the front end to be
upgraded with the registry even within a minor version, as 1.0.0-rc2 needed
1.0.0rc2: follow the release notes of both.

Rolling back from 1.0.0rc2 to an earlier version needs the database of that
version, as it was (see [Upgrading from 1.0.0rc1](#upgrading-from-100rc1)).
Don't roll back to an image older than 0.4.0 (e.g., that of the previous
deployment) once admins have verified services: older versions serve the
internal field `_verifiedAt` in GA4GH responses and drop verifications when
services are updated. If a rollback can't be avoided, ask the maintainers
first ([cloud-service@elixir-europe.org][elixir-on-cloud-email]).

## Uninstalling

```bash
helm uninstall cloud-registry -n <namespace>
```

The chart keeps MongoDB's volume (the claim `cloud-registry-mongodb`) and
the data when the release is uninstalled, and a new release of the same name
uses it again; delete the claim by hand to remove the data (see
[Persistence][cr-persistence]), and the PersistentVolume, if its reclaim
policy is `Retain`.

[cr-repo]: <https://github.com/elixir-cloud-aai/cloud-registry>
[cr-release]: <https://github.com/elixir-cloud-aai/cloud-registry/releases/tag/v1.0.0rc2>
[cr-release-notes]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/releases/1.0.0rc2/>
[cr-ui-repo]: <https://github.com/elixir-cloud-aai/cloud-registry-ui>
[cr-ui-registry-settings]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/configuration/#registry>
[cr-ui-admin-mode]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/admins/#admin-mode>
[cr-ui-branding]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/branding/>
[cr-ui-login]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/login/>
[cr-ui-sessions]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/login/#sessions-and-logout>
[cr-ui-copy-token]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/login/#copying-the-access-token>
[cr-deployment-readme]: <https://github.com/elixir-cloud-aai/cloud-registry/blob/v1.0.0rc2/deployment/README.md>
[cr-deployment]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/>
[cr-image]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#image>
[cr-installation]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#installation>
[cr-ingress]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#ingress>
[cr-rate-limits]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#rate-limits>
[cr-tls]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#tls>
[cr-network-policies]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#network-policies>
[cr-upgrades]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#upgrades>
[cr-mongodb-version]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#version>
[cr-authentication]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#authentication>
[cr-persistence]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#persistence>
[cr-upgrading-0.4.0]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/upgrading/#from-versions-before-040>
[cr-configuration]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/configuration/>
[cr-service-info]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/configuration/#service-info>
[cr-access-control]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/access-control/>
[cr-ac-authentication]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/access-control/#authentication>
[cr-admins]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/access-control/#admins>
[cr-group-membership-changes]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/access-control/#group-membership-changes>
[cr-current-user]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/access-control/#current-user>
[cr-operations]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/operations/>
[cr-verifying]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/operations/#verifying-images-and-charts>
[cr-verified-services]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/api/#verified-services>
[cr-upgrading-0.4.0-to-0.5.0]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/upgrading/#from-040>
[cr-chart-0.5.0]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#to-app-version-050>
[cr-chart-0.6.0]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#to-app-version-060>
[cr-upgrading-0.5.0]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/upgrading/#from-050>
[cr-admin-mode]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/access-control/#admin-mode>
[cr-making-admins]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/operations/#making-users-admins>
[cr-service-environments]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/configuration/#service-environments>
[cr-service-types-config]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/configuration/#service-types>
[foca-networkpolicy-peers]: <https://github.com/elixir-cloud-aai/foca/blob/chart-v0.4.0/docs/helm-chart.md#networkpolicy-peers>
[ls-login]: <https://www.lifescience-ri.eu/life-science-login/>
[ls-login-discovery]: <https://login.aai.lifescience-ri.eu/oidc/.well-known/openid-configuration>
[mongodb-server-121912]: <https://jira.mongodb.org/browse/SERVER-121912>
[cr-server]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#server>
[cr-service-url-schemes]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/configuration/#service-url-schemes>
[cr-ui-verifying-images]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/deployment/#verifying-images>
[cr-upgrading]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/upgrading/>
[cr-upgrading-0.6.0]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/upgrading/#from-060>
[cr-upgrading-stored-services]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/upgrading/#stored-services>
[cr-chart-1.0.0rc1]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#to-app-version-100rc1>
[cr-replicas]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#replicas>
[cr-services-per-user]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/configuration/#services-per-user>
[cr-invitations]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/access-control/#invitations>
[cr-ui-release]: <https://github.com/elixir-cloud-aai/cloud-registry-ui/releases/tag/v1.0.0-rc2>
[cr-ui-release-notes]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/releases/1.0.0-rc2/>
[cr-ui-operator-guide]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/>
[cr-ui-user-guide]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/>
[cr-ui-compatibility]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/#compatibility>
[cr-ui-upgrading]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/upgrading/>
[cr-ui-updating]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/upgrading/#updating-a-deployment>
[cr-ui-upgrading-1.0.0-rc1]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/upgrading/#100-rc1>
[cr-ui-upgrading-login]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/upgrading/#login-providers-instead-of-ls_login_url-and-oidc_>
[cr-ui-services-limit]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/registering/#limit-on-registered-services>
[cr-upgrading-1.0.0rc1]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/upgrading/#from-100rc1>
[cr-chart-1.0.0rc2]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#to-app-version-100rc2>
[cr-apps-connections]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/deployment/#the-apps-connections>
[cr-service-info-import]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/configuration/#service-info-import>
[cr-service-info-sync]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/configuration/#service-info-sync>
[cr-notifications]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/api/#notifications>
[cr-ui-upgrading-1.0.0-rc2]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/upgrading/#100-rc2>
[cr-ui-access-dialog]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/configuration/#access-dialog>
[cr-ui-reverse-proxy]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/deployment/#behind-a-reverse-proxy>
[cr-ui-timeouts]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/deployment/#timeouts>
[cr-listing-itself]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/operator-guide/admins/#listing-the-registry-itself>
[gh-cli]: <https://cli.github.com/>
[rclone]: <https://rclone.org/>
