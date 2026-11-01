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
   Cloud Registry uses the groups to decide what a user may do. The
   registration of your client at LS Login must allow all these scopes.
   Otherwise, the groups are missing and group-based access fails.
3. Keep the access token that you receive.

The endpoints of LS Login are in its [discovery
document](https://login.aai.lifescience-ri.eu/oidc/.well-known/openid-configuration).

!!! note "Your client ID must be on the list of the Cloud Registry"
    The Cloud Registry accepts tokens only for the client IDs on its list. If
    a write fails with `401 Unauthorized` although the token is valid, the
    operators of the deployment must add your client ID. Write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email]. For other
    services, ask their operators which tokens and clients they accept.

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
  [DRS-Filer](https://github.com/elixir-cloud-aai/drs-filer) (DRS) have no
  separate docs yet: see their READMEs.
- The access rules of the products: [Cloud
  Registry](https://cloud-registry.readthedocs.io/en/latest/access-control/),
  [proTES](https://protes.readthedocs.io/en/latest/access-control/) and
  [TRS-Filer](https://trs-filer.readthedocs.io/en/latest/access-control/).
- How users and service providers work with LS Login: [User
  Stories](user-stories.md).
