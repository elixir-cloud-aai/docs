# NVFlare Testbed

The [NVFlare on WES and TES testbed][repo] runs a federated learning job
with [NVIDIA FLARE](https://github.com/NVIDIA/NVFlare) through a [GA4GH
WES][ga4gh-wes], with one [GA4GH TES][ga4gh-tes] task per site for the
learning clients. The sites train a model on their own data, and the
federated model beats the models trained at either site alone. The testbed
also evaluates the ways to do this, and lists the shortcuts it takes.

!!! warning "Local runs only"
    So far, the testbed has run on one computer only, with two local
    [Funnel](../operators/services/funnel.md) instances as the sites, a thin
    WES of its own and a small synthetic test set, and without authentication.
    Never use it in production or with real data. See the testbed's
    [shortcuts][docs-shortcuts].

## What you need

- Docker with Compose, on Linux.
- About 1 GB of disk for the images, and 3 GB more for the run through
  proTES.
- Nothing else: no Python on your computer, no free ports, no account.

The Funnel containers get the Docker socket of your computer, to start the
containers of the tasks. Access to the Docker socket amounts to full control
of the computer, so run the testbed in a virtual machine or on a Docker host
that you can throw away, and read the repository's
[`compose.yaml`](https://github.com/elixir-cloud-aai/nvflare-wes-testbed/blob/dev/compose.yaml)
before you start.

## Steps

1. Clone the repository, build the images and run one WES run:

    ```sh
    git clone https://github.com/elixir-cloud-aai/nvflare-wes-testbed.git
    cd nvflare-wes-testbed
    docker compose --profile test build
    docker compose --profile test run --rm e2e
    ```

2. Check the output. It ends with `8/8 checks passed`: one WES run, with one
   TES task per site, and a federated model that beats the models of the
   single sites.
3. Remove the containers:

    ```sh
    docker compose --profile test down -v
    ```

The repository's CI runs this and most other tests on every change.

## Through proTES

To send the tasks through the [proTES](../operators/services/protes.md)
gateway, with each task pinned to the TES of its site, add the overlay
`compose.protes.yaml`. The first build takes a few minutes, as it builds
proTES from its repository:

```sh
docker compose -f compose.yaml -f compose.protes.yaml --profile test build
docker compose -f compose.yaml -f compose.protes.yaml --profile test run --rm e2e
docker compose -f compose.yaml -f compose.protes.yaml --profile test down -v
```

It ends with `10/10 checks passed`. See test [T4][docs-t4].

## Where to go next

- All tests, and the results of the local runs: [Tests][docs-tests].
- The options that were evaluated, and the recommendation:
  [Options][docs-options].
- To run the testbed on real sites, or as a Node operator: [Real
  sites][docs-real-sites].

[docs-options]: <https://nvflare-wes-testbed.readthedocs.io/en/latest/testbed/options/>
[docs-real-sites]: <https://nvflare-wes-testbed.readthedocs.io/en/latest/setup/real-sites/>
[docs-shortcuts]: <https://nvflare-wes-testbed.readthedocs.io/en/latest/testbed/shortcuts/>
[docs-t4]: <https://nvflare-wes-testbed.readthedocs.io/en/latest/tests/t4-protes/>
[docs-tests]: <https://nvflare-wes-testbed.readthedocs.io/en/latest/tests/>
[repo]: <https://github.com/elixir-cloud-aai/nvflare-wes-testbed>
