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
| [Use Krini](krini.md) | Run TES tasks and WES workflows in your browser, at <https://portal.elixir-on.cloud>, on services from the Cloud Registry, and follow your runs. No WES service can be selected there yet. | A web browser, an LS Login account, and compute access to run tasks. |
| [Use the Command Line](cli.md) | Find services in the Cloud Registry, send tasks to a TES service such as proTES, run workflows on a WES service, find workflows in WorkflowHub and look up DRS objects from your terminal with `ga4gh-cli`. | Git and Rust on your computer, and an LS Login access token for services that need a login. |
| [Tutorial: Your First Run in Krini](tutorial-krini.md) | Log in to Krini, run a task and a workflow on demo data, and read the results, step by step. For now, the task part only. | A web browser, an LS Login account, and compute access. |
| [Tutorial: Your First Run from the Command Line](tutorial-cli.md) | Install `ga4gh-cli`, find services, log in with a token, run a task and a workflow on demo data, and read the results, step by step. | Git and Rust on your computer, an LS Login account, and access to a TES and a WES service. |
| [Run Workflows Across Nodes](federated-workflows.md) | Run a Snakemake workflow on the TES services of several Nodes, through the proTES gateway. | A Python environment on your computer, and access to proTES or other TES services. |
| [Sensitive Data in a Secure Processing Environment](spe-with-weskit.md) | Run workflows on sensitive data that you never see, and read the results. | An LS Login account and permission from the operator of the environment. |
| [Crypt4GH with proTES](crypt4gh-with-protes.md) | Process Crypt4GH-encrypted files in a secure container. Needs an unreleased proTES branch until the Crypt4GH plugin for current proTES is released. | Docker and three virtual machines. |
| [Run Interactive Services on TES](../tutorials/tes-services/interactive_services_tes.md) | Run RStudio, JupyterLab or Atlas with OMOP demo data as TES tasks, and open them in your browser. Synthetic data only. | A virtual machine with a public host name and an open HTTPS port, and a TES service. |

## Before you start

1. Get an [LS Login](https://www.lifescience-ri.eu/life-science-login/)
   account. It is the identity provider of the deployment.
2. Become a member of the LS Login group `ECP_CLN:EOC-Compute`, which
   gives access to the compute services of the deployment (see [Apply for
   compute access](#apply-for-compute-access)).
3. Choose a page above and follow its steps.

## Apply for compute access

Members of the LS Login group `ECP_CLN:EOC-Compute` can run tasks and
workflows on the compute services of the deployment, e.g., through Krini or
proTES. To become a member:

1. Open the [application form][eoc-compute-form] and log in with LS Login.
2. Fill in your affiliation and the reason for access, i.e., what you want
   to run. If you aren't a member of the ELIXIR community in LS Login yet,
   the form asks you to apply for that too.
3. Submit the form. You get an e-mail that your application was received.
4. Wait for the e-mail that your application was approved. The admins of
   the deployment review each application by hand.
5. Log out of Krini and log in again: tokens that you got before the
   approval don't carry the group. Other clients carry it only if their
   LS Login registration releases the group; ask their operators.

If you don't hear back within a week, write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email].

!!! warning "Synthetic or public data only"
    Membership gives access to a sandbox for demos and tests. Don't use it
    with personal or other sensitive data.

[eoc-compute-form]: <https://signup.aai.lifescience-ri.eu/registrar/?vo=elixir&group=ECP_CLN%3AEOC-Compute>

## Which TES services you can use

Send your tasks to the TES gateway of the deployment,
[proTES](../operators/services/protes.md), at its TES API
`https://gateway-tes.elixir-on.cloud/ga4gh/tes/v1`, with an LS Login access
token (the old address `protes.rahtiapp.fi` keeps working).
proTES forwards each task to one of the TES services that it knows; for
now, that is only a TESK for tests at CSC, not yet the TES services of the
Nodes (see [proTES](../operators/services/protes.md#in-the-elixir-on-cloud)).
Since 21 November 2026, that TESK requires LS Login tokens, and proTES
doesn't send one of its own yet: until it does, tasks sent to proTES fail.
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

## Where to go next

- The tasks and the API of a TES service: [GA4GH
  TES][ga4gh-tes] and the [proTES docs](https://protes.readthedocs.io/en/latest/).
- Workflow engines that can send their tasks to a TES service: [Run
  workflows through TES](../partners-and-developers/ga4gh-standards.md#run-workflows-through-tes).
- Questions: the [Discussions][elixir-on-cloud-forum] or the [About](../about.md)
  page.
