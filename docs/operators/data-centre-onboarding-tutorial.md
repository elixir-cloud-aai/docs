# Tutorial: Onboard a Data Centre

## Synopsis

This tutorial is for the operators of data centres: sites that offer
storage, tools or workflows to the ELIXIR On-Cloud, but don't run tasks. It
takes such a site from a Kubernetes cluster to a [GA4GH TRS][ga4gh-trs]
service that is registered in the [Cloud Registry][elixir-cloud-registry]
and verified by its admins, and shows how to offer storage to the TES
services of the federation. To run tasks too, follow [Tutorial: Onboard a
Node](node-onboarding-tutorial.md).

What a data centre can offer today, and what is planned:

| Offer | Product | Status |
|---|---|---|
| Storage for the inputs and outputs of tasks | an S3 or FTP server, e.g., [MinIO][minio] or [vsftpd][vsftpd] | available: see [step 2](#2-offer-storage-for-tasks) |
| Tools and workflows, through the TRS API | [TRS-Filer](services/trsfiler.md) 0.5.0 | available, without authentication of writes: see [step 3](#3-deploy-trs-filer) |
| Data objects, through the [DRS API][ga4gh-drs] | [DRS-Filer](services/drsfiler.md) | planned: no release yet, not covered here |

The commands and values on this page come from the docs of each product,
at the versions in the table below. For anything else, follow the linked
product docs: they are the reference, and this page doesn't repeat them.
Nothing on this page depends on a particular Kubernetes distribution or
hosting provider.

| Product | Version | Role |
|---|---|---|
| [TRS-Filer][trsfiler-docs] (Helm chart) | 0.5.0 | TRS service, with a MongoDB database |
| [Cloud Registry][cr-docs] | 1.0.0rc2 | Registry of the services |

!!! warning "Under construction"
    The policies for joining the federation are not written down yet: who
    can join, what a data centre has to provide, and what the admins check
    before they verify a service. Write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email] before you
    start. The steps below have not yet been tested by an operator who
    didn't write them: please report what doesn't work.

## 1. Prerequisites

You need:

- **A cluster.** A Kubernetes or OpenShift cluster, a namespace of your
  own for TRS-Filer, e.g., `trs`, and the right to create Deployments,
  Services, ConfigMaps, Secrets, Jobs, Roles and RoleBindings in it (the
  chart's configuration Job gets a Role in the namespace, see [Security
  notes][trsfiler-security-notes]).
- **Tools:** `kubectl`, [Helm](https://helm.sh/) 3, and, to check the
  chart before you install it, the [GitHub CLI](https://cli.github.com/) and
  [cosign](https://docs.sigstore.dev/cosign/system_config/installation/) 3
  or later.
- **Storage.** A default storage class: MongoDB keeps its data in a
  persistent volume claim (1 GiB by default, see
  [Persistence][trsfiler-persistence]).
- **Ingress and HTTPS.** An Ingress controller (or OpenShift Routes), a host
  name that points to it, e.g., `trs.example.org`, and a TLS certificate,
  e.g., from Let's Encrypt with cert-manager. The Cloud Registry of this
  deployment accepts `https` URLs only, and TRS-Filer advertises
  `https://<host name>` in its responses.
- **A way to restrict writes.** TRS-Filer 0.5.0 has no authentication
  (see [step 3](#restrict-writes)): your Ingress controller, router or a
  proxy in front of the cluster must allow `POST`, `PUT` and `DELETE` only
  from trusted clients.
- **LS Login.** An [LS Login](ls-login.md) account, to log in to the Cloud
  Registry.

## 2. Offer storage for tasks

The TES services of the federation read the inputs of tasks from, and write
their outputs to, S3 or FTP servers. To offer storage:

1. Deploy an S3 or FTP server, as described in [Deploy
   storage](onboarding.md#2-deploy-storage): MinIO for S3, vsftpd for FTP,
   with TLS.
2. Write to [cloud-service@elixir-europe.org][elixir-on-cloud-email]: say
   which TES services may use it, and agree how their operators get the
   credentials. Never send credentials by plain email.
3. The operators of those TES services configure them with your server and
   credentials, e.g., the `storage` value of the [TESK chart][tesk-storage].

!!! warning "Under construction"
    Storage servers aren't registered in the Cloud Registry: there is no
    GA4GH API type for them yet. Which storage servers the TES services of
    the federation use is agreed with the admins.

## 3. Deploy TRS-Filer

[TRS-Filer](services/trsfiler.md) serves tools and workflows through the
TRS API. Its [deployment guide][trsfiler-deployment] covers the installation
in full; this is the path for a data centre of the federation.

### Create the namespace and the database credentials

MongoDB requires credentials, which the chart reads from a Secret that you
create first (see [Authentication][trsfiler-mongodb-auth]), e.g., with
random passwords:

```bash
kubectl create namespace trs
kubectl create secret generic trs-filer-mongodb-credentials -n trs \
    --from-literal=root-username=root \
    --from-literal=root-password="$(openssl rand -hex 24)" \
    --from-literal=username=trs-filer \
    --from-literal=password="$(openssl rand -hex 24)"
```

### Download and check the chart

Download the chart attached to the release, and check that TRS-Filer's
release workflow built and signed it from the release tag (see [Verifying
images and charts][trsfiler-verifying]):

```bash
set -e  # stop if a check fails (Bash; in Fish, run the commands one by one)
gh release download v0.5.0 --repo elixir-cloud-aai/trs-filer \
    --pattern 'trs-filer-0.5.0.tgz*'
gh attestation verify trs-filer-0.5.0.tgz \
    --repo elixir-cloud-aai/trs-filer \
    --signer-workflow elixir-cloud-aai/trs-filer/.github/workflows/release.yml \
    --source-ref refs/tags/v0.5.0
cosign verify-blob trs-filer-0.5.0.tgz \
    --bundle trs-filer-0.5.0.tgz.sigstore.json \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com \
    --certificate-identity https://github.com/elixir-cloud-aai/trs-filer/.github/workflows/release.yml@refs/tags/v0.5.0
tar -xzf trs-filer-0.5.0.tgz  # unpacks the chart into trs-filer/
```

### Set the service info

The registry imports the service info of your TRS service in [step
4](#4-register-the-service), and keeps the entry in sync with it, so set it
before you install: at least `id` (unique, in reverse domain notation),
`name`, `organization`, `contactUrl` and `environment` (`prod` or `test`;
TRS-Filer's default, `dev`, is refused here). Follow the checklist of
[Prepare Your Service Info](service-info.md#checklist).

The chart of TRS-Filer 0.5.0 has no value for the service info yet: without
an overlay of your own, it serves the placeholders of its base config
(`id: org.example.trs-filer`). A value is planned
([trs-filer#135][trsfiler-135]). Until then, add a config overlay to the
unpacked chart, as described in [Configuration][trsfiler-configuration]:

1. Add the ConfigMap `trs-filer/templates/trs-filer-config-local.yaml`,
   with your values:

    ```yaml
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: app-config-local-{{ .Values.trs_filer.appName }}
    data:
      config.yaml: |
        service_info:
          service:
            id: org.example.trs
            name: Example TRS
            description: Tools and workflows of Example
            organization:
              name: Example
              url: https://example.org/
            contactUrl: mailto:trs@example.org
            documentationUrl: https://example.org/trs/
            environment: prod
    ```

2. In `trs-filer/templates/trs-filer-deploy.yaml`, append the overlay to
   `FOCA_CONFIG_OVERLAY` and mount it, as shown in
   [Configuration][trsfiler-configuration].

Keep your copy of the chart, e.g., in version control: you need it for
every upgrade, until the chart takes the service info as a value.

### Restrict writes

TRS-Filer 0.5.0 has no authentication: anyone who reaches the API can
register, replace and delete tools (see [Access
control][trsfiler-access-control]). Tokens for writes are planned
([trs-filer#7][trsfiler-7]). Until then:

- Let your Ingress controller, router or a proxy in front of the cluster
  allow only `GET`, `HEAD` and `OPTIONS` from the public, and the other
  methods only from trusted clients. [Ingress and
  Route][trsfiler-ingress] has examples for ingress-nginx and the
  OpenShift router; with other controllers or the Gateway API, use their
  means.
- If your cluster enforces NetworkPolicies, let only the Ingress controller
  or router connect to the app (`trs_filer.networkPolicy`), and trust
  forwarded headers only from them (`trs_filer.forwardedAllowIps`; see
  [Network policies][trsfiler-network-policies] and [Forwarded
  headers][trsfiler-forwarded-headers]).

### Install TRS-Filer

Write your values into `my-values.yaml`. For an Ingress with a certificate
of cert-manager (on OpenShift, set `trs_filer.ingress.enabled: false` to
get a Route instead, see [Ingress and Route][trsfiler-ingress]):

```yaml
host_name: trs.example.org
mongodb:
  auth:
    existingSecret: trs-filer-mongodb-credentials
trs_filer:
  ingress:
    className: nginx
    https:
      enabled: true
      issuer: letsencrypt-prod
    # The restriction of writes of your Ingress controller, e.g., the
    # annotations of the example in "Ingress and Route"
    annotations: {}
```

Install the unpacked chart into the namespace:

```bash
helm upgrade --install trs-filer ./trs-filer -n trs -f my-values.yaml
```

### Check the installation

```bash
helm list -n trs
kubectl get pods -n trs
curl https://trs.example.org/ga4gh/trs/v2/service-info
```

The pods of TRS-Filer and MongoDB should be running, and the service info
should show your values, with the type `org.ga4gh` / `trs`. Then check that
writes are refused from an address that isn't trusted:

```bash
curl -X POST https://trs.example.org/ga4gh/trs/v2/tools \
    -H 'Content-Type: application/json' -d '{}'
```

This request must fail with `403 Forbidden` (or the status that your
Ingress controller or proxy returns for refused requests). If it answers
with `400 Bad Request` or `200 OK` instead, it reached TRS-Filer: fix the
restriction before you go on.

## 4. Register the service

Register your TRS service in the [Cloud Registry][elixir-cloud-registry] by
importing its service info, and keep sync on, as for a TES service (see
[step 5 of the Node tutorial](node-onboarding-tutorial.md#5-register-the-service)
and [Using the Cloud
Registry](using-cloud-registry.md#registering-a-service)). In short:

1. Check your service info against the rules of this deployment, as
   described in [Check before you
   import](service-info.md#check-before-you-import).
2. Log in to the [Cloud Registry][elixir-cloud-registry] with LS Login.
3. Import `https://trs.example.org/ga4gh/trs/v2/service-info`, check the
   values, and register them, with **Keep this service in sync with its
   service info** ticked.
4. If the registry answers that the API type or its version isn't allowed,
   ask the [admins][elixir-on-cloud-email] to add the TRS type (TRS-Filer
   0.5.0 reports `org.ga4gh` / `trs` / `2.0.1`): only they can add types in
   this deployment.

## 5. Get verified

Write to [cloud-service@elixir-europe.org][elixir-on-cloud-email] with the
address of your entry, and ask for its verification, as described in [step
6 of the Node tutorial](node-onboarding-tutorial.md#6-get-verified).

!!! warning "Under construction"
    The checks for the verification of a TRS service are not written down
    yet.

## 6. Add tools and workflows

Register your tools and workflows from a trusted client, as described in
[Registering tools][trsfiler-registering-tools] in the TRS-Filer docs.
Researchers then find them through the TRS API of your service.

## Planned

- **DRS-Filer**, for data objects through the DRS API, has no release yet.
  This tutorial will cover it once it has one.
- **Writes with tokens** in TRS-Filer ([trs-filer#7][trsfiler-7]), which
  replace the restriction of writes at the Ingress controller or proxy.
- **The service info as a value** of the TRS-Filer chart
  ([trs-filer#135][trsfiler-135]), which replaces the copy of the chart.

[cr-docs]: <https://cloud-registry.readthedocs.io/en/v1.0.0rc2/>
[tesk-storage]: <https://tesk.readthedocs.io/en/latest/deployment/#storage-backends>
[trsfiler-7]: <https://github.com/elixir-cloud-aai/trs-filer/issues/7>
[trsfiler-135]: <https://github.com/elixir-cloud-aai/trs-filer/issues/135>
[trsfiler-access-control]: <https://trs-filer.readthedocs.io/en/v0.5.0/access-control/>
[trsfiler-configuration]: <https://trs-filer.readthedocs.io/en/v0.5.0/deployment/#configuration>
[trsfiler-deployment]: <https://trs-filer.readthedocs.io/en/v0.5.0/deployment/>
[trsfiler-docs]: <https://trs-filer.readthedocs.io/en/v0.5.0/>
[trsfiler-forwarded-headers]: <https://trs-filer.readthedocs.io/en/v0.5.0/deployment/#forwarded-headers>
[trsfiler-ingress]: <https://trs-filer.readthedocs.io/en/v0.5.0/deployment/#ingress-and-route>
[trsfiler-mongodb-auth]: <https://trs-filer.readthedocs.io/en/v0.5.0/deployment/#authentication>
[trsfiler-network-policies]: <https://trs-filer.readthedocs.io/en/v0.5.0/deployment/#network-policies>
[trsfiler-persistence]: <https://trs-filer.readthedocs.io/en/v0.5.0/deployment/#persistence>
[trsfiler-registering-tools]: <https://trs-filer.readthedocs.io/en/v0.5.0/api/#registering-tools>
[trsfiler-security-notes]: <https://trs-filer.readthedocs.io/en/v0.5.0/deployment/#security-notes>
[trsfiler-verifying]: <https://trs-filer.readthedocs.io/en/v0.5.0/operations/#verifying-images-and-charts>
