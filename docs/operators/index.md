---
last_verified: 2026-11-17
---

# Architects & Operators: Start Here

This section is primarily for architects, who decide whether to adopt GA4GH
products and patterns, and also for operators, who want their Node safe and
to keep controlling access to their resources. It shows how a Node runs a TES
service in the ELIXIR On-Cloud federation and how it connects to the
deployment's other services.

--8<-- "includes/scope.md"

## What a Node runs

A compute Node offers compute and storage to the federation:

- **Compute:** at least one [GA4GH Task Execution Service][ga4gh-tes] (TES)
  or [Workflow Execution Service][ga4gh-wes] (WES) in front of the Node's
  cluster, which requires access tokens of [LS Login](ls-login.md): e.g.,
  [TESK](services/tesk.md) or [Poiesis](services/poiesis.md) on Kubernetes,
  [Funnel](services/funnel.md) on an HPC or HTC cluster.
- **Storage:** an S3 or FTP server that the TES service uses for the input
  and output files of tasks.
- **Registration:** the Node's services are registered in the
  [Cloud Registry](cloud-registry.md) of the deployment, so that others can
  find them.

A Node can also run the other [services](services/index.md) of the
deployment.

## Who can join

These pages are for compute Nodes. A compute Node joins the federation with
at least one TES or WES service that requires LS Login access tokens, and
registers it in the Cloud Registry. Data nodes, which offer cloud storage or
data through the [GA4GH DRS][ga4gh-drs] API, may join too: their
requirements will follow. [Tutorial: Onboard a Data
Centre](data-centre-onboarding-tutorial.md) shows what they can offer
today. Write to the admins at
[cloud-service@elixir-europe.org][elixir-on-cloud-email] before you start.

## Steps to join

1. Read [Onboarding](onboarding.md).
2. Deploy a TES or WES service and a storage server at your Node.
3. Register your service in the Cloud Registry.
4. Optional: deploy more [services](services/index.md), and connect your own
   services to [LS Login](ls-login.md).

## Pages in this section

| Page | What it covers |
|---|---|
| [Central Addresses](addresses.md) | The addresses of the deployment's central services: portal, Cloud Registry, TES gateway and others. |
| [Onboarding](onboarding.md) | The steps for a Node to join the federation. |
| [Tutorial: Onboard a Node](node-onboarding-tutorial.md) | Step by step, from a cluster to a registered, verified TES service behind the gateway. |
| [Tutorial: Onboard a Data Centre](data-centre-onboarding-tutorial.md) | Step by step, from a cluster to storage for tasks and a registered, verified TRS service. |
| [Cloud Registry](cloud-registry.md) | The settings of the deployment's registry, for the admins who run it. |
| [Using the Cloud Registry](using-cloud-registry.md) | How to look up, register and maintain services, and what the labels mean. |
| [Using the Cloud Registry UI](using-cloud-registry-ui.md) | How to log in to the registry's front end, who has which rights, and whom to ask. |
| [LS Login](ls-login.md) | How to register a service, how LS Login releases groups (facilities, entitlements, 403 checklist), and how to connect JupyterHub, HedgeDoc and MinIO. |
| [Services](services/index.md) | The services of the deployment and their role. |
