---
hide:
  - feedback
---

# Glossary

This page names the things in the ELIXIR On-Cloud docs and says what each
one is. Every page uses these names and spellings. If a page uses another
name for one of these things, fix the page, not the glossary.

## Names of the deployment

ELIXIR On-Cloud
:   The federated cloud services of the [ELIXIR Compute
    Platform](https://elixir-europe.org/platforms/compute), a [Driver
    Project][ga4gh-dps] of the [GA4GH][ga4gh]. Always write "ELIXIR
    On-Cloud" exactly so, with "ELIXIR" in capitals.

Documentation Hub
:   These docs, at <https://docs.elixir-on.cloud/>.

Federation
:   The Nodes and their services that work together in the deployment.

Node
:   A site that offers compute, and optionally storage, to the federation.
    Write "Node" with a capital N, and "compute Node" for a Node that runs
    TES or WES services. See [Onboarding](operators/onboarding.md).

Data centre
:   A site that offers storage, tools or workflows to the federation but
    doesn't run tasks. See [Tutorial: Onboard a Data
    Centre](operators/data-centre-onboarding-tutorial.md).

Sandbox
:   What the deployment is today: a place for demos and tests, with
    synthetic or public data only. See [Researchers](researchers/index.md).

## Services and standards

TES
:   [GA4GH Task Execution Service][ga4gh-tes] API: it runs one task, for
    example a container.

WES
:   [GA4GH Workflow Execution Service][ga4gh-wes] API: it runs a whole
    workflow.

TRS
:   [GA4GH Tool Registry Service][ga4gh-trs] API: it lists tools and
    workflows.

DRS
:   [GA4GH Data Repository Service][ga4gh-drs] API: it serves data
    objects.

Service Registry
:   [GA4GH Service Registry][ga4gh-service-registry] API: it lists
    services. The Cloud Registry implements it.

Service info
:   What a GA4GH service reports at `GET <base URL>/service-info`: its name,
    type, organization and version. The Cloud Registry imports it. Write
    "service info" in prose and `service-info` for the endpoint. See
    [Prepare Your Service Info](operators/service-info.md).

TESK
:   A TES service for Kubernetes and OpenShift. See
    [TESK](operators/services/tesk.md).

Poiesis
:   A TES service for Kubernetes. See
    [Poiesis](operators/services/poiesis.md).

Funnel
:   A TES service for HPC and HTC clusters, for example with Slurm. See
    [Funnel](operators/services/funnel.md).

WESkit
:   A WES service for Snakemake and Nextflow workflows. See
    [WESkit](operators/services/weskit.md).

proTES, TES gateway
:   A gateway in front of several TES services. "proTES" is the product;
    "TES gateway" is the role it plays in the deployment, at
    `https://gateway-tes.elixir-on.cloud/ga4gh/tes/v1`. See
    [proTES](operators/services/protes.md).

proWES
:   A gateway in front of several WES services. Being revived, not
    deployed yet. See [proWES](operators/services/prowes.md).

DRS-Filer
:   A DRS service. Being revived, not deployed yet. See
    [DRS-Filer](operators/services/drsfiler.md).

TRS-Filer
:   A TRS service. See [TRS-Filer](operators/services/trsfiler.md).

Pubgrade
:   The service that upgrades deployments when new images are published.
    See [Central Addresses](operators/addresses.md).

## Registry and access

Cloud Registry
:   The list of the deployment's services, an implementation of the
    GA4GH Service Registry API, at <https://registry.elixir-on.cloud/>.
    See [Cloud Registry](operators/cloud-registry.md) and [Using the Cloud
    Registry](operators/using-cloud-registry.md).

Cloud Registry UI
:   The front end of the Cloud Registry. See [Using the Cloud Registry
    UI](operators/using-cloud-registry-ui.md).

Verified
:   A label of a registry entry: the registry knows and trusts the original
    registrators of the service. It says nothing about the service as it is
    now. See [Verified
    services](operators/using-cloud-registry.md#verified-services).

Synced
:   A label of a registry entry: whether the registry keeps the entry up to
    date from the service's own service info. See [Using the Cloud
    Registry](operators/using-cloud-registry.md).

LS Login
:   The identity provider of the deployment. Users and services get access
    tokens from it. See [LS Login](operators/ls-login.md).

Perun
:   The system behind LS Login that keeps its users, groups and services.

Facility
:   In Perun, the representation of a client, that is, of a registered
    service. LS Login releases a group only if it is assigned to a resource
    on the facility of the client that requested the token. See [Groups and
    facilities](operators/ls-login.md#groups-and-facilities).

Entitlement
:   A group membership that LS Login releases in the claim
    `eduperson_entitlement`.

EOC-Compute entitlement, compute access
:   Membership of the LS Login group `ECP_CLN:EOC-Compute`. It gives access
    to the compute services of the deployment, such as Krini and proTES. See
    [Apply for compute
    access](researchers/index.md#apply-for-compute-access).

## Tools for users

Krini
:   The web portal of the deployment, at <https://portal.elixir-on.cloud/>.
    It replaces the TES Dashboard. Write "Krini" for the product and
    "portal" only where the address is meant. See [Use
    Krini](researchers/krini.md).

ga4gh-cli
:   The command line tool of the GA4GH SDK. See [Use the Command
    Line](researchers/cli.md).

SPE
:   Secure Processing Environment: a place where researchers run workflows
    on sensitive data that they never see. See [Sensitive Data in a Secure
    Processing Environment](researchers/spe-with-weskit.md).

## Packages

FOCA
:   A Python framework for OpenAPI-based web services. See
    [Packages](partners-and-developers/packages.md).

foca-plugins
:   Plugins for gateway apps built with FOCA, for example proTES.

Cloud Components
:   Web components for the front ends of GA4GH services.
