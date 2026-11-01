# User Stories

These stories show how users and providers work with services and data in
ELIXIR On-Cloud. Use them to plan an integration. The stories about access
to services use [LS Login](https://www.lifescience-ri.eu/life-science-login/),
the identity provider of the deployment.

## Access to services

### Researcher: Access a service

*As a researcher, I can access a cloud service that gives access to research
data, so that I can analyse the data.*

1. The user opens the service and goes to its login page.
2. The service redirects the user to LS Login.
3. The user logs in at their own identity provider, for example their
   institute.
4. LS Login checks whether the user may access the service, through group
   memberships or roles.
5. If so, LS Login redirects the user back to the service and sends the
   service the user's information.

### Service provider: Register a service

*As a service provider, I can register my service, so that external
researchers can log in and use it.*

1. Register the service at LS Login as a relying party (RP). See the [LS Login
   guide](https://www.lifescience-ri.eu/registering-integrating-and-managing-your-service/)
   and the [registration tool (SPREG)](https://services.aai.lifescience-ri.eu/spreg).
2. Configure the service to use LS Login. For examples with JupyterHub and
   HedgeDoc, see [Using LS Login](../operators/ls-login.md).

### Service provider: Control access

*As a service provider, I can define who may use my service, so that only
specific users have access.*

LS Login manages groups and decides access from group memberships. See the
[guide for managing access to a service](https://docs.google.com/document/d/1L9paVp6hAc2iJ_LRD866LPTfBFTo_AVfFxrvtbfQyJU/edit).
In short:

1. In SPREG, turn on "Restrict access to the service based on membership in
   groups".
2. Assign a group to your service as a facility in
   [Perun](https://perun.aai.lifescience-ri.eu/facilities).
3. Add users to the group. See the [instructions for group
   managers](https://docs.google.com/document/d/1-qHT4N_iRrMLZmdIYpU9dXqactg61yFKAT0VFFLoK8c/edit).

### Service provider: Withdraw access

*As a service provider, I can withdraw access, so that a user can no longer
use the service.*

Remove the user from the group. See the [instructions for group
managers](https://docs.google.com/document/d/1-qHT4N_iRrMLZmdIYpU9dXqactg61yFKAT0VFFLoK8c/edit).

## Access to data

### Researcher: Find a data set

*As a researcher, I can find a relevant sensitive data set, so that I can
consider it for my research.*

Data can be reused if it is findable, accessible, interoperable and reusable
(FAIR) and described in a searchable catalogue. The [ELIXIR
RDMkit](https://rdmkit.elixir-europe.org/) has best practices for FAIR data
and data management.

### Researcher: Request access

*As a researcher, I can request access to a sensitive data set, so that I can
use it in my research.*

The researcher files a data access request for the data set in an access
management system, for example [REMS](https://github.com/CSCfi/rems).

### Data controller: Grant access

*As a data controller, I can give a researcher access to a data set, so that
the researcher can work with the data under my usage policies.*

The data controller decides on each request. For human data, the data
subjects usually limit the purposes of use, and the controller checks that a
request fits them. GA4GH helps with two standards:

- The [Data Use Ontology
  (DUO)](https://www.ga4gh.org/product/data-use-ontology-duo/) describes
  consents and requests in a standard way.
- [GA4GH Passports](https://www.ga4gh.org/product/passports/) store approved
  access requests in a standard way. LS Login can act as a passport broker,
  and can give the services the authorisations of a user. See [GA4GH Passport
  support in the Life Science
  AAI](https://docs.google.com/document/d/1QpMgSeDdtPJWujdR9Z93WsTC5I9vyvd4bHjpWcGVnz0/edit).

## Analysis

### Researcher: Run a workflow on an external data set

*As a researcher, I can run a workflow on an external data set in the cloud,
so that I can use the results in my research.*

GA4GH standardises the execution of workflows and their tasks with the
[Workflow Execution Service
(WES)](https://www.ga4gh.org/product/workflow-execution-service-wes/) and
the [Task Execution Service
(TES)](https://www.ga4gh.org/product/task-execution-service-tes/). The user
sends a workflow to a WES service. When the run is complete, the user can use
the results. For the services of the deployment, see [Using the
APIs](apis.md). For a walk-through, see
[Researchers](../researchers/index.md).
