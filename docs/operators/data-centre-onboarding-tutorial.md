---
last_verified: null
---

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
| Data objects, through the [DRS API][ga4gh-drs] | [DRS-Filer](services/drsfiler.md) | being revived: not covered here yet |

The commands and values on this page come from the docs of each product,
at the versions in the table below. For anything else, follow the linked
product docs: they are the reference, and this page doesn't repeat them.
Nothing on this page depends on a particular Kubernetes distribution or
hosting provider.

| Product | Version | Role |
|---|---|---|
| [TRS-Filer][trsfiler-docs] (Helm chart) | 0.5.0 | TRS service, with a MongoDB database |
| [Cloud Registry][cr-docs] | 1.0.0rc2 | Registry of the services |

!!! warning "Requirements for data nodes"
    Data nodes may join the federation (see [Who can
    join](index.md#who-can-join)). The requirements for every service of
    the federation are in [Policies and Requirements](policies.md);
    requirements specific to data nodes are not written down yet. What the
    admins check before they verify a service is in [What the admins
    check](using-cloud-registry.md#what-the-admins-check). Write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email] before you
    start. A reader who didn't write the steps below ran step 3 on a local
    test cluster, without an Ingress controller. The restriction of writes
    at a real Ingress controller and the steps that need the registry or
    the admins haven't been tested that way yet: please report what
    doesn't work.

## 1. Prerequisites

You need:

- **A cluster.** A Kubernetes or OpenShift cluster, a namespace of your
  own for TRS-Filer, e.g., `trs`, and the right to create the chart's
  objects in it: Deployments, Services, ConfigMaps, Secrets,
  PersistentVolumeClaims, Jobs, ServiceAccounts, Roles, RoleBindings,
  NetworkPolicies, and Ingresses or OpenShift Routes (the chart's
  configuration Job gets a Role in the namespace, see [Security
  notes][trsfiler-security-notes]).
- **Tools:** `kubectl`, [Helm](https://helm.sh/) 3, `openssl` (for the
  passwords below), `curl`, and, to check the
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
  (see [step 3](#restrict-writes)): your Ingress controller or a proxy in
  front of the cluster must allow `POST`, `PUT` and `DELETE` only from
  trusted clients. On OpenShift, this needs a proxy in front of the
  router, which can only restrict clients, for all methods.
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

!!! note "Storage servers and the registry"
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
(`id: org.example.trs-filer`). The chart on TRS-Filer's default branch
has the value, which comes with the next release
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

2. In `trs-filer/templates/trs-filer-deploy.yaml`, append the overlay's
   path to `FOCA_CONFIG_OVERLAY`, mount it there, and add its volume (see
   [Configuration][trsfiler-configuration]):

    ```yaml
              - name: FOCA_CONFIG_OVERLAY
                value: /etc/trs-filer/config.yaml:/etc/trs-filer/local.yaml
    # ...
            volumeMounts:
            # ...
            - mountPath: /etc/trs-filer/local.yaml
              name: config-local
              subPath: config.yaml
    # ...
          volumes:
          # ...
          - configMap:
              name: app-config-local-{{ .Values.trs_filer.appName }}
            name: config-local
    ```

Keep your copy of the chart, e.g., in version control: you need it for
every upgrade, until the chart takes the service info as a value. Files
mounted with `subPath` aren't updated in running pods: after changing the
overlay, upgrade the release and restart the app (`kubectl rollout restart
deploy/trs-filer -n trs`).

### Restrict writes

TRS-Filer 0.5.0 has no authentication: anyone who reaches the API can
register, replace and delete tools (see [Access
control][trsfiler-access-control]). Tokens for writes are on TRS-Filer's
default branch and come with the next release
([trs-filer#7][trsfiler-7]); the [TRS-Filer of the
deployment](services/trsfiler.md#in-the-elixir-on-cloud) runs such a
development build. Until then:

- Let your Ingress controller or a proxy in front of the cluster allow
  only `GET`, `HEAD` and `OPTIONS` from the public, and the other methods
  only from trusted clients. [Ingress and Route][trsfiler-ingress] has an
  example for ingress-nginx; with other controllers or the Gateway API,
  use their means. The OpenShift router can only allow clients, for all
  methods, which would make the service info private too: on OpenShift,
  restrict writes at a proxy in front of the router.
- Pods in the cluster that reach the app's Service directly bypass the
  restriction. On a cluster shared with workloads that you don't trust,
  let only the Ingress controller or router connect to the app
  (`trs_filer.networkPolicy`, which needs a network plugin that enforces
  NetworkPolicies), and trust forwarded headers only from them
  (`trs_filer.forwardedAllowIps`; see [Network
  policies][trsfiler-network-policies] and [Forwarded
  headers][trsfiler-forwarded-headers]). If your cluster can't enforce
  NetworkPolicies, run TRS-Filer only where no untrusted workload can reach
  it.

The install below exposes the API only once the restriction is in the
values, and checks it before you register the service.

### Install TRS-Filer

Write your values into `my-values.yaml`. Install first without exposing the
API, so that it isn't public before the restriction of writes is in place:

```yaml
host_name: trs.example.org
mongodb:
  auth:
    existingSecret: trs-filer-mongodb-credentials
trs_filer:
  ingress:
    enabled: false
  route:
    enabled: false
```

Install the unpacked chart into the namespace, and check it from your
machine:

```bash
helm upgrade --install trs-filer ./trs-filer -n trs -f my-values.yaml
helm list -n trs
kubectl get pods -n trs
kubectl port-forward -n trs service/trs-filer 8080:8080 &
sleep 2
curl http://localhost:8080/ga4gh/trs/v2/service-info
kill %1  # stop the port forward
```

The pods of TRS-Filer and MongoDB should be running, and the service info
should show your values, with the type `org.ga4gh` / `trs`. If local port
8080 is taken, the port forward fails, and `curl` reaches whatever listens
there: use another local port, e.g., `18080:8080` and
`http://localhost:18080`.

### Expose the API

Add the Ingress, with your restriction of writes, to `my-values.yaml`, e.g.,
with a certificate of cert-manager:

```yaml
trs_filer:
  ingress:
    enabled: true
    className: nginx
    https:
      enabled: true
      # The name of your ClusterIssuer
      issuer: letsencrypt-prod
    # Required: the restriction of writes for your Ingress controller,
    # e.g., the annotations of the example in "Ingress and Route"
    annotations: {}
```

On OpenShift, keep the Ingress disabled and enable the Route instead
(`trs_filer.route.enabled: true`). The OpenShift router can't restrict
methods, only clients, for all methods (see [Ingress and
Route][trsfiler-ingress]): an allow list in `trs_filer.route.annotations`
would also make the service info private, and the registry can't import
it in [step 4](#4-register-the-service). So on OpenShift, restrict writes
at a proxy in front of the router. If a proxy in front of the cluster
restricts writes, configure it first.
Then upgrade the release, and check from an address that isn't trusted
that the service info is public and writes are refused:

```bash
helm upgrade --install trs-filer ./trs-filer -n trs -f my-values.yaml
curl https://trs.example.org/ga4gh/trs/v2/service-info
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
    https://trs.example.org/ga4gh/trs/v2/tools \
    -H 'Content-Type: application/json' -d '{}'
```

The second request must print `403` (or the status that your Ingress
controller or proxy returns for refused requests). If it prints `400` or
`200`, the request reached TRS-Filer: disable the Ingress or Route again
and fix the restriction before you go on.

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

The admins check a TRS entry as any other entry, see [What the admins
check](using-cloud-registry.md#what-the-admins-check).

## 6. Add tools and workflows

Register your tools and workflows from a trusted client, as described in
[Registering tools][trsfiler-registering-tools] in the TRS-Filer docs.
Researchers then find them through the TRS API of your service.

## 7. Keep the registry entry up to date

End every upgrade, move or change of TRS-Filer, e.g., with `helm upgrade`,
with this step: **update the service's Cloud Registry entry, or check that
sync did.** With sync on, check that the entry shows the new version,
labelled `synced`; after a new URL or API type, ask the
[admins][elixir-on-cloud-email] to verify it again. See [After a deployment
or an upgrade](using-cloud-registry.md#after-a-deployment-or-an-upgrade).

## Planned

These are on TRS-Filer's default branch and come with its next release;
this tutorial will then move to that release.

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
