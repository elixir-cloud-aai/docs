# Node Operators: Start Here

This section is for admins of ELIXIR Nodes. It shows how a Node runs a TES
service in the ELIXIR On-Cloud federation and how it connects to the
deployment's other services.

--8<-- "includes/scope.md"

## What a Node runs

A Node offers compute and storage to the federation:

- **Compute:** a [GA4GH Task Execution Service][ga4gh-tes] (TES) in front of
  the Node's cluster: [TESK](services/tesk.md) or
  [Poiesis](services/poiesis.md) on Kubernetes, [Funnel](services/funnel.md)
  on an HPC or HTC cluster.
- **Storage:** an S3 or FTP server that the TES service uses for the input
  and output files of tasks.
- **Registration:** the Node's TES service is registered in the
  [Cloud Registry](cloud-registry.md) of the deployment, so that others can
  find it.

A Node can also run the other [services](services/index.md) of the
deployment.

## Steps to join

1. Read [Onboarding](onboarding.md).
2. Deploy a TES service and a storage server at your Node.
3. Register your TES service in the Cloud Registry.
4. Optional: deploy more [services](services/index.md), and connect your own
   services to [LS Login](ls-login.md).

## Pages in this section

| Page | What it covers |
|---|---|
| [Onboarding](onboarding.md) | The steps for a Node to join the federation. |
| [Cloud Registry](cloud-registry.md) | The settings of the deployment's registry, for the admins who run it. |
| [LS Login](ls-login.md) | How to connect JupyterHub, HedgeDoc and MinIO to LS Login. |
| [Services](services/index.md) | The services of the deployment and their role. |

!!! warning "Under construction"
    The policies for joining the federation are not written down yet:
    who can join, what a Node has to provide, and how long it takes to be
    verified. Until then, write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email] before you
    start.
