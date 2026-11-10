# Onboarding

Follow these steps to connect your Node to the ELIXIR On-Cloud federation.
At the end, your cluster is available through the [GA4GH Task Execution
Service][ga4gh-tes] (TES) API, and others can find it in the [Cloud
Registry][elixir-cloud-registry].

You need:

- a Kubernetes cluster, or an HPC or HTC cluster with Slurm
- an LS Login account (see [LS Login](ls-login.md))
- an HTTPS host name for your TES service

!!! warning "Under construction"
    The requirements for a Node to join are not written down yet. Write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email] before you
    start.

## 1. Deploy compute

Choose the TES service that fits your cluster:

| Your cluster | TES service |
|---|---|
| Kubernetes or OpenShift | [TESK](services/tesk.md) |
| Kubernetes | [Poiesis](services/poiesis.md) |
| HPC or HTC (Slurm) | [Funnel](services/funnel.md) |

Follow the product docs that each page links to. When it works,
`GET /ga4gh/tes/v1/tasks` on your TES service returns a list of tasks.

## 2. Deploy storage

Tasks read and write files through a storage server. The ELIXIR On-Cloud
supports two kinds:

- S3: [MinIO][minio]
- FTP: [vsftpd][vsftpd]

Other S3 and FTP servers may work, but nobody has tested them.

### MinIO (S3)

1. Deploy MinIO with the [MinIO documentation][minio-docs-k8s].
2. On OpenShift, you can use the
   [Minio-OpenShift][minio-deploy-openshift-template] template.
3. On Kubernetes, you can also use the CSC [MinIO Helm
   chart](https://github.com/CSCfi/helm-charts/tree/main/charts/minio).
4. Give your TES service the S3 credentials. For TESK, see the `storage`
   value of its chart.

### vsftpd (FTP)

1. Deploy [vsftpd][vsftpd], for example with [this guide][vsftpd-deploy].
2. Require secure FTP: set `ssl_enable=YES`, `force_local_logins_ssl=YES`
   and `force_local_data_ssl=YES`. Clients must then connect with FTP over
   TLS (FTPS).
3. Create one account for the federation. Write to
   [cloud-service@elixir-europe.org][elixir-on-cloud-email] for the user name
   and password to use.

## 3. Register your TES service

1. Open the [Cloud Registry][elixir-cloud-registry] and log in with LS
   Login.
2. Register your TES service. **Import its values from its public service
   info endpoint** in the registration form, and keep sync on, so that the
   entry follows your service (see [Using the Cloud
   Registry](using-cloud-registry.md#registering-a-service)). Check the
   values before registering them:
    - **URL:** the URL of your TES service. It must start with `https`.
    - **Type:** the TES type from the list. Only admins can add types. If it
      is missing, write to
      [cloud-service@elixir-europe.org][elixir-on-cloud-email].
    - **Environment:** `prod` for a production Node, `test` for a test Node.
3. You are now the owner of the entry. You can update or delete it later.
4. Tell the admins about your new TES service:
   [cloud-service@elixir-europe.org][elixir-on-cloud-email].

An admin of the registry verifies the entry. Services such as proTES can use
the verified TES services of a Cloud Registry (see [Discovery in a service
registry](https://protes.readthedocs.io/en/latest/configuration/#discovery-in-a-service-registry)
in the proTES docs). For the registry's API, see the [Cloud Registry
docs](https://cloud-registry.readthedocs.io/en/latest/api/).

For the policies of the registry and what its labels mean, see [Using the
Cloud Registry](using-cloud-registry.md).

!!! warning "Under construction"
    The checks for the verification of a TES service are not written down
    yet. It is also not documented which services of the ELIXIR On-Cloud
    use the verified entries.

## 4. Next steps

- Deploy more [services](services/index.md).
- Connect your own services to [LS Login](ls-login.md).
