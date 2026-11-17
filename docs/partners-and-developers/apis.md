---
last_verified: null
---

# Using the APIs

This page shows how to send a request to a service of the ELIXIR On-Cloud
deployment. The steps are the same for all services. What each API offers is
in the docs of its product and in the GA4GH specification (see [GA4GH
Standards](ga4gh-standards.md)).

There is no separate test environment for partners: use the services of
the deployment with a test account.

## 1. Find the services

The [Cloud Registry](https://cloud-registry.readthedocs.io/en/latest/) of
the deployment is the source of truth for its services: which services
run, their endpoints, and the versions of the GA4GH APIs that they
implement, which the registry reads from the service info of each service
(`GET /service-info`). These docs don't repeat them. Entries labelled
`synced` follow their service; entries without a label were entered by
hand, and `out-of-sync` entries keep their last values, so both may be
out of date: check the service info of such a service before you rely on
it (see
[Labels](../operators/using-cloud-registry.md#labels)). The registry
implements the [GA4GH Service Registry
API](https://github.com/ga4gh-discovery/ga4gh-service-registry). Anyone can
read it, without a token.

List the registered services:

```bash
curl "https://elixir-on.cloud/ga4gh/registry/v1/services" -H "accept: application/json"
```

Each entry has the URL of the service, its `type` (for example, artifact
`TES` and version `1.0.0`), its `environment` and its organization. Use the
`type` to choose a service and the `url` to call it.

You can also browse the registry in its [web
front end](https://registry.elixir-on.cloud/) and try its API in the [Swagger
UI](https://elixir-on.cloud/ga4gh/registry/v1/ui/). The other operations of
its API are in the [Cloud Registry API
docs](https://cloud-registry.readthedocs.io/en/latest/api/).

## 2. Get an access token

Most operations need an access token. [LS
Login](https://www.lifescience-ri.eu/life-science-login/) is the identity
provider of the deployment: the Cloud Registry accepts its tokens only. A token must be:

- an access token in JWT format, as in [RFC
  9068](https://www.rfc-editor.org/rfc/rfc9068), not an ID token;
- issued by `https://login.aai.lifescience-ri.eu/oidc/`;
- issued to a client that the service accepts (the `aud` claim of the token).

To get one:

1. Register your app or script as a service at LS Login. Follow the [LS Login
   guide](https://www.lifescience-ri.eu/registering-integrating-and-managing-your-service/).
2. Log in with your client through the OpenID Connect flow of LS Login. Ask
   for the scopes `openid profile eduperson_entitlement`. LS Login releases
   the groups of a user only for the scope `eduperson_entitlement`, and the
   Cloud Registry uses the groups to decide what a user may do. The
   registration of your client at LS Login must allow all these scopes.
   Otherwise, the groups are missing and group-based access fails.
3. Keep the access token that you receive.

The endpoints of LS Login are in its [discovery
document](https://login.aai.lifescience-ri.eu/oidc/.well-known/openid-configuration).

### Services that use LS Login

These services of the deployment accept LS Login access tokens:

| Service | What needs a token |
|---|---|
| [proTES](../operators/services/protes.md), the TES gateway | all task requests |
| [TRS-Filer](../operators/services/trsfiler.md) | writes; reads are public |
| Cloud Registry | writes; reads are public |
| [WESkit](https://gitlab.com/one-touch-pipeline/weskit/documentation) at the Berlin Institute of Health (BIH) | as its operators set it up |

Find their addresses in the Cloud Registry (step 1).

!!! note "Your client ID must be accepted by the service"
    A service accepts tokens only for the client IDs on its
    list (the `aud` claim). If a request fails with `401 Unauthorized`
    although the token is valid, the operators of the service must add your
    client ID. Write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email], with your
    client ID and the services that you want to call.

## 3. Send a request

Send the token as a bearer token in the `Authorization` header. This example
asks the Cloud Registry who you are. It works with any valid token that the
registry accepts:

```bash
read -rs TOKEN   # paste the token; it is not shown or saved in the history
printf 'Authorization: Bearer %s\n' "$TOKEN" | curl "https://elixir-on.cloud/ga4gh/registry/v1/me" -H @-
```

The header goes to `curl` through standard input, so the token does not
appear in the command line, the shell history or the process list. The
response shows the user that the token identifies.

To call another service, use the base URL of its API instead. It starts with
the `url` from the registry entry. The path depends on the product (for
example, proTES serves its TES API at `/ga4gh/tes/v1`). The docs of the
product list the operations. A service that requires a token answers a
request without a valid token with `401 Unauthorized`, and a request with a
valid token but without the required role with `403 Forbidden`.

Treat tokens like passwords: never put them in command lines, websites,
tickets or chats.

## Where to go next

- The API docs of the products: [Cloud
  Registry](https://cloud-registry.readthedocs.io/en/latest/api/),
  [proTES](https://protes.readthedocs.io/en/latest/api/) (TES) and
  [TRS-Filer](https://trs-filer.readthedocs.io/en/latest/api/) (TRS).
  [proWES](https://github.com/elixir-cloud-aai/proWES) (WES) and
  [DRS-Filer](https://github.com/elixir-cloud-aai/drs-filer) (DRS) are
  being revived and get docs sites with the revival; until then, see
  their READMEs.
- The access rules of the products: [Cloud
  Registry](https://cloud-registry.readthedocs.io/en/latest/access-control/),
  [proTES](https://protes.readthedocs.io/en/latest/access-control/) and
  [TRS-Filer](https://trs-filer.readthedocs.io/en/latest/access-control/).
- How users and service providers work with LS Login: [User
  Stories](user-stories.md).
