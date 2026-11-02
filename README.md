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
deployment: guides for node operators, partners and developers, and
researchers. Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
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
