---
last_verified: null
---

# Researchers: Start Here

This section is for researchers who want to try the federated analytics
blueprint of ELIXIR On-Cloud: run analyses on compute that stays at the
ELIXIR Nodes, and keep sensitive data under the control of its owner.

--8<-- "includes/scope.md"

## What you can try

| Page | What you do | What you need |
|---|---|---|
| [Use Krini](krini.md) | Run TES tasks and WES workflows in your browser, on services from the Cloud Registry, and follow your runs. Describes the new version of the portal, which is being rewritten. | A web browser and an LS Login account. |
| [Use the Command Line](cli.md) | Find services in the Cloud Registry, send tasks to a TES service such as proTES, run workflows on a WES service, find workflows in WorkflowHub and look up DRS objects from your terminal with `ga4gh-cli`. | Git and Rust on your computer, and an LS Login access token for services that need a login. |
| [Tutorial: Your First Run in Krini](tutorial-krini.md) | Log in to Krini, run a task and a workflow on demo data, and read the results, step by step. | A web browser, an LS Login account, and access to a TES and a WES service. |
| [Tutorial: Your First Run from the Command Line](tutorial-cli.md) | Install `ga4gh-cli`, find services, log in with a token, run a task and a workflow on demo data, and read the results, step by step. | Git and Rust on your computer, an LS Login account, and access to a TES and a WES service. |
| [Run Workflows Across Nodes](federated-workflows.md) | Run a Snakemake workflow on the TES services of several Nodes, through the proTES gateway. | A Python environment on your computer, and access to proTES or other TES services. |
| [Crypt4GH with proTES](crypt4gh-with-protes.md) | Process Crypt4GH-encrypted files in a secure container. Needs an unreleased proTES branch until the Crypt4GH plugin for current proTES is released. | Docker and three virtual machines. |
| [Run Interactive Services on TES](../tutorials/tes-services/interactive_services_tes.md) | Run RStudio, JupyterLab or Atlas with OMOP demo data as TES tasks, and open them in your browser. Synthetic data only. | A virtual machine with a public host name and an open HTTPS port, and a TES service. |

## Before you start

1. Get an [LS Login](https://www.lifescience-ri.eu/life-science-login/)
   account. It is the identity provider of the deployment.
2. Become a member of the LS Login group `ECP_CLN:EOC-Compute`, which
   gives access to the compute services of the deployment. An application
   form is coming ([generic-issues#49][gi-49]); until then, write to
   [cloud-service@elixir-europe.org][elixir-on-cloud-email].
3. Choose a page above and follow its steps.

## Which TES services you can use

Send your tasks to the TES gateway of the deployment,
[proTES](../operators/services/protes.md), at its TES API
`https://protes.rahtiapp.fi/ga4gh/tes/v1`, with an LS Login access token.
proTES forwards each task to one of the TES services that it knows; for
now, that is only a TESK for tests at CSC, not yet the TES services of the
Nodes (see [proTES](../operators/services/protes.md#in-the-elixir-on-cloud)).
Get the
token from [Krini](krini.md#copy-your-access-token): proTES accepts tokens
that LS Login issued to Krini.

You can also send tasks directly to the TES services of the Nodes that
require LS Login tokens. Find them, and their addresses, in the Cloud
Registry (see [Using the
APIs](../partners-and-developers/apis.md#1-find-the-services)).

!!! warning "Send your token only to services that you trust"
    Anyone who runs a service that receives your token can act as you until
    the token expires. Before you send it to a TES service, check that the
    service is verified in the Cloud Registry (see [Verified
    services](../operators/using-cloud-registry.md#verified-services)) and
    that you trust its operator.

[gi-49]: <https://github.com/elixir-cloud-aai/generic-issues/issues/49>

## Where to go next

- The tasks and the API of a TES service: [GA4GH
  TES][ga4gh-tes] and the [proTES docs](https://protes.readthedocs.io/en/latest/).
- Workflow engines that can send their tasks to a TES service: [Run
  workflows through TES](../partners-and-developers/ga4gh-standards.md#run-workflows-through-tes).
- Questions: the [Discussions][elixir-on-cloud-forum] or the [About](../about.md)
  page.
