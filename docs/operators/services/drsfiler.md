---
last_verified: 2026-11-25
---

# DRS-Filer

!!! warning "Being revived"
    The [DRS-Filer](https://github.com/elixir-cloud-aai/drs-filer)
    repository is being revived since 2026-11-16, after it had been
    archived. It has no release yet, and the ELIXIR On-Cloud doesn't run
    it yet. This page follows with the revival.

[DRS-Filer](https://github.com/elixir-cloud-aai/drs-filer) is a lightweight
implementation of the [GA4GH DRS][ga4gh-drs] API. It serves data objects.

## Role in the deployment

DRS-Filer is the DRS implementation of the ELIXIR On-Cloud project. Data
nodes may offer data through it (see [Who can
join](../index.md#who-can-join)).

## Access control

DRS-Filer has no release yet. On its default branch:

- writes (registering, replacing and deleting objects and access methods,
  and posting the service info) require an access token of an issuer that
  the deployment trusts, and the role `admin`;
- access URLs require login by default; objects and the service info can
  be read by anyone, unless the deployment requires login for all reads;
- owners and maintainers of objects, so that users other than admins can
  register objects, are still missing ([drs-filer#95][drsfiler-95], part
  of [drs-filer#92][drsfiler-92]).

See [Access control][drsfiler-access-control] in the DRS-Filer docs.

## Docs

- [DRS-Filer docs](https://drs-filer.readthedocs.io/)
- [Deployment](https://drs-filer.readthedocs.io/en/latest/deployment/)
- [DRS-Filer repository](https://github.com/elixir-cloud-aai/drs-filer)

[drsfiler-92]: <https://github.com/elixir-cloud-aai/drs-filer/issues/92>
[drsfiler-95]: <https://github.com/elixir-cloud-aai/drs-filer/issues/95>
[drsfiler-access-control]: <https://drs-filer.readthedocs.io/en/latest/access-control/>
