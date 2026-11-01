# Partners and Developers: Start Here

This section is for people who want to integrate the ELIXIR On-Cloud
deployment or its components with their own solutions.

--8<-- "includes/scope.md"

## What you can integrate

- **The deployment's APIs.** The stack implements the GA4GH APIs for
  workflows (WES), tasks (TES), data (DRS), tools (TRS) and services
  (Service Registry). Clients use these APIs as GA4GH defines them.
- **LS Login.** It is the identity provider of the deployment. Your app or
  script gets an access token from it to call the services.
- **The packages behind the services.** You can reuse FOCA, foca-plugins and
  Cloud Components in your own services and web apps.

## Follow these steps

1. Read [GA4GH Standards](ga4gh-standards.md) to see which API versions the
   stack implements and which workflow engines can use them.
2. Follow [Using the APIs](apis.md) to find the services of the deployment,
   get an access token from LS Login and send a request.
3. Read [Packages](packages.md) if you want to build your own service or
   front end with the same tools.
4. [Contribute](#contribute) your changes.

Working with sensitive data, or planning how users reach your service? See
[Sensitive Data](sensitive-data.md) and [User Stories](user-stories.md).

## Contribute

All repositories of the [ELIXIR On-Cloud GitHub
organization][elixir-on-cloud-github] share one [contributing
guide](https://github.com/elixir-cloud-aai/.github/blob/main/CONTRIBUTING.md).
It covers the workflow, the code of conduct and the security policy. The docs
of each package add the steps for its code. See the "Contributing" page of
[FOCA](https://foca.readthedocs.io/en/latest/contributing/),
[foca-plugins](https://foca-plugins.readthedocs.io/en/latest/contributing/),
[Cloud
Registry](https://cloud-registry.readthedocs.io/en/latest/contributing/) and
[Cloud
Components](https://cloud-components.readthedocs.io/en/latest/docs/contributing).

For questions and ideas, use the [Discussions][elixir-on-cloud-forum]. More
ways to get in touch are on the [About](../about.md) page.
