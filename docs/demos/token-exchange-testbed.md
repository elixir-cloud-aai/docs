# Token Exchange Testbed

The [token exchange testbed][repo] tries per-hop OAuth 2.0 token exchange
with [LS Login](../operators/ls-login.md), for the chain of ELIXIR On-Cloud
services from a front end through a WES and the proTES gateway to the TES
nodes: each service exchanges the token that it received for one that is only
good for the next service. It tests the design proposed in [proTES issue
#391](https://github.com/elixir-cloud-aai/proTES/issues/391), with a small
client, gateway and node as stand-ins for the real services.

!!! warning "Local mock only"
    So far, the testbed has run against a local mock of LS Login only. The
    mock accepts almost everything, so the testbed enforces LS Login's rules
    itself. A passing run shows that the testbed works, not how LS Login
    behaves. See the testbed's [limits][docs-limits]. Never use it in
    production or with real accounts.

## What you need

- Docker with Compose, on Linux, macOS or WSL. It has been run on Linux only
  so far.
- Nothing else for the mock: no Python on your computer, no free ports, no
  account.

## Steps

1. Clone the repository, build the images and run all scenarios against the
   mock:

    ```sh
    git clone https://github.com/elixir-cloud-aai/token-exchange-flow-testbed.git
    cd token-exchange-flow-testbed
    docker compose build
    docker compose run --rm e2e
    ```

2. Check the output. It ends with `N/N checks passed`, with the same number
   twice.
3. Remove the containers:

    ```sh
    docker compose down -v
    ```

The repository's CI runs the same scenarios on every change.

## What you see

The run goes through the scenarios of the [tests][docs-tests]: one sign-in,
then one token per hop up to the node; requests that must be refused, and
which service refuses them; groups and entitlements; token lifetimes and
refresh; and what a node can tell about the path of a request.

## Where to go next

- To try the commands by hand against the mock: [Checking the
  setup][docs-checking].
- To run the tests against LS Login, with test accounts and registered
  clients: [Tests][docs-tests] and [Client registration][docs-clients].
- The background, independent of any product: [Use case][docs-use-case].

[docs-checking]: <https://token-exchange-flow-testbed.readthedocs.io/en/latest/setup/checking/>
[docs-clients]: <https://token-exchange-flow-testbed.readthedocs.io/en/latest/setup/client-registration/>
[docs-limits]: <https://token-exchange-flow-testbed.readthedocs.io/en/latest/testbed/limits/>
[docs-tests]: <https://token-exchange-flow-testbed.readthedocs.io/en/latest/tests/>
[docs-use-case]: <https://token-exchange-flow-testbed.readthedocs.io/en/latest/background/use-case/>
[repo]: <https://github.com/elixir-cloud-aai/token-exchange-flow-testbed>
