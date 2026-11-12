# Prepare Your Service Info

## Synopsis

Every GA4GH service answers `GET /service-info` with what it says about
itself: its identifier, name, API type, organization, contacts and
environment. The [Cloud Registry][elixir-cloud-registry] of the ELIXIR
On-Cloud reads it when you register a service, and again every day to keep
the entry up to date.

**Importing your service's own service info, with sync on, is the way to
register a service here.** This page tells you how to set the service info
so that the import passes the rules of this deployment, how to check it
before you import, and what to do where the service info can't be set yet.
Entering the values by hand is the [fallback](#manual-entry-the-fallback).

For how the import and sync work, see [Using the Cloud
Registry](using-cloud-registry.md#registering-a-service) and the registry's
docs on [Importing service info][cr-import] and [Synced
services][cr-synced].

## The rules of this deployment

The registry publishes the rules that it enforces in its own service info,
under `registrationRules` (see [Registration rules][cr-rules]). Read them
there rather than from this page, as admins can change them:

```bash
curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/service-info \
  | jq .registrationRules
```

At the time of writing, the rules are:

- `environments`: `prod` and `test` only;
- `urlSchemes`: `https` only;
- `serviceTypes`: `controlled`: only admins add API types, so your service's
  type must be one of the registered types. The types are a controlled,
  case-sensitive vocabulary: the admins don't add case variants of
  registered types (e.g., `TES` next to `tes`), so your service must report
  the type exactly as registered.

List the registered types with:

```bash
curl -fsS https://elixir-on.cloud/ga4gh/registry/v1/services/types \
  | jq -c '.[]'
```

## Checklist

**The endpoint:**

- [ ] `GET <base URL>/service-info` answers `200 OK` **without a token**:
  the registry never sends one. With access control on, keep this endpoint
  public.
- [ ] The address is an `https` URL, with a valid certificate for the
  host, and the host has public addresses only.
- [ ] It answers without redirects, within 10 seconds, with at most
  256 KiB.
- [ ] The base URL is the URL of your API, e.g.,
  `https://tes.example.org/ga4gh/tes/v1`: the registry registers the import
  address without `/service-info`.

**The fields** (see [Registrations][cr-registrations] for the limits of
their lengths):

- [ ] `id`: unique and stable, in reverse domain notation, e.g.,
  `org.example.tes`, not the default of your product. The import needs it,
  and sync checks that it stays the same.
- [ ] `name`: a descriptive name, e.g., "Example TES".
- [ ] `description`: what the service offers, and to whom.
- [ ] `type`: `group`, `artifact` and `version` of one of the [registered
  types](#the-rules-of-this-deployment), e.g., `org.ga4gh`, `tes`, `1.1.0`,
  as registered here at the time of writing.
  Types are compared as written, so report the type exactly as registered:
  case variants such as `TES` aren't added. If your service implements an
  API that has no registered type yet, ask the
  [admins][elixir-on-cloud-email] to add it before you import.
- [ ] `organization`: the `name` and `url` of your Node, and no other
  fields.
- [ ] `contactUrl`: where users get support, an HTTP(S) or `mailto:` URL,
  e.g., `mailto:tes@example.org`.
- [ ] `documentationUrl`: documentation for the users of your service.
- [ ] `environment`: one of the [allowed
  environments](#the-rules-of-this-deployment), `prod` for a production
  service, `test` for a test service. The values are case-sensitive.
- [ ] `version`: the version of your service's software.

The import needs `id`, `name`, `type`, `organization` and `version`. It
reads and checks all the fields above, `environment` too, and ignores fields
that aren't on this list (e.g., `createdAt` or `storage`).

## Setting it per product

### TESK

From chart 0.3.0, set the service info in the chart's values, under
`serviceInfo` (see [Service info][tesk-service-info] in the TESK docs). The
chart sets `type` and `version` itself:

```yaml title="my-values.yaml"
serviceInfo:
  id: org.example.tes
  name: Example TES
  description: TES of Example for the members of its research groups
  organization:
    name: Example
    url: https://example.org/
  contactUrl: mailto:tes@example.org
  documentationUrl: https://example.org/tes/
  environment: prod
```

The chart's defaults describe no particular deployment, and its default
environment, `dev`, isn't allowed here. Keep `auth.serviceInfoPublic` at its
default, `true`, so that the endpoint stays public with `auth.mode: auth`.
TESK serves the registered type `org.ga4gh` / `tes`, as the TES
specification requires.

### proTES, TRS-Filer and other FOCA apps

Apps built with [FOCA][foca-service-info] serve the service info from
`service_info.service` of their config, and set `version` from the
installed package. Their base config describes the app, with placeholders:
set `id`, `name`, `description`, `organization`, `contactUrl` and
`environment` in a config overlay.

- **proTES:** in the chart's values, under `config.service_info.service`
  (see [Service info][protes-service-info]).
- **TRS-Filer** 0.5.0: in a config overlay of your own, as the chart has no
  value for it yet (see [Service info][trsfiler-service-info]).

### Funnel, Poiesis and TESP API

**The service info of these products can't be set yet:** their code fixes
the identifier, the organization and other fields for every deployment.
Register them [by hand](#manual-entry-the-fallback) until the linked issues
are resolved.

| Product | What it serves | Import | Issue |
|---|---|---|---|
| [Funnel](services/funnel.md) 0.12.3 | `id: org.ga4gh.funnel`, `environment: development`; only `name` can be set | refused (`environment`) | [calypr/funnel#1493][funnel-1493] |
| [Poiesis](services/poiesis.md) 0.2.0 | `id: org.ga4gh.poiesis` and the project's organization and contacts, no `environment` | can pass, but describes the project, not your Node | [JaeAeich/poiesis#112][poiesis-112] |
| [TESP API][tesp-api] 0.2.0 | `id: fi.muni.cz.tesp`, `environment: dev` | refused (`environment`) | [CESNET/tesp-api#62][tesp-api-62] |

## Check before you import

Check the endpoint without a token, and without following redirects, with
the address of your service:

```bash
SERVICE_INFO=https://tes.example.org/ga4gh/tes/v1/service-info
curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' "$SERVICE_INFO"
curl -fsS "$SERVICE_INFO" | jq '{id, name, description, type,
  organization, contactUrl, documentationUrl, environment, version}'
```

The first command must print `200` and nothing else. Compare the second
with the [checklist](#checklist) and the [rules](#the-rules-of-this-deployment).

## Register by import, and keep sync on

1. Log in to the [Cloud Registry][elixir-cloud-registry] with [LS
   Login](ls-login.md), open **Services** and select **Register Service**.
2. Under **Import from service info**, enter the address of your service
   info and select **Import**. The form takes the values; the **Service
   URL** is the address without `/service-info`.
3. Check the values, and don't change them: change the service info instead,
   and import again. Changed values grey out sync.
4. Keep **Keep this service in sync with its service info** ticked, and
   select **Create Service**.

If the registry can't fetch the service info, the form says so, but not
why: go through the [checklist](#checklist) again. Service info that
doesn't pass the rules is refused, naming the field. See [Importing from
service info][cr-ui-import] in the UI's user guide; scripts use the API, as
described in [Using the Cloud
Registry](using-cloud-registry.md#registering-a-service).

Once sync is on, keep the service info right: the registry applies it every
day, and labels the entry `out-of-sync` if it can't (see [Out-of-sync
reasons](using-cloud-registry.md#out-of-sync-reasons)). Keep `id` and the
API type (`type.group` and `type.artifact`) as they were at the import: if
either changes, sync stops with `identity mismatch`, and the reasons table
says how to recover. If you change them between the import and **Create
Service**, import again.

## Manual entry, the fallback

Enter the values by hand only if the import can't work or doesn't fit:

- the service info **can't be set yet**: [Funnel, Poiesis and TESP
  API](#funnel-poiesis-and-tesp-api);
- the service info **isn't public**;
- a **quick test** with values that differ from the service info.

A manual entry has no sync, so it can drift from what the service says, and
an entry without publicly readable service info is never verified here (see
[Verified services](using-cloud-registry.md#verified-services)). Ask the
[admins][elixir-on-cloud-email] how to proceed with one of the products
above.

To register by hand, fill in the form of **Register Service** with the
values of the [checklist](#checklist) (see [Registering a
service][cr-ui-registering] in the UI's user guide):

- **Service URL:** the base URL of your API, e.g.,
  `https://tes.example.org/ga4gh/tes/v1`.
- **Service Type:** the registered type that your service implements, e.g.,
  `org.ga4gh · tes · 1.1.0`.
- **Environment:** `prod` or `test`.
- **Organization Name** and **Organization URL:** those of your Node, not
  of the product.
- **Service Name**, **Service Version**, **Contact URL**, **Documentation
  URL** and **Description:** as in the checklist.

Leave sync off: with Funnel and TESP API, the first sync would fail, and with
Poiesis, it would replace your values with those of the project. Once your
product lets you set the service info, set it, and turn sync on in the
details of the entry (**Turn sync on**; see [Syncing
services][cr-ui-syncing]).

[cr-import]: <https://cloud-registry.readthedocs.io/en/latest/api/#importing-service-info>
[cr-registrations]: <https://cloud-registry.readthedocs.io/en/latest/api/#registrations>
[cr-rules]: <https://cloud-registry.readthedocs.io/en/latest/api/#registration-rules>
[cr-synced]: <https://cloud-registry.readthedocs.io/en/latest/api/#synced-services>
[cr-ui-import]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/registering/#importing-from-service-info>
[cr-ui-registering]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/registering/#registering-a-service>
[cr-ui-syncing]: <https://cloud-registry-ui.readthedocs.io/en/v1.0.0-rc2/user-guide/syncing/#turning-sync-on-and-off>
[foca-service-info]: <https://foca.readthedocs.io/en/latest/configuration/service-info/>
[funnel-1493]: <https://github.com/calypr/funnel/issues/1493>
[poiesis-112]: <https://github.com/JaeAeich/poiesis/issues/112>
[protes-service-info]: <https://protes.readthedocs.io/en/v0.6.0/configuration/#service-info>
[tesk-service-info]: <https://tesk.readthedocs.io/en/latest/configuration/#service-info-serviceinfo>
[tesp-api]: <https://github.com/CESNET/tesp-api>
[tesp-api-62]: <https://github.com/CESNET/tesp-api/issues/62>
[trsfiler-service-info]: <https://trs-filer.readthedocs.io/en/v0.5.0/configuration/#service-info>
