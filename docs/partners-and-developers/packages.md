# Packages

The services of ELIXIR On-Cloud are built with a few open-source packages.
You can use them to build your own GA4GH services and web apps. This page
says what each package is for. Each package's docs explain how to install and
use it.

| Package | Use it to | Docs |
| --- | --- | --- |
| [FOCA](https://github.com/elixir-cloud-aai/foca) | Build an OpenAPI-based web service in Python, with configuration, token validation, access control, MongoDB, background tasks and a plugin engine for gateway apps | [FOCA docs](https://foca.readthedocs.io/en/latest/) |
| [foca-plugins](https://github.com/elixir-cloud-aai/foca-plugins) | Add plugins to a gateway app built with FOCA (for example, proTES), or write your own | [foca-plugins docs](https://foca-plugins.readthedocs.io/en/latest/) |
| [Cloud Components](https://github.com/elixir-cloud-aai/cloud-components) | Build the front end of a GA4GH service with web components (Lit and TypeScript, with React wrappers) | [Cloud Components docs](https://cloud-components.readthedocs.io/en/latest/) |

## Which package do I need?

- **You build a service that implements a GA4GH API, or a gateway to such
  services.** Start with FOCA. Its [getting
  started](https://foca.readthedocs.io/en/latest/getting-started/) page
  shows the first steps.
- **You run a gateway and want to change how it handles requests.** Install
  plugins from foca-plugins. See [Installing
  plugins](https://foca-plugins.readthedocs.io/en/latest/installing/) and
  [Writing plugins](https://foca-plugins.readthedocs.io/en/latest/writing-plugins/).
- **You build a web app for a GA4GH API.** Use Cloud Components. See
  [Installation](https://cloud-components.readthedocs.io/en/latest/docs/installation/).
  The packages cover the Service Registry, TRS, WES and DRS APIs, and the
  Cloud Registry, TRS-Filer and DRS-Filer.

## Services built with these packages

You can also use the services themselves, or read their code as examples of
FOCA apps. Cloud Registry, proTES and TRS-Filer come with a Docker image and a Helm chart.

- [Cloud Registry](https://cloud-registry.readthedocs.io/en/latest/): a
  GA4GH Service Registry. It has a [web front
  end](https://cloud-registry-ui.readthedocs.io/en/latest/).
- [proTES](https://protes.readthedocs.io/en/latest/): a TES gateway that
  federates TES services.
- [TRS-Filer](https://trs-filer.readthedocs.io/en/latest/): a TRS service for
  tools and workflows.
- [proWES](https://github.com/elixir-cloud-aai/proWES): a WES gateway, and
  [CWL-WES](https://github.com/elixir-cloud-aai/cwl-WES): a WES service for CWL
  workflows. They have no docs site yet: see their READMEs.
- [DRS-Filer](https://github.com/elixir-cloud-aai/drs-filer): a DRS service.
  It has no docs site yet: see its README.

More services are listed in the [GitHub organization][elixir-on-cloud-github].
If you run a service yourself, you can add your deployment to the "Known
deployments" table in the repository of the product.
