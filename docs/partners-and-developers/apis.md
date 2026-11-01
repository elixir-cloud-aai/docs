# Using the APIs

This page shows how to send a request to a service of the ELIXIR On-Cloud
deployment. The steps are the same for all services. What each API offers is
in the docs of its product and in the GA4GH specification (see [GA4GH
Standards](ga4gh-standards.md)).

!!! warning "Under construction"
    Only the Cloud Registry has a known public endpoint. These are not
    documented yet: the endpoints of the WES, TES, DRS and TRS services of
    the deployment, which of them use LS Login, who may call them, how a
    partner gets its client ID accepted, and a test environment. Until then,
    find the services in the Cloud Registry (step 1) or write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email].

## 1. Find the services

The [Cloud Registry](https://cloud-registry.readthedocs.io/en/latest/) lists
the services of the deployment. It implements the [GA4GH Service Registry
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
   Cloud Registry uses the groups to decide what a user may do.
3. Keep the access token that you receive.

The endpoints of LS Login are in its [discovery
document](https://login.aai.lifescience-ri.eu/oidc/.well-known/openid-configuration).

!!! note "Your client ID must be on the service's list"
    A service accepts tokens only for the client IDs on its list. If a request
    fails with `401 Unauthorized` although the token is valid, the operators
    of the service must add your client ID. Write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email] and say which
    service you want to call.

## 3. Send a request

Send the token as a bearer token in the `Authorization` header. For example,
to list your tasks at a TES service:

```bash
curl "<API base URL>/tasks" -H "Authorization: Bearer <token>"
```

Replace `<API base URL>` with the base URL of the service's API. It starts
with the `url` from the registry entry. The path depends on the product (for
example, proTES serves its TES API at `/ga4gh/tes/v1`). Its docs list the
operations. A request without a valid token gets `401
Unauthorized`. A valid token without the required role gets `403 Forbidden`.

Treat tokens like passwords: never paste them into websites, tickets or chats.

## Where to go next

- The API docs of the products: [Cloud
  Registry](https://cloud-registry.readthedocs.io/en/latest/api/),
  [proTES](https://protes.readthedocs.io/en/latest/api/) (TES) and
  [TRS-Filer](https://trs-filer.readthedocs.io/en/latest/api/) (TRS).
  [proWES](https://github.com/elixir-cloud-aai/proWES) (WES) and
  [DRS-Filer](https://github.com/elixir-cloud-aai/drs-filer) (DRS) have no
  separate docs yet: see their READMEs.
- The access rules of the products: [Cloud
  Registry](https://cloud-registry.readthedocs.io/en/latest/access-control/),
  [proTES](https://protes.readthedocs.io/en/latest/access-control/) and
  [TRS-Filer](https://trs-filer.readthedocs.io/en/latest/access-control/).
- How users and service providers work with LS Login: [User
  Stories](user-stories.md).
