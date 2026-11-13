# Tutorial: Onboard a Node

## Synopsis

This tutorial takes a Node from nothing to a TES service that is registered
in the [Cloud Registry][elixir-cloud-registry], verified by its admins and
reachable through the gateway of the ELIXIR On-Cloud. It is for the
operators of compute centres; data centres follow [Tutorial: Onboard a Data
Centre](data-centre-onboarding-tutorial.md). [Onboarding](onboarding.md) is
the short checklist; this page goes through the same steps in detail, with
the commands of each product.

The commands and values on this page come from the docs of each product, at
the versions in the table below. For anything else, follow the linked
product docs: they are the reference, and this page doesn't repeat them.

| Product | Version | Role |
|---|---|---|
| [TESK][tesk] (Helm chart) | 0.3.0, with tesk-api 1.2.0 | TES service for Kubernetes |
| [Poiesis](services/poiesis.md) | 0.2.0 | TES service for Kubernetes (alternative) |
| [Funnel][funnel] | 0.12.3 | TES service for HPC and HTC clusters (alternative) |
| [Cloud Registry][cr-docs] | 1.0.0rc2 | Registry of the services |
| [proTES][protes-docs] | 0.6.0 | Gateway in front of the TES services |
| [Pubgrade-Sidecar][sidecar-docs] | 0.2.0 | Automatic upgrades (optional) |

!!! warning "Under construction"
    The policies for joining the federation are not written down yet: who
    can join, what a Node has to provide, and what the admins check before
    they verify a service. Write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email] before you
    start. The steps below have not yet been tested by an operator who
    didn't write them: please report what doesn't work.

## 1. Prerequisites

You need:

- **A cluster.** For TESK and Poiesis, a Kubernetes or OpenShift cluster
  and [Helm](https://helm.sh/) 3. TESK needs access to one namespace only
  (see [Requirements][tesk-requirements]); Poiesis needs Kubernetes 1.29 or
  later and a PostgreSQL database (see [Prerequisites][poiesis-prereq]). For
  Funnel, an HPC or HTC cluster, e.g., with Slurm (see
  [Funnel](services/funnel.md)).
- **A namespace** of its own for the TES service, e.g., `tesk`.
- **Storage.** A default storage class (TESK creates a temporary volume
  claim for each task with inputs or outputs; `ReadWriteOnce` is enough),
  and a storage backend for the inputs and outputs of tasks, e.g., S3 or FTP
  (see [Deploy storage](onboarding.md#2-deploy-storage)).
- **Ingress and HTTPS.** An Ingress controller (or OpenShift Routes), a host
  name that points to it, and a TLS certificate, e.g., from Let's Encrypt
  with cert-manager. The Cloud Registry of this deployment accepts `https`
  URLs only, and the gateway uses only TES services at public addresses
  that answer without redirects.
- **LS Login.** An [LS Login](ls-login.md) account, and an LS Login client
  that you use to get access tokens for your tests (see [Register your
  service](ls-login.md#register-your-service) and [Get an access
  token](../partners-and-developers/apis.md#2-get-an-access-token)). The
  client must be allowed the scope `eduperson_entitlement`, which releases
  the groups of a user. For the tests, your account must be a member of the
  LS Login group `ECP_CLN` or one of its subgroups (see [step
  3](#3-enable-ls-login-and-ecp_cln-access)): ask the
  [admins][elixir-on-cloud-email].

## 2. Deploy a TES service

Choose the TES service that fits your cluster. What each of them supports
today:

| | TESK | Poiesis | Funnel |
|---|---|---|---|
| Runs on | Kubernetes, OpenShift | Kubernetes 1.29+ | HPC, HTC (e.g., Slurm) |
| Validates LS Login tokens | yes, with gaps (see [step 3](#3-enable-ls-login-and-ecp_cln-access)) | yes (OIDC issuer and audience) | yes (OIDC issuer and audience) |
| Access by membership in `ECP_CLN` | by a claim of the user info | no, any valid token ([generic-issues#21][gi-21]) | no, any valid token ([generic-issues#20][gi-20]) |
| Service info for the registry | set in the chart's values: import | fixed by the code: manual entry ([JaeAeich/poiesis#112][poiesis-112]) | fixed by the code: manual entry ([calypr/funnel#1493][funnel-1493]) |

**Poiesis and Funnel can't enforce the `ECP_CLN` policy yet:** they accept
every valid token of the provider, so anyone with an LS Login account who
gets such a token could run tasks on your cluster. Ask the
[admins][elixir-on-cloud-email] before you join with one of them.

The rest of this step deploys TESK. For the alternatives, follow their own
docs and continue with [step 3](#3-enable-ls-login-and-ecp_cln-access):

- **Poiesis:** [Deploying Poiesis][poiesis-deploy] and the [Helm
  chart][poiesis-chart] of version 0.2.0.
- **Funnel:** the [Slurm guide][funnel-slurm] of version 0.12.3, and the
  notes on [Funnel](services/funnel.md).

### Install TESK

The [deployment guide of TESK][tesk-deployment] covers the installation;
this is the short path. Download chart 0.3.0 from its release, check that
TESK's release workflow built and signed it from the release tag (with the
[GitHub CLI](https://cli.github.com/) and
[cosign](https://docs.sigstore.dev/cosign/system_config/installation/), see
[From a release][tesk-from-release]), and unpack it, as some settings are
files in the chart directory:

```bash
set -e  # stop if a check fails (Bash; in Fish, run the commands one by one)
gh release download v0.3.0 --repo elixir-cloud-aai/TESK --pattern 'tesk-*'
gh attestation verify tesk-0.3.0.tgz --repo elixir-cloud-aai/TESK \
    --signer-workflow elixir-cloud-aai/TESK/.github/workflows/release.yml \
    --source-ref refs/tags/v0.3.0
cosign verify-blob tesk-0.3.0.tgz --bundle tesk-0.3.0.tgz.sigstore.json \
    --certificate-identity https://github.com/elixir-cloud-aai/TESK/.github/workflows/release.yml@refs/tags/v0.3.0 \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com
tar -xzf tesk-0.3.0.tgz  # unpacks the chart into tesk/
```

Write your settings into `my-values.yaml`. For an
Ingress with a certificate of cert-manager (see [Exposing the
API][tesk-exposing]; on OpenShift, use a Route instead, as described
there):

```yaml
hostName: tes.example.org
ingress:
  enabled: true
  className: nginx
  path: /
  # The secret that cert-manager creates; empty switches TLS off
  tlsSecretName: tesk-tls
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-production
```

Set up the storage backend of your Node as described in [Storage
backends][tesk-storage] (e.g., `storage: s3` and the files in
`tesk/s3-config/` of the unpacked chart).

Set the service info in `my-values.yaml`, under `serviceInfo`, before
installing: at least `id` (unique, in reverse domain notation), `name`,
`organization`, `contactUrl` and `environment` (see [Service
info][tesk-service-info]). The registry imports these values in [step
5](#5-register-the-service), and keeps the entry in sync with them, so get
them right first: follow the checklist of [Prepare Your Service
Info](service-info.md#checklist). This deployment accepts only the
environments `prod` and `test`: the chart's default, `dev`, is refused.

```yaml
serviceInfo:
  id: org.example.tes
  name: Example TES
  description: TES of Example for the members of its research groups
  organization:
    name: Example
    url: https://example.org/
  contactUrl: mailto:tes@example.org
  documentationUrl: https://example.org/tes/
  environment: prod
```

**Add the `auth` values of [step 3](#tesk) to `my-values.yaml` before you
install.** With the default, `auth.mode: noauth`, all endpoints are open, so
anyone who reaches the Ingress could run tasks on your cluster. If you can't
set them yet, keep `ingress.enabled: false` until you can.

Install the chart into a namespace of its own. `secrets.yaml` holds
credentials, e.g., of FTP: leave out `-f secrets.yaml` if you need none.

```bash
helm upgrade --install tesk ./tesk \
    --namespace tesk --create-namespace \
    -f my-values.yaml -f secrets.yaml
```

Check the installation:

```bash
helm list -n tesk
kubectl get all -n tesk
kubectl port-forward -n tesk service/tesk-api 8080:8080 &
sleep 2
curl http://localhost:8080/ga4gh/tes/v1/service-info
kill %1  # stop the port forward
```

The service info should show your values. Then check that it is reachable
from outside, without a token:

```bash
curl https://tes.example.org/ga4gh/tes/v1/service-info
```

## 3. Enable LS Login and ECP_CLN access

**The policy of the ELIXIR On-Cloud:** users of a Node's TES service must be
members of the LS Login group `ECP_CLN` or of one of its subgroups. LS Login
releases group memberships as values of the claim `eduperson_entitlement`.
The exact values are being recorded in [generic-issues#46][gi-46]: ask the
[admins][elixir-on-cloud-email] for them rather than guessing them.

**Keep `GET /service-info` public.** The registry can only import and sync
service info that answers without a token (see [Using the Cloud
Registry](using-cloud-registry.md#registering-a-service)).

### TESK

With `auth.mode: auth`, TESK requires an access token for every endpoint
except `GET /service-info`, which stays public by default
(`auth.serviceInfoPublic`). Until the groups of `ECP_CLN` are recorded (see
the gaps below), authorise users by a claim of the user info (see
[Authorisation by a claim][tesk-claim]). Add to `my-values.yaml`, with the
values that the admins give you:

```yaml
auth:
  mode: auth
  # The user info endpoint of LS Login; the default is that of ELIXIR AAI
  userInfoUri: https://login.aai.lifescience-ri.eu/oidc/userinfo
  claim:
    enabled: true
    name: eduperson_entitlement
    values:
      - <the ECP_CLN value(s) from the admins>
```

Users with one of the values may create tasks, which belong to them only,
and list, get and cancel their own tasks. Everyone with one of the values
can run any image with any command on your cluster: read the [security
implications][tesk-api-claim-security] in the docs of tesk-api. Set these
values before the first installation (see [step 2](#install-tesk)); to
change them later, run its `helm upgrade --install` command again.

!!! warning "Gaps"
    - **User info endpoint:** tesk-api validates tokens at the user info
      endpoint of the provider, whose default is the endpoint of ELIXIR
      AAI, `https://login.elixir-czech.org/oidc/userinfo` (see [Token
      validation][tesk-api-token-validation]). From chart 0.3.0,
      `auth.userInfoUri` sets it, as above. Whether tokens of LS Login are
      accepted with it has not been verified for this tutorial.
    - **Group model:** from chart 0.3.0, the chart also sets the prefix and
      suffix that tesk-api expects around group names (`auth.groups`, see
      [LS Login and other providers][tesk-ls-login]). The names of the
      groups of `ECP_CLN` aren't recorded yet ([generic-issues#46][gi-46]).
      Hence the claim above.
    - **Status:** enabling LS Login on the TESK deployments of the ELIXIR
      On-Cloud, and recording a configuration that works, is tracked in
      [generic-issues#35][gi-35] and [generic-issues#50][gi-50]. Check them
      before you start.

### Poiesis

Poiesis 0.2.0 validates OIDC tokens of one issuer, with values under
`auth.oidc.*` of its chart: `issuer` and `audience` are required (see
[Authentication][poiesis-auth]). The issuer of LS Login is
`https://login.aai.lifescience-ri.eu/oidc/`; ask the
[admins][elixir-on-cloud-email] which audience to require. Every user sees
only their own tasks.

!!! warning "Gap"
    Poiesis accepts every valid token of the issuer and audience: it can't
    yet limit access to members of `ECP_CLN`. This is tracked in
    [generic-issues#21][gi-21].

### Funnel

Funnel 0.12.3 validates OIDC tokens with the `Server.OidcAuth` section of
its configuration: `ServiceConfigURL` (for LS Login,
`https://login.aai.lifescience-ri.eu/oidc/.well-known/openid-configuration`)
and the required `RequireAudience`, and `TaskAccess: Owner` limits users to
their own tasks (see [OAuth2][funnel-oauth2]). Ask the
[admins][elixir-on-cloud-email] which audience to require.

!!! warning "Gap"
    Funnel accepts every valid token of the provider: it can't yet limit
    access to members of `ECP_CLN`. This is tracked in
    [generic-issues#20][gi-20].

## 4. Check it with a test task

Get an access token of your LS Login account, with the scope
`eduperson_entitlement` (see [Get an access
token](../partners-and-developers/apis.md#2-get-an-access-token)). Then
create a task, with the example of TESK's [API][tesk-api] docs, and get its
state, with your host name:

```bash
TES=https://tes.example.org/ga4gh/tes/v1
cat > hello.json <<'EOF'
{
  "name": "Hello World",
  "executors": [
    {"image": "alpine", "command": ["echo", "TESK says: Hello World"]}
  ]
}
EOF
read -rs TOKEN   # paste the token; it is not shown or saved in the history
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl -X POST "${TES}/tasks" \
    -H 'Content-Type: application/json' -H @- \
    -d @hello.json
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl "${TES}/tasks/<id>?view=BASIC" -H @-
```

The first request returns the ID of the new task. Repeat the second one
with that ID until the state is `COMPLETE`. The task runs the image
`alpine`, which the cluster must be able to pull. Poiesis and Funnel
implement the same API; [Deploying Poiesis][poiesis-deploy] has a similar
example.

Also check that access is limited:

- Without a token, `POST /tasks` must fail (`401 Unauthorized` with TESK
  and Poiesis).
- With TESK, a token of an account without one of the values must fail with
  `403 Forbidden`.

## 5. Register the service

Register your TES service in the [Cloud Registry][elixir-cloud-registry] by
importing its service info, and keep sync on, so that the entry follows
your service. [Using the Cloud
Registry](using-cloud-registry.md#registering-a-service) describes the
policies of this deployment, and [Using the Cloud Registry
UI](using-cloud-registry-ui.md) how to log in and register in the front end.
In short:

1. Check your service info against the rules of this deployment, as
   described in [Check before you
   import](service-info.md#check-before-you-import).
2. Log in to the [Cloud Registry][elixir-cloud-registry] with LS Login.
3. Import the service info of your service, e.g.,
   `https://tes.example.org/ga4gh/tes/v1/service-info`, check the values,
   and register them, with **Keep this service in sync with its service
   info** ticked. If the values are wrong, correct the service info and
   import again, rather than changing them in the form.
4. If the registry answers that the API type or its version isn't allowed,
   check that your service reports the type exactly as registered: types
   are compared as written, and case variants of registered types aren't
   added. TESK serves the registered type `org.ga4gh` / `tes`. If your
   service implements an API, or a version of it, that isn't registered
   yet, ask the [admins][elixir-on-cloud-email] to add it: only they can
   add types in this deployment.

If your entry shows `out-of-sync`, see [Out-of-sync
reasons](using-cloud-registry.md#out-of-sync-reasons).

!!! warning "Gap: Poiesis and Funnel"
    The service info of Poiesis and Funnel can't be set yet
    ([JaeAeich/poiesis#112][poiesis-112], [calypr/funnel#1493][funnel-1493]):
    Funnel's has the environment `development`, which this deployment
    refuses, and Poiesis's describes the project, not your Node. Register
    them by hand, with sync off, as described in [Manual entry, the
    fallback](service-info.md#manual-entry-the-fallback). Ask the
    [admins][elixir-on-cloud-email] how to proceed, as entries without
    readable service info aren't verified here (see [Verified
    services](using-cloud-registry.md#verified-services)).

## 6. Get verified

Write to [cloud-service@elixir-europe.org][elixir-on-cloud-email] with the
address of your entry, and ask for its verification. Only admins can verify
services; you can't verify your own. What they check is up to this
deployment, e.g., that the service accepts tokens of LS Login (see
[Verified services][cr-verified]).

Verification is kept when sync updates the entry, but changing the URL or
the API type removes it. See [Verified
services](using-cloud-registry.md#verified-services) for what it means.

!!! warning "Under construction"
    The checks for the verification of a TES service are not written down
    yet.

## 7. Get added behind the gateway

[proTES](services/protes.md) is the gateway in front of the Nodes' TES
services: clients send their tasks to proTES, which forwards each task to
one of the TES services it knows. It knows a TES service in one of two ways
(see [TES instances][protes-tes-instances]):

- **Configured:** its admins list your service in the configuration of
  proTES.
- **Discovered:** proTES reads the verified TES services of a Cloud Registry,
  so that a new Node is used once it is registered and verified, without a
  change of the configuration (see [Discovery in a service
  registry][protes-discovery]).

For discovery, proTES uses a service only if all of these hold: it is
verified, with its current URL and API type; it is a TES service of one of
the versions that proTES accepts, and of one of the environments, if the
gateway selects by environment; its URL is an `https` URL; and its host has
public addresses only. Requests to discovered services don't follow
redirects.

proTES never forwards the tokens of its users. It authenticates at TES
services with credentials of its own: an access token of its own client
(`client_credentials`, the default, also for discovered services), HTTP Basic
credentials (`basic`, a transitional mode for TES services that don't accept
tokens yet), or none (see [Credentials of TES
instances][protes-credentials]). Agree with the
[admins][elixir-on-cloud-email] how the gateway authenticates at your
service, and make your service accept it.

Tell the [admins][elixir-on-cloud-email] that your service is ready, then
check that tasks sent through the gateway arrive at your service.

!!! warning "Under construction"
    The configuration of the ELIXIR On-Cloud's proTES (its address, its
    client, the TES services that it uses and how it authenticates at
    them) is tracked in [generic-issues#31][gi-31].

## 8. Optional: automatic upgrades with Pubgrade-Sidecar

[Pubgrade-Sidecar][sidecar-docs] rolls out new releases of a service to its
Kubernetes Deployments when [Pubgrade][pubgrade] notifies it. It runs in the
namespace of the service, and changes only the image tags of the
Deployments that it may update. Install version 0.2.0 into the namespace of
TESK, as described in [Deployment][sidecar-deployment]:

1. Check out the release:

    ```bash
    git clone --depth 1 --branch v0.2.0 https://github.com/elixir-cloud-aai/Pubgrade-Sidecar.git
    cd Pubgrade-Sidecar
    ```

2. Create a Secret with a token of its own for your Node:

    ```bash
    kubectl -n tesk create secret generic pubgrade-sidecar \
      --from-literal=access-token="$(openssl rand -hex 32)"
    ```

3. Write the values, e.g., `my-values.yaml`. `tesk-api` is the Deployment
   of TESK for the release `tesk`:

    ```yaml
    targetDeployments:
      - tesk-api
    accessToken:
      existingSecret: pubgrade-sidecar
    hostName: sidecar.example.org
    # On OpenShift:
    route:
      enabled: true
    # Elsewhere, instead:
    # ingress:
    #   enabled: true
    #   className: nginx
    #   tlsSecretName: sidecar-tls
    ```

4. Install the chart:

    ```bash
    helm install pubgrade-sidecar deployment/ -n tesk -f my-values.yaml
    ```

!!! warning "Gap"
    The central Pubgrade service of the ELIXIR On-Cloud isn't deployed yet
    ([generic-issues#32][gi-32]), so nothing notifies the sidecar so far.
    Until then, upgrade TESK by hand, following the [upgrade
    notes][tesk-upgrading].

## Data centres

A data centre that doesn't run tasks can still join, with storage for the
tasks of the federation or with a TRS service for tools and workflows:
follow [Tutorial: Onboard a Data Centre](data-centre-onboarding-tutorial.md).

[cr-docs]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/>
[cr-verified]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/api/#verified-services>
[funnel-1493]: <https://github.com/calypr/funnel/issues/1493>
[funnel-oauth2]: <https://github.com/calypr/funnel/blob/v0.12.3/docs/security/oauth2.md>
[funnel-slurm]: <https://github.com/calypr/funnel/blob/v0.12.3/docs/compute/slurm.md>
[gi-20]: <https://github.com/elixir-cloud-aai/generic-issues/issues/20>
[gi-21]: <https://github.com/elixir-cloud-aai/generic-issues/issues/21>
[gi-31]: <https://github.com/elixir-cloud-aai/generic-issues/issues/31>
[gi-32]: <https://github.com/elixir-cloud-aai/generic-issues/issues/32>
[gi-35]: <https://github.com/elixir-cloud-aai/generic-issues/issues/35>
[gi-46]: <https://github.com/elixir-cloud-aai/generic-issues/issues/46>
[gi-50]: <https://github.com/elixir-cloud-aai/generic-issues/issues/50>
[poiesis-auth]: <https://poiesis.jaeaeich.com/docs/deploy/authentication.html>
[poiesis-chart]: <https://github.com/JaeAeich/poiesis/tree/v0.2.0/deployment/helm/poiesis>
[poiesis-112]: <https://github.com/JaeAeich/poiesis/issues/112>
[poiesis-deploy]: <https://poiesis.jaeaeich.com/docs/deploy/deploying-poiesis.html>
[poiesis-prereq]: <https://poiesis.jaeaeich.com/docs/deploy/prerequisites.html>
[protes-credentials]: <https://protes.readthedocs.io/en/v0.6.0/access-control/#credentials-of-tes-instances>
[protes-discovery]: <https://protes.readthedocs.io/en/v0.6.0/configuration/#discovery-in-a-service-registry>
[protes-docs]: <https://protes.readthedocs.io/en/v0.6.0/>
[protes-tes-instances]: <https://protes.readthedocs.io/en/v0.6.0/configuration/#tes-instances>
[pubgrade]: <https://github.com/elixir-cloud-aai/Pubgrade>
[sidecar-deployment]: <https://pubgrade.readthedocs.io/en/latest/sidecar/deployment/>
[sidecar-docs]: <https://pubgrade.readthedocs.io/en/latest/sidecar/>
[tesk-api]: <https://tesk.readthedocs.io/en/latest/api/>
[tesk-api-claim-security]: <https://tesk.readthedocs.io/en/latest/tesk-api/access-control/#security-implications>
[tesk-api-token-validation]: <https://tesk.readthedocs.io/en/latest/tesk-api/access-control/#token-validation>
[tesk-claim]: <https://tesk.readthedocs.io/en/latest/deployment/#authorisation-by-a-claim>
[tesk-deployment]: <https://tesk.readthedocs.io/en/latest/deployment/>
[tesk-exposing]: <https://tesk.readthedocs.io/en/latest/deployment/#exposing-the-api>
[tesk-from-release]: <https://tesk.readthedocs.io/en/latest/deployment/#from-a-release>
[tesk-ls-login]: <https://tesk.readthedocs.io/en/latest/deployment/#ls-login-and-other-providers>
[tesk-requirements]: <https://tesk.readthedocs.io/en/latest/deployment/#requirements>
[tesk-service-info]: <https://tesk.readthedocs.io/en/latest/configuration/#service-info-serviceinfo>
[tesk-storage]: <https://tesk.readthedocs.io/en/latest/deployment/#storage-backends>
[tesk-upgrading]: <https://tesk.readthedocs.io/en/latest/upgrading/>
