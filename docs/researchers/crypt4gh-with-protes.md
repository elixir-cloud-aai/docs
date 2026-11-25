---
last_verified: null
---

# Crypt4GH with proTES

This page shows how researchers can analyse Crypt4GH-encrypted sensitive
data without opening the decrypted files themselves. A data holder encrypts
the data with [Crypt4GH][crypt4gh]. The researcher sends a [GA4GH
TES][ga4gh-tes] task to [proTES][protes]. A middleware of proTES adds a
step that decrypts the files inside a container of the [Funnel][funnel] TES
service, and the task commands run on the decrypted files.

Unlike the tutorials of this section, this page doesn't use the live
services of ELIXIR On-Cloud: you set up Funnel and proTES on three virtual
machines of your own.

!!! warning "Needs an unreleased proTES branch"
    The Crypt4GH middleware is a proof of concept, and no release of proTES
    runs it:

    - proTES 0.4.0 and later don't run middlewares any more: they refuse
      `custom.middlewares` at startup and use plugins instead (see the
      [upgrade
      steps](https://protes.readthedocs.io/en/latest/upgrading/#plugins)).
    - proTES 0.3.0 and earlier load only middlewares that derive from its
      class `AbstractMiddleware`. The released middleware (version 0.0.1 on
      the default branch of
      [protes-middleware-crypt4gh](https://github.com/elixir-cloud-aai/protes-middleware-crypt4gh), <!-- historical -->
      last changed in 2024) doesn't, so proTES refuses it at startup. The
      fix ([protes-middleware-crypt4gh#33](https://github.com/elixir-cloud-aai/protes-middleware-crypt4gh/pull/33)) <!-- historical -->
      was never merged, and the repository is archived.

    The steps below therefore use the branch on which the authors of this
    tutorial ran it: `adjust_middleware` of proTES, which adds the
    middleware to proTES itself (see [step 4](#4-set-up-protes)). The README
    of the middleware also warns that you must not use it in untrusted
    environments: it needs secret keys to be sent and stores decrypted files
    on disk.

!!! note "Successor: the Crypt4GH plugin for current proTES"
    The middleware's successor is the plugin
    [`tes.data.crypt4gh`](https://github.com/elixir-cloud-aai/foca-plugins/tree/dev/plugins/tes/data/crypt4gh)
    of [foca-plugins](https://foca-plugins.readthedocs.io/en/latest/), for
    current proTES. Its first release,
    [0.1.0](https://github.com/elixir-cloud-aai/foca-plugins/releases/tag/foca-plugin-tes-data-crypt4gh-v0.1.0),
    came out on 21 November 2026 as a pre-release. The proTES of ELIXIR
    On-Cloud doesn't run it yet
    ([generic-issues#120](https://github.com/elixir-cloud-aai/generic-issues/issues/120)).
    Once it does, this page will be rewritten for the plugin and the
    deployed proTES
    ([docs#177](https://github.com/elixir-cloud-aai/docs/issues/177)).

!!! note "Tested versions"
    This page goes back to a tutorial that its authors added to this hub in
    December 2025 and updated in July 2026
    ([#36](https://github.com/elixir-cloud-aai/docs/pull/36)). It records no
    released versions. Its authors used:

    | Product | Version |
    |---|---|
    | proTES, with the middleware | branch [`adjust_middleware`](https://github.com/elixir-cloud-aai/proTES/tree/adjust_middleware), commit [`0d7efdf`](https://github.com/elixir-cloud-aai/proTES/commit/0d7efdf) (April 2026): not merged, in no release |
    | Middleware, as a separate package | branch `update_middleware` of protes-middleware-crypt4gh ([#33](https://github.com/elixir-cloud-aai/protes-middleware-crypt4gh/pull/33), not merged) <!-- historical --> |
    | Funnel | built from the default branch of its repository, at a commit that wasn't recorded |

    The steps were not run again for this page.

!!! danger "The task commands see the decrypted data"
    The commands of a task run on the decrypted files. A command that
    researchers write can copy the plaintext into the task outputs or send it
    elsewhere. The setup protects the data only if the commands are trusted or
    approved by the data holder, and if the outputs and the network access of
    the containers are restricted. Use it for sensitive data only after you
    have checked this.

## How it works

1. The data holder encrypts the data with Crypt4GH and stores it, for
   example in an S3 bucket.
2. The researcher sends a task for the encrypted files to proTES.
3. The middleware of proTES finds the encrypted files and adds an executor
   that decrypts them with the keys in the task.
4. Funnel runs the decrypt executor and then the executors of the
   researcher on the decrypted files, all in containers.
5. The results go to storage that the researcher can read.

The researcher can repeat the analysis with other parameters at any time,
without the data holder.

## What you need

- Three virtual machines with Docker and network connections to each other:
  a Funnel server, a Funnel worker and a proTES gateway.
- Space for the encrypted and decrypted files and for the results.
- A private network for the machines. The Funnel server accepts tasks on
  its HTTP and RPC ports (8000 and 9090 below) and the worker runs them, so
  only the proTES gateway and the worker may reach these ports. If other
  machines can reach them, enable authentication in Funnel (see `Server.BasicAuth`
  in its [default
  config](https://github.com/calypr/funnel/blob/develop/internal/config/examples/default-config.yaml)).

## Set up

### 1. Install Funnel on the server and the worker

Install Funnel on both machines. See the [Funnel
docs](https://calypr.org/tools/funnel/) and the
[releases](https://github.com/calypr/funnel/releases) of
[Funnel][funnel].

### 2. Configure and start the Funnel server

On the server machine, create `server-config.yaml`:

```yaml
Server:
  HostName: 0.0.0.0
  HTTPPort: "8000"
  RPCPort: "9090"

Database: boltdb

BoltDB:
  Path: ./funnel-work-dir/funnel.db

Compute: "manual"

Scheduler:
  ScheduleRate: 1s
  ScheduleChunk: 10

LocalStorage:
  AllowedDirs:
    - /tmp/funnel-storage
```

The server listens on all interfaces (`HostName`), serves its HTTP API on
port 8000 and the RPC port for workers on 9090. `Compute: "manual"` means
that you start the workers yourself. Start the server:

```bash
funnel server run --config server-config.yaml &
```

### 3. Configure and start the Funnel worker

On the worker machine, create `worker-config.yaml`. Replace `<server-ip>`
with the IP address of the server (the internal one, if both are in the
same network):

```yaml
Server:
  HostName: <server-ip>
  RPCPort: "9090"

RPCClient:
  ServerAddress: <server-ip>:9090

Worker:
  WorkDir: "/tmp/funnel-work"

Node:
  ID: "worker-node-1"
  Resources:
    Cpus: 4
    RamGb: 7.0
    DiskGb: 18.0
  UpdateRate: 5s

LocalStorage:
  AllowedDirs:
    - /tmp/funnel-storage
```

Give the worker an ID that no other worker has, and set the resources to
what the machine offers. Start the worker:

```bash
funnel node run --config worker-config.yaml &
```

If the worker stops after one task, run the command in a loop (`while true; do
funnel node run --config worker-config.yaml; done`). Check that both
processes run, and that the server answers at `http://<server-ip>:8000`.

### 4. Set up proTES

On the third machine, deploy proTES from the branch `adjust_middleware`
(see "Needs an unreleased proTES branch" above). The branch contains the
middleware as `pro_tes/plugins/middlewares/crypt4gh_decrypt.py`, so there
is nothing else to install, and its `pro_tes/config.yaml` already enables
it:

```yaml
custom:
  middlewares:
    - - "pro_tes.plugins.middlewares.crypt4gh_decrypt.CryptMiddleware"
      - "pro_tes.plugins.middlewares.task_distribution.random.TaskDistributionRandom"
```

The random middleware is the fallback for tasks without Crypt4GH inputs.

1. Clone proTES and check out the branch:

    ```bash
    git clone --branch adjust_middleware https://github.com/elixir-cloud-aai/proTES.git
    cd proTES
    ```

2. In `pro_tes/config.yaml`, set `custom.tes.service_list` to the address
   of your Funnel server, e.g., `http://<server-ip>:8000`. The branch has an
   address of the authors' network there (`http://192.168.0.91:8000`).
   The next step builds the edited file into the image.
3. Build and start proTES with its Docker Compose file, as the README of
   the branch describes:

    ```bash
    docker compose up -d --build
    ```

    The README names the older command `docker-compose`; both work with
    the file.

proTES then serves its TES API on port 8080 of the machine (see
`docker-compose.yaml`).

## Write the tasks

Each task is a TES task in a JSON file. Run them in order. If you already
have Crypt4GH keys, skip task 1, and put your keys at the paths that tasks
2 and 3 read (`/tmp/funnel-storage/keys/...`) or change the `url` of
their key inputs. In this setup, all files are in
`/tmp/funnel-storage` on the Funnel machines (`file://` URLs). With real
data, the data holder's and the researcher's files would be in separate
storage, for example in different S3 buckets.

### Task 1: Generate key pairs

This task creates a key pair for the data holder and one for the
researcher. In practice, each party creates its keys once, on its own
computer, and keeps the private key safe. The task writes unencrypted
private keys to the Funnel storage, which is fine for this demo only: for
real data, never create keys in a task (see [Keep your keys
safe](#keep-your-keys-safe)).

Create a file named `task1_keygen.json`:

```json
{
  "name": "Generate crypt4gh key pairs",
  "description": "Generate data holder and researcher key pairs locally in container",
  "inputs": [],
  "outputs": [
    {
      "name": "data_holder_sk",
      "description": "Data holder private key",
      "url": "file:///tmp/funnel-storage/keys/data_holder/data_holder.sec",
      "path": "/outputs/keys/data_holder/data_holder.sec",
      "type": "FILE"
    },
    {
      "name": "data_holder_pk",
      "description": "Data holder public key",
      "url": "file:///tmp/funnel-storage/keys/data_holder/data_holder.pub",
      "path": "/outputs/keys/data_holder/data_holder.pub",
      "type": "FILE"
    },
    {
      "name": "researcher_sk",
      "description": "Researcher private key",
      "url": "file:///tmp/funnel-storage/keys/researcher/researcher.sec",
      "path": "/outputs/keys/researcher/researcher.sec",
      "type": "FILE"
    },
    {
      "name": "researcher_pk",
      "description": "Researcher public key",
      "url": "file:///tmp/funnel-storage/keys/researcher/researcher.pub",
      "path": "/outputs/keys/researcher/researcher.pub",
      "type": "FILE"
    },
    {
      "name": "researcher_pk_copy",
      "description": "Copy of the researcher public key",
      "url": "file:///tmp/funnel-storage/keys/data_holder/researcher.pub",
      "path": "/outputs/keys/data_holder/researcher.pub",
      "type": "FILE"
    }
  ],
  "executors": [
    {
      "image": "quay.io/grbot/crypt4gh-tutorial",
      "command": [
        "/bin/bash",
        "-c",
        "crypt4gh-keygen --sk /outputs/keys/data_holder/data_holder.sec --pk /outputs/keys/data_holder/data_holder.pub -f --nocrypt && crypt4gh-keygen --sk /outputs/keys/researcher/researcher.sec --pk /outputs/keys/researcher/researcher.pub -f --nocrypt && cp /outputs/keys/researcher/researcher.pub /outputs/keys/data_holder/researcher.pub"
      ],
      "workdir": "/tmp"
    }
  ],
  "resources": {
    "cpu_cores": 1,
    "ram_gb": 2,
    "disk_gb": 5
  }
}
```

What the task does:

- It creates two key pairs, one for the data holder and one for the
  researcher.
- It doesn't encrypt the private keys (`--nocrypt`), for the demo only.
- It puts a copy of the researcher's public key in the data holder's
  directory, next to the data holder's keys. Task 2 reads the original in
  the researcher's directory.
- It exports all keys to the Funnel storage as TES outputs.

### Task 2: Encrypt a file

This task downloads an image, writes its size in bytes to a text file, and
encrypts that text file with the data holder's private key and the
researcher's public key. It stores the plain text file in `raw/` and the
encrypted file in `encrypted/`. The data holder runs this task, not the
researcher, because it needs the data holder's private key; with real
data, the data holder encrypts the files in a trusted environment of its
own and never passes its private key to a task that researchers can
write or change. Create a file named
`task2_encrypt_file.json`:

```json
{
  "name": "Encrypt stat file with crypt4gh",
  "description": "Retrieve a file, record its size, and encrypt it using data holder and researcher keys",
  "inputs": [
    {
      "name": "data_holder_sk",
      "description": "Data holder private key",
      "url": "file:///tmp/funnel-storage/keys/data_holder/data_holder.sec",
      "path": "/inputs/keys/data_holder/data_holder.sec",
      "type": "FILE"
    },
    {
      "name": "researcher_pk",
      "description": "Researcher public key",
      "url": "file:///tmp/funnel-storage/keys/researcher/researcher.pub",
      "path": "/inputs/keys/researcher/researcher.pub",
      "type": "FILE"
    }
  ],
  "outputs": [
    {
      "name": "encrypted_file",
      "description": "Encrypted file",
      "url": "file:///tmp/funnel-storage/encrypted/united_kingdom_logo_size.txt.c4gh",
      "path": "/outputs/encrypted/united_kingdom_logo_size.txt.c4gh",
      "type": "FILE"
    },
    {
      "name": "size_file",
      "description": "Text file containing original file size",
      "url": "file:///tmp/funnel-storage/raw/united_kingdom_logo_size.txt",
      "path": "/outputs/raw/united_kingdom_logo_size.txt",
      "type": "FILE"
    }
  ],
  "executors": [
    {
      "image": "quay.io/grbot/crypt4gh-tutorial",
      "command": [
        "/bin/bash",
        "-c",
        "curl -L -o /tmp/file.png http://britishfamily.co.uk/wp-content/uploads/2015/02/MADE_IN_BRITAIN_web_300x300.png && stat -c %s /tmp/file.png > /outputs/raw/united_kingdom_logo_size.txt && crypt4gh encrypt --sk /inputs/keys/data_holder/data_holder.sec --recipient_pk /inputs/keys/researcher/researcher.pub < /outputs/raw/united_kingdom_logo_size.txt > /outputs/encrypted/united_kingdom_logo_size.txt.c4gh"
      ],
      "workdir": "/tmp"
    }
  ],
  "resources": {
    "cpu_cores": 1,
    "ram_gb": 2,
    "disk_gb": 10
  }
}
```

What the task does:

- It downloads a sample image and writes its size to a text file.
- It takes the data holder's private key and the researcher's public key
  as inputs.
- It encrypts the size file with Crypt4GH, into a `.c4gh` file for the
  researcher. The researcher's private key decrypts it, and so does the
  data holder's, because Crypt4GH derives the key from the sender's and
  the recipient's key pairs.
- It exports the size file and the encrypted file.

### Task 3: Decrypt the file and process it

This task computes the MD5 checksum of the decrypted file. The task itself
contains no decryption step: proTES finds the input that ends in `.c4gh`
and adds one. Create a file named `task3_decrypt_and_write_size.json`:

```json
{
  "name": "Decrypt crypt4gh file",
  "description": "Decrypt an encrypted file using researcher key locally",
  "volumes": ["/outputs/test"],
  "inputs": [
    {
      "name": "encrypted_file",
      "description": "Encrypted input file",
      "url": "file:///tmp/funnel-storage/encrypted/united_kingdom_logo_size.txt.c4gh",
      "path": "/inputs/encrypted/united_kingdom_logo_size.txt.c4gh",
      "type": "FILE"
    },
    {
      "name": "researcher_sk",
      "description": "Researcher private key",
      "url": "file:///tmp/funnel-storage/keys/researcher/researcher.sec",
      "path": "/inputs/keys/researcher/researcher.sec",
      "type": "FILE"
    }
  ],
  "outputs": [
    {
      "name": "decrypted_file",
      "description": "MD5 checksum of automatically decrypted file",
      "url": "file:///tmp/funnel-storage/decrypted/united_kingdom_logo_md5sum.txt",
      "path": "/outputs/decrypted/united_kingdom_logo_md5sum.txt",
      "type": "FILE"
    }
  ],
  "executors": [
    {
      "image": "quay.io/grbot/crypt4gh-tutorial",
      "command": [
        "/bin/sh",
        "-c",
        "mkdir -p /outputs/decrypted && /bin/md5sum /outputs/decrypted/united_kingdom_logo_size.txt > /outputs/decrypted/united_kingdom_logo_md5sum.txt"
      ],
      "workdir": "/tmp"
    }
  ],
  "resources": {
    "cpu_cores": 1,
    "ram_gb": 2,
    "disk_gb": 5
  }
}
```

What the task does:

- It takes the encrypted `.c4gh` file and the researcher's private key as
  inputs.
- The middleware of proTES adds a first executor that decrypts the inputs
  into a volume of its own and copies the decrypted files into the
  directory of each output, here `/outputs/decrypted`. The decrypted file
  loses its extension `.c4gh`, so the command reads
  `/outputs/decrypted/united_kingdom_logo_size.txt`, a path that the task
  itself doesn't declare.
- It computes the MD5 checksum of the decrypted file and exports only the
  checksum: Funnel uploads only the declared outputs, not the decrypted
  copy next to them.
- The volume `/outputs/test` isn't used by the command; the task works
  without it.

## Submit the tasks

Send each task to proTES. Wait until a task is complete before you send the
next one:

```bash
curl -X POST http://localhost:8080/ga4gh/tes/v1/tasks \
  -H "Content-Type: application/json" \
  -d @task1_keygen.json
```

Use `task2_encrypt_file.json` and `task3_decrypt_and_write_size.json` in
the same way. This setup serves proTES over plain HTTP on port 8080, so
send the tasks from the proTES machine itself (`localhost`), or put proTES
behind a reverse proxy with TLS before you send tokens or keys over the
network. If your proTES requires access tokens (see its [access
control](https://protes.readthedocs.io/en/v0.3.0/access-control/)), add an
`Authorization: Bearer` header to every request. Each submission returns a
task ID. Use it to watch the task:

```bash
curl http://localhost:8080/ga4gh/tes/v1/tasks/<task-id>
```

## Troubleshooting

- **Tasks do not run.** Check that the Funnel server and the worker run and
  that the machines reach each other.
- **A file is not decrypted.** Check the configuration of the middleware in
  proTES, and read the logs of the proTES container (`docker logs`) while you
  submit a task. The encrypted files must have the extension `.c4gh`.
- **Task details.** Ask the Funnel server:
  `curl http://<server-ip>:8000/v1/tasks/<funnel-task-id>`. Funnel's task
  ID isn't the ID that proTES returned: list Funnel's tasks with
  `curl http://<server-ip>:8000/v1/tasks` to find it.

## Keep your keys safe

- Never commit private keys to version control.
- Store private keys encrypted, and restrict access to the storage
  directories.
- Use signed URLs or a key management system to send keys to the TES service.
- Use TLS for all endpoints outside tests.

## Where to go next

- [Funnel][funnel]
- [proTES][protes]
- [Crypt4GH plugin for current proTES](https://github.com/elixir-cloud-aai/foca-plugins/tree/dev/plugins/tes/data/crypt4gh)
- [Crypt4GH middleware](https://github.com/elixir-cloud-aai/protes-middleware-crypt4gh) (archived) <!-- historical -->
- [Crypt4GH][crypt4gh]
- [GA4GH TES][ga4gh-tes]
