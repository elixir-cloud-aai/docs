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

### Last verified dates

Pages with operational facts that can't be generated, such as onboarding
steps, access procedures, addresses, versions and contacts, say when
someone last checked those facts against their sources. Their front matter
holds the date, which the page shows at its end (see
[`overrides/partials/content.html`](overrides/partials/content.html)):

```markdown
---
last_verified: 2026-11-17
---
```

- Set the date (`YYYY-MM-DD`) only after you have checked every operational
  fact of the page against its source: the Cloud Registry, the repository
  and docs of the product, or the live service. Fix what is wrong in the
  same pull request.
- `last_verified: null` marks a page with operational facts that nobody has
  verified yet; the page says "Facts not verified yet".
- Which pages carry the key: the operator pages (`docs/operators/`), the
  researchers' start page and guides, the tutorial on interactive services
  (`tutorials/tes-services/`), the API guide
  (`partners-and-developers/apis.md`), the demos index and About. Give new
  pages with operational facts the key too, with `null` until you have
  verified them. This is a convention: the build doesn't require the key.
- Editing a page doesn't change its date, but check every operational fact
  that you add or change against its source, as for any change of the
  docs. A pull request that sets a date verifies the page as it is on
  `main` when it merges: update its branch first, and check what changed.
- Anything else than an unquoted date or `null` fails the build (hook
  [`hooks/last_verified.py`](hooks/last_verified.py)).
- The partial is a copy of Material's: when you upgrade Material, compare
  it with the new release's `partials/content.html`.

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
