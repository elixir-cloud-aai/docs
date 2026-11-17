<!-- markdownlint-disable MD033 MD041 -- logo first; <picture> for dark mode -->
<a href="https://elixir-on.cloud/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/logo_elixir_on_cloud_night.png">
    <img src="docs/images/logo_elixir_on_cloud.png" alt="ELIXIR On-Cloud">
  </picture>
</a>
<!-- markdownlint-enable MD033 MD041 -->

# ELIXIR On-Cloud docs

[![License][badge-license]][badge-url-license]
[![Build_status][badge-build-status]][badge-url-build-status]
[![Docs][badge-docs]][badge-url-docs]

Documentation hub of the [ELIXIR On-Cloud](https://elixir-on.cloud/) federated
deployment: guides for architects and operators, partners and developers,
and researchers. Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
and published on Read the Docs.

**Read the [documentation][docs]** at https://docs.elixir-on.cloud/.

## Development

Install the dependencies in a virtual environment, check the spelling of the
project names, and build the site (warnings fail the build):

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e ".[docs,tests]"
python scripts/check_names.py
mkdocs build --strict
pytest
```

To preview the site while you edit, run `mkdocs serve`.

The strict build checks the links between pages. External links are checked
weekly by the [`Links` workflow](.github/workflows/links.yml), which opens an
issue "Dead links in the docs" when it finds any. To run the same check
locally, install [lychee](https://lychee.cli.rs/) and run:

```sh
lychee --config lychee.toml "docs/**/*.md" "includes/*.md" README.md
```

Set `GITHUB_TOKEN` to any token first to avoid GitHub's rate limits.

The same workflow checks the GA4GH service URLs in the docs (URLs with
`/ga4gh/<api>/v<n>`) and opens an issue "Service URLs in the docs" if a
service is not in the [Cloud Registry](#services-from-the-cloud-registry)
or does not answer `GET <url>/service-info`. Both checks run every Monday
and can be started by hand (`gh workflow run links.yml`); they run only in
the `elixir-cloud-aai` organization, not in forks, and are not required
checks of pull requests. While a problem persists, each run comments on
the open issue. To run the service check locally:

```sh
python scripts/check_services.py
```

It checks `README.md`, `docs` and `includes` (or the paths you pass)
against the registry of `extra.registry_url` in `mkdocs.yml` (or
`--registry URL`); `--output FILE` also writes the report to a file, and
`--help` lists all options. It exits with 0 if all services are fine, 2 if
it found problems and 1 if it could not run (e.g. the registry is down or
the configuration is invalid). Placeholders and local hosts such as
`example.org`, `<HOST>`, `localhost`, in-cluster names and private
addresses are skipped. Configure the rest in
[`service-check.toml`](service-check.toml):

- `skip_hosts`: public third-party services (e.g. WorkflowHub), which are
  not ours to register.
- `unregistered`: our services that pages still name but that are not
  registered yet, each with the reason. They must still answer
  `service-info`. The check reports an entry once the service is
  registered or no page names it any more, so remove it then.

Prefer linking to a service's registry entry over naming its address; a
new address in the docs needs a registry entry first.

### Services from the Cloud Registry

Tables of the deployed services are not written by hand: the hook
[`hooks/registry.py`](hooks/registry.py) fetches them from the
[Cloud Registry](https://elixir-on.cloud/ga4gh/registry/v1/services) on
every build. To add a table to a page, put a marker on a line of its own,
e.g.:

```markdown
<!-- registry:services -->
<!-- registry:services type=tes -->
<!-- registry:services type=tes,wes environment=all -->
```

- `type`: comma-separated service types (the `type.artifact` of the
  service, e.g. `tes`, `wes`); all types if left out.
- `environment`: `prod` (default), `test`, any other environment of the
  registry, or `all`. Services without an environment are listed only
  with `all`.

A marker may be indented, e.g. inside an admonition or a tab; the table
gets the same indentation. Markers in fenced code blocks are left alone,
so pages can show the syntax there (not in indented code blocks, where
markers are replaced).

The table lists name, organization, type and API version, service version,
environment, URL and docs link of each matching service. The registry is
set by `extra.registry_url` in `mkdocs.yml`; forks can point it to their
own registry.

The build needs network access to the registry and **fails** if the
registry can't be reached or answers with something that isn't a list of
services, so the site never shows stale data. This applies to the `Docs`
job of CI and to Read the Docs too: if the registry is down, re-run the
job once it is back. For local builds and previews without network
access, render a warning in place of each table instead:

```sh
DOCS_REGISTRY_OFFLINE=1 mkdocs build --strict
DOCS_REGISTRY_OFFLINE=1 mkdocs serve
```

The hook refuses `DOCS_REGISTRY_OFFLINE=1` in CI and on Read the Docs
(where `CI` or `READTHEDOCS` is set), so published builds always show
the services.

## Contributing

Contributions are welcome! See the organisation's [contributing
guide][contributing] and mind our [code of conduct][code-of-conduct].

## License

The content is licensed under [Creative Commons Zero, version 1.0][license]
(CC0).

[badge-build-status]: <https://github.com/elixir-cloud-aai/docs/actions/workflows/ci.yml/badge.svg?branch=main>
[badge-docs]: <https://img.shields.io/readthedocs/elixir-on-cloud-docs>
[badge-license]: <https://img.shields.io/badge/license-CC0%201.0-blue.svg>
[badge-url-build-status]: <https://github.com/elixir-cloud-aai/docs/actions/workflows/ci.yml?query=branch%3Amain>
[badge-url-docs]: <https://docs.elixir-on.cloud/>
[badge-url-license]: <https://creativecommons.org/publicdomain/zero/1.0/>
[code-of-conduct]: <https://github.com/elixir-cloud-aai/.github/blob/main/CODE_OF_CONDUCT.md>
[contributing]: <https://github.com/elixir-cloud-aai/.github/blob/main/CONTRIBUTING.md>
[docs]: <https://docs.elixir-on.cloud/>
[license]: LICENSE
