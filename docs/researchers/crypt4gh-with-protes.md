# Crypt4GH with proTES

This page shows how researchers can analyse Crypt4GH-encrypted sensitive
data without getting access to the decrypted data. A data holder encrypts
the data with [Crypt4GH](https://crypt4gh.readthedocs.io/). The researcher
sends a [GA4GH TES][ga4gh-tes] task to [proTES](https://protes.readthedocs.io/en/v0.3.0/).
A middleware of proTES adds a step that decrypts the files inside a
container of the [Funnel][funnel] TES service, and the task command runs on
the decrypted files.

!!! warning "Needs proTES 0.3.0 or earlier"
    The Crypt4GH middleware is a proof of concept. proTES 0.4.0 does not
    run middlewares any more: it refuses `custom.middlewares` at startup and
    uses plugins instead, and no port of the middleware exists in its repository or in
    [foca-plugins](https://foca-plugins.readthedocs.io/en/latest/) (see the
    [upgrade
    steps](https://protes.readthedocs.io/en/latest/upgrading/#plugins)). The
    steps below therefore need [proTES
    0.3.0](https://protes.readthedocs.io/en/v0.3.0/). The README of the
    middleware also warns that you must not use it in untrusted
    environments: it needs secret keys to be sent and stores decrypted files
    on disk.

!!! warning "Under construction"
    Not documented: how to install the middleware into proTES 0.3.0 (the
    repository describes only its development setup), a version of the
    middleware for current proTES, and which versions the steps were tested
    with. The configuration in step 4 is from the original tutorial and was
    not run again for this page.

## How it works

1. The data holder encrypts the data with Crypt4GH and stores it, for
   example in an S3 bucket.
2. The researcher sends a task for the encrypted files to proTES.
3. The middleware of proTES finds the encrypted files and adds an executor
   that decrypts them with the keys in the task.
4. Funnel runs the decrypt executor and then the executors of the
   researcher on the decrypted files, all in containers.
5. The results go to a storage that the researcher can read.

The researcher can repeat the analysis with other parameters at any time,
without the data holder.

## What you need

- Three virtual machines with Docker and network connections to each other:
  a Funnel server, a Funnel worker and a proTES gateway.
- Space for the encrypted and decrypted files and for the results.

## Set up

### 1. Install Funnel on the server and the worker

Install Funnel on both machines. See the [Funnel docs](https://calypr.org/tools/funnel/)
and the [releases](https://github.com/calypr/funnel/releases) of
[Funnel](https://github.com/calypr/funnel).

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

On the worker machine, create `worker-config.yaml`. Replace `XXX` with the
IP address of the server (the internal one, if both are in the same
network):

```yaml
Server:
  HostName: XXX
  RPCPort: "9090"

RPCClient:
  ServerAddress: XXX:9090

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

Deploy [proTES 0.3.0](https://protes.readthedocs.io/en/v0.3.0/) on the third
machine, with the Funnel server as its TES service, and install the
[Crypt4GH
middleware](https://github.com/elixir-cloud-aai/protes-middleware-crypt4gh)
(see "Under construction" above). Then enable the middleware in the
`custom` section of `pro_tes/config.yaml`:

```yaml
custom:
  middlewares:
    - - "pro_tes.plugins.middlewares.crypt4gh_decrypt.CryptMiddleware"
      - "pro_tes.plugins.middlewares.task_distribution.random.TaskDistributionRandom"
```

## Run the tasks

The three tasks run one after the other. Each is a TES task in a JSON file.

### Task 1: Generate Crypt4GH Key Pairs

This task generates cryptographic key pairs for both the data holder and researcher. This step is independent of the following steps and may have happened a while ago. Your private keys may already be in a secure place. If you have crypt4gh keys, feel free to skip this step.

Create a file named `task1_keygen.json`:

```json
{
  "name": "Generate crypt4gh key pairs",
  "description": "Generate data holder and researcher key pairs locally in container",
  "inputs": [],
  "outputs": [
    {
      "name": "data_holder_sk",
      "description": "Data holder secret key",
      "url": "file:///tmp/funnel-storage/keys/data_holder/data_holder.sec",
      "path": "/outputs/keys/data_holder/data_holder.sec",
      "type": "FILE"
    },
    {
      "name": "data_holder_pk",
      "description": "data_holder public key",
      "url": "file:///tmp/funnel-storage/keys/data_holder/data_holder.pub",
      "path": "/outputs/keys/data_holder/data_holder.pub",
      "type": "FILE"
    },
    {
      "name": "researcher_sk",
      "description": "researcher secret key",
      "url": "file:///tmp/funnel-storage/keys/researcher/researcher.sec",
      "path": "/outputs/keys/researcher/researcher.sec",
      "type": "FILE"
    },
    {
      "name": "researcher_pk",
      "description": "researcher public key",
      "url": "file:///tmp/funnel-storage/keys/researcher/researcher.pub",
      "path": "/outputs/keys/researcher/researcher.pub",
      "type": "FILE"
    },
    {
      "name": "researcher_pk_copy",
      "description": "Copy of researcher public key",
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

**Key Details:**

- Generates two key pairs: one for the data holder and one for the researcher
- Keys are generated without encryption (`--nocrypt`) for demonstration purposes
- The researcher's public key is copied to the data holder's directory for use during encryption
- All keys are exported to local storage via TES outputs

### Task 2: Encrypt a File

This task retrieves a file, encrypts it using Crypt4GH keys, and stores both the encrypted file in a distinct location. Create a file named `task2_encrypt_file.json`:

```json
{
  "name": "Encrypt stat file with crypt4gh",
  "description": "Retrieve a file, record its size, and encrypt it using data holder and researcher keys",
  "inputs": [
    {
      "name": "data_holder_sk",
      "description": "data_holder secret key",
      "url": "file:///tmp/funnel-storage/keys/data_holder/data_holder.sec",
      "path": "/inputs/keys/data_holder/data_holder.sec",
      "type": "FILE"
    },
    {
      "name": "researcher_pk",
      "description": "researcher public key",
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

**Key Details:**

- Downloads a sample file from a URL
- Records the original file size
- Takes the data holder's private key and researcher's public key as inputs
- Encrypts the file using Crypt4GH, producing a `.c4gh` encrypted file
- Stores the encrypted file

### Task 3: Decrypt and Process File

This task decrypts the encrypted file using the researcher's private key and processes it.

**Note:** The different paths indicate isolated storage paths that do not necessarily see each other. For example, distinct S3 buckets.

Create a file named `task3_decrypt_and_write_size.json`:

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
      "description": "researcher secret key",
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

**Key Details:**

- Takes the encrypted `.c4gh` file and researcher's private key as inputs
- The proTES middleware automatically decrypts the file during task execution
- Computes an MD5 checksum of the decrypted data for verification
- Stores the checksum in the output directory

## Submit the tasks

Send each task to proTES. Wait until a task is complete before you send the
next one:

```bash
curl -X POST http://localhost:8080/ga4gh/tes/v1/tasks \
  -H "Content-Type: application/json" \
  -d @task1_keygen.json
```

Use `task2_encrypt_file.json` and `task3_decrypt_and_write_size.json` in the
same way. Replace `localhost:8080` with the address of your proTES. If your
proTES requires access tokens (see its [access
control](https://protes.readthedocs.io/en/v0.3.0/access-control/)), add an
`Authorization: Bearer` header. Each submission returns a task ID. Use it to
watch the task:

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
  `curl http://<server-ip>:8000/v1/tasks/<task-id>`.

## Keep your keys safe

- Never commit private keys to version control.
- Store private keys encrypted, and restrict access to the storage
  directories.
- Use signed URLs or a key management system to send keys to the TES service.
- Use TLS for all endpoints outside tests.

## More information

- [Funnel](https://github.com/calypr/funnel)
- [proTES](https://protes.readthedocs.io/en/v0.3.0/)
- [Crypt4GH middleware](https://github.com/elixir-cloud-aai/protes-middleware-crypt4gh)
- [Crypt4GH](https://crypt4gh.readthedocs.io/)
- [GA4GH TES][ga4gh-tes]
