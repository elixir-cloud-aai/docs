# Researchers: Start Here

This section is for researchers who want to try the federated analytics
blueprint of ELIXIR On-Cloud: run analyses on compute that stays at the
ELIXIR Nodes, and keep sensitive data under the control of its owner.

--8<-- "includes/scope.md"

## What you can try

| Page | What you do | What you need |
|---|---|---|
| [Use Krini](krini.md) | Run TES tasks and WES workflows in your browser, on services from the Cloud Registry, and follow your runs. Describes the new version of the portal, which is being rewritten. | A web browser and an LS Login account. |
| [Use the Command Line](cli.md) | Find services in the Cloud Registry, send tasks to a TES service and look up DRS objects from your terminal with `ga4gh-cli`. Doesn't support tokens or WES yet. | Git and Rust on your computer, and a service that you can call without a token. |
| [Run Workflows Across Nodes](federated-workflows.md) | Run a Snakemake workflow on the TES services of several Nodes, through the proTES gateway. | A Python environment on your computer, and the addresses of TES services. |
| [Sensitive Data in a Secure Processing Environment](spe-with-weskit.md) | Run workflows on sensitive data that you never see, and read the results. | An LS Login account and permission from the operator of the environment. |
| [Crypt4GH with proTES](crypt4gh-with-protes.md) | Process Crypt4GH-encrypted files in a secure container. Needs proTES 0.3.0 or earlier. | Docker and three virtual machines. |
| [Run Interactive Services on TES](../tutorials/tes-services/interactive_services_tes.md) | Run RStudio, JupyterLab or Atlas with OMOP demo data as TES tasks, and open them in your browser. Synthetic data only. | A virtual machine with a public host name and an open HTTPS port, and a TES service. |

## Before you start

1. Get an [LS Login](https://www.lifescience-ri.eu/life-science-login/)
   account. It is the identity provider of the deployment.
2. Find the TES services that you can use. [Using the
   APIs](../partners-and-developers/apis.md#1-find-the-services) shows how
   to list them in the Cloud Registry.
3. Choose a page above and follow its steps.

!!! warning "Under construction"
    The deployment does not publish the addresses of its TES services for
    researchers yet, and it is not documented how a researcher gets access
    to them. Until then, write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email] to ask for
    services that you can use.

## Where to go next

- The tasks and the API of a TES service: [GA4GH
  TES][ga4gh-tes] and the [proTES docs](https://protes.readthedocs.io/en/latest/).
- Workflow engines that can send their tasks to a TES service: [Run
  workflows through TES](../partners-and-developers/ga4gh-standards.md#run-workflows-through-tes).
- Questions: the [Discussions][elixir-on-cloud-forum] or the [About](../about.md)
  page.
