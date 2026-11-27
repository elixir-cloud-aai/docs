# NVFlare Testbed

The [NVFlare on WES and TES testbed][repo] runs a federated learning job
with [NVIDIA FLARE](https://github.com/NVIDIA/NVFlare) through a [GA4GH
WES][ga4gh-wes], with one [GA4GH TES][ga4gh-tes] task per site for the
learning clients. The sites train a model on their own data, and the
federated model beats the models trained at either site alone. The testbed
also evaluates the ways to do this, and lists the shortcuts it takes.

## Status

The testbed has run on two Nodes. On 2026-11-24, run `ae7742f2` trained the
model over the TESK of the FI Node, on Rahti at CSC, and the TESK of the CZ
Node, at CERIT-SC. Both TES checked the LS Login access token that came with
each task. The run ended `COMPLETE`, and the federated model reached a
holdout accuracy of 0.975, the same as in the testbed's simulator. What ran,
the evidence, and what it does and doesn't show are in the testbed's
[Report][docs-report]; the raw rows are in [Results][docs-results].

[Release 0.1.0][release], of the same day, brings the testbed as it ran: the
thin WES with the FL server beside it, the client and probe tasks, a Helm
chart for the hub, and the synthetic test set. Its image, for all
participants, is `docker.io/elixircloud/nvflare-wes-testbed:0.1.0` (see the
[release notes][docs-release]).

!!! warning "A sandbox, never for production or real data"
    Both TES of the run on two Nodes are run by the testbed's maintainers,
    both are TESK, and the model and the data are toys. The testbed takes
    every shortcut it can: see its [Limitations][docs-limitations] and
    [shortcuts][docs-shortcuts]. Use synthetic or public data only.

## Try it on your computer

The quick start runs the whole testbed on one computer, with two local
[Funnel](../operators/services/funnel.md) instances as the sites. It needs
Docker with Compose, on Linux, and nothing else: no Python, no free ports,
no account. Follow the [quick start of the README][repo-quick-start]; the
[installation guide][docs-installation] lists the requirements.

The Funnel containers get the Docker socket of your computer, to start the
containers of the tasks. Access to the Docker socket amounts to full control
of the computer, so run the testbed in a virtual machine or on a Docker host
that you can throw away, and read the repository's
[`compose.yaml`](https://github.com/elixir-cloud-aai/nvflare-wes-testbed/blob/v0.1.0/compose.yaml)
before you start.

To send the tasks through the [proTES](../operators/services/protes.md)
gateway, with each task pinned to the TES of its site, see test
[T4][docs-t4]. The repository's CI runs the quick start and most other
tests on every change.

## Where to go next

- All tests, and their results: [Tests][docs-tests].
- The options that were evaluated, and the recommendation:
  [Options][docs-options].
- To run the testbed on real sites, or to take part as a Node operator:
  [Real sites][docs-real-sites].

[docs-installation]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/setup/installation/>
[docs-limitations]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/outcomes/report/#limitations>
[docs-options]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/testbed/options/>
[docs-real-sites]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/setup/real-sites/>
[docs-release]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/releases/0.1.0/>
[docs-report]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/outcomes/report/>
[docs-results]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/outcomes/results/>
[docs-shortcuts]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/testbed/shortcuts/>
[docs-t4]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/tests/t4-protes/>
[docs-tests]: <https://nvflare-wes-testbed.readthedocs.io/en/stable/tests/>
[release]: <https://github.com/elixir-cloud-aai/nvflare-wes-testbed/releases/tag/v0.1.0>
[repo]: <https://github.com/elixir-cloud-aai/nvflare-wes-testbed>
[repo-quick-start]: <https://github.com/elixir-cloud-aai/nvflare-wes-testbed/blob/v0.1.0/README.md#quick-start>
