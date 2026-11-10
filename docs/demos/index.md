# Demos: Start Here

This section lists the demos and test beds of ELIXIR On-Cloud: what each one
shows, whether it works with the current products, and how to run the ones
that do. Each demo lives in its own repository, with its own instructions;
the pages here say what to expect and where to start.

## Status

Each demo has one of these states:

- **Current:** works as its repository describes, with the products as they
  are today.
- **Outdated:** still useful, but built for older versions of the products.
  Its page here lists what differs today and how to work around it.
- **Retired:** kept for the record only. It is not maintained, and depends on
  services or versions that no longer exist. Don't build on it.

## Overview

| Demo | Status | What it shows | Instructions |
|---|---|---|---|
| [Token exchange testbed][repo-txf] | Current | Per-hop OAuth 2.0 token exchange with LS Login along a chain of services, from a front end through a WES and the proTES gateway to TES nodes. Runs on your computer against a local mock of LS Login. | [Token Exchange Testbed](token-exchange-testbed.md) |
| [NVFlare on WES and TES testbed][repo-nvflare] | Current | A federated learning job with NVIDIA FLARE, started through GA4GH WES, with one GA4GH TES task per site, also through proTES. Runs on your computer with two local Funnel instances and synthetic data. | [NVFlare Testbed](nvflare-wes-testbed.md) |
| [GA4GH SDK upgrade][repo-sdk] | Current | Plan and guide of a BioHackathon Europe 2026 project. Its goal: the command line tool of the GA4GH SDK sends tasks to proTES with an LS Login token. The tool doesn't send tokens yet, so it can only use services that need none; nothing to run beyond building it. | [Use the Command Line](../researchers/cli.md) and the [project docs][docs-sdk] |
| [Hybrid cloud via TES][repo-hybrid] (`demo-tes-hybrid-cloud`) | Outdated | A Snakemake workflow on the TES services of several Nodes, one after the other, and then on all of them through proTES. | [Run Workflows Across Nodes](../researchers/federated-workflows.md) |
| [Crypt4GH with proTES][repo-crypt4gh] (`protes-middleware-crypt4gh`) | Outdated | A task on Crypt4GH-encrypted files that are decrypted only inside the task's container, through a proTES middleware and Funnel. Needs proTES 0.3.0 or earlier, as later versions run plugins instead of middlewares. | [Crypt4GH with proTES](../researchers/crypt4gh-with-protes.md) |
| [Demo 2023-ecp-f2f][repo-f2f] (`elixir-cloud-demos`) | Retired | Tasks with `curl` and `py-tes` on TESK and Funnel, distribution through proTES, and a CWL workflow with `cwl-tes`, as shown at the ELIXIR Compute Platform meeting in February 2023. | [Retired demos](#retired-demos) |
| [Demo workflows][repo-workflows] (`demo-workflows`) | Retired | CWL and Snakemake workflows (GWAS, hash splitter, sequence comparison, rare diseases) for tests of the stack from 2019 to 2022. | [Retired demos](#retired-demos) |

The states were checked on 2026-11-10, against the default branch of each
repository: `token-exchange-flow-testbed` at `7585c99`,
`nvflare-wes-testbed` at `ca418a6`, `biohackeu26-ga4gh-sdk-upgrade` at
`290cb80`, `demo-tes-hybrid-cloud` at `a9fcf13`,
`protes-middleware-crypt4gh` at `2c33121`, `elixir-cloud-demos` at
`5a7576b` and `demo-workflows` at `a069bea`.

## Test beds and demos

The two test beds are not demos of the deployment: they run everything on
your computer, with stand-ins for real sites and services, and say plainly
what they have and haven't shown. They are the quickest way to see how the
pieces fit, and they need no account. Never use them in production or with
real data.

The demo `demo-tes-hybrid-cloud` runs against real TES services and a proTES
gateway. There is no public deployment with a guaranteed uptime for it:
deploy the services yourself, or write to
[cloud-service@elixir-europe.org][elixir-on-cloud-email].

## Retired demos

**Demo 2023-ecp-f2f.** The demo was feature-locked after the meeting, as the
repository's README describes. It needs the proTES image of February 2023,
forks of `cwl-tes` and `py-tes` at fixed commits, and FTP servers with
credentials in the URLs of the task inputs and outputs. proTES 0.3.0 and
later require an access token and refuse tasks with credentials in their URLs
by default (`custom.controllers.post_task.url_credentials`, see the [proTES
configuration](https://protes.readthedocs.io/en/latest/configuration/#tasks)).
For tasks on several TES services through proTES, use
[Run Workflows Across Nodes](../researchers/federated-workflows.md) instead.

**Demo workflows.** The repository was last changed in 2022. Its run scripts
point to TES services and FTP servers that no longer exist, and to a fork of
`cwl-tes` from 2020. The CWL and Snakemake files may still serve as examples,
but they are not tested against the current products. To run your own
workflow through TES, see [Run workflows through
TES](../partners-and-developers/ga4gh-standards.md#run-workflows-through-tes).

## Add a demo

A demo that is listed as current has:

- a README with a quick start: the commands from a fresh clone to a result,
  and the output that tells that it worked;
- a CI job that runs this quick start on every change;
- a statement of what it has and hasn't been run against.

Propose a new demo, or report one that no longer works, in the
[Discussions][elixir-on-cloud-forum] or in the [issues of this
repository](https://github.com/elixir-cloud-aai/docs/issues).

[docs-sdk]: <https://biohackeu26-ga4gh-sdk-upgrade.readthedocs.io/en/latest/>
[repo-crypt4gh]: <https://github.com/elixir-cloud-aai/protes-middleware-crypt4gh>
[repo-f2f]: <https://github.com/elixir-cloud-aai/elixir-cloud-demos/tree/main/demos/2023-ecp-f2f>
[repo-hybrid]: <https://github.com/elixir-cloud-aai/demo-tes-hybrid-cloud>
[repo-nvflare]: <https://github.com/elixir-cloud-aai/nvflare-wes-testbed>
[repo-sdk]: <https://github.com/elixir-cloud-aai/biohackeu26-ga4gh-sdk-upgrade>
[repo-txf]: <https://github.com/elixir-cloud-aai/token-exchange-flow-testbed>
[repo-workflows]: <https://github.com/elixir-cloud-aai/demo-workflows>
