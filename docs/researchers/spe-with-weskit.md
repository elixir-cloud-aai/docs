# Sensitive Data in a Secure Processing Environment

A Secure Processing Environment (SPE) lets researchers run workflows on
sensitive data without ever getting access to the data. The data stays in a
cluster. Researchers submit runs of workflows that a data controller approved,
and they read only the results that the environment releases.

This page describes the SPE that was built in the de.NBI Cloud (ELIXIR-DE)
with open-source services. It has two parts: the steps for a researcher who
uses an SPE, and the steps for an operator who sets one up.

!!! warning "Under construction"
    No SPE is listed as a public service of the deployment. The address of
    the environment, its web interface and the way to ask for permission are
    not documented. Until then, write to
    [cloud-service@elixir-europe.org][elixir-on-cloud-email].

## How it works

| Part | Service | Role |
|---|---|---|
| Execution | [WESkit](https://gitlab.com/one-touch-pipeline/weskit/documentation) | A [GA4GH WES][ga4gh-wes] service. It accepts runs of Snakemake and Nextflow workflows and sends them to the cluster. |
| Cluster | [Slurm](https://slurm.schedmd.com/) | Runs the workflows. Holds all sensitive data. |
| Results | S3 storage, for example MinIO | Holds the results that may leave the cluster. |
| Login | [LS Login](https://www.lifescience-ri.eu/life-science-login/) | Identifies the users of WESkit and of the results storage. |
| Web interface | [WESkit dashboard](https://gitlab.com/one-touch-pipeline/weskit/gui/-/tree/spe4hd_demo) | Lets researchers start and watch runs in a browser. |

## Use an SPE

1. Ask the operator of the SPE for permission. Access is restricted because
   of national rules and laws, so collaborators and researchers from other
   countries need the permission of the identity provider of the SPE.
2. Log in with LS Login at the web interface, or get an access token (see
   [Using the APIs](../partners-and-developers/apis.md#2-get-an-access-token)).
3. Submit a run. You can only choose a workflow that the data controller
   installed in the environment. Follow the WESkit [user
   guide](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/user/README.md)
   for the request, and for the [states of a
   run](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/user/WESStates.md).
4. Wait until the run is complete.
5. Log in to the results storage with LS Login and read the files in the
   bucket `results`.

## Set up an SPE

You need one virtual machine for WESkit, one or two for a Slurm cluster, and
one for the S3 storage.

1. **Deploy WESkit** with the [admin
   guide](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/README.md)
   on a machine that users can reach over the internet. Then:
    - configure the [compute
      environment](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/executor.md)
      and the workflow engines;
    - install the approved workflows, as the guide to [workflow
      installation](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/workflow-installation.md)
      describes. A workflow is a Snakemake or Nextflow script with its
      dependencies and data;
    - put the sensitive data on the file system of the cluster.
2. **Provide a Slurm cluster.** You can create one with
   [BiBiGrid](https://cloud.denbi.de/wiki/Tutorials/BiBiGrid/) in the
   [de.NBI Cloud](https://www.denbi.de/cloud), or use any other Slurm cluster.
3. **Deploy an S3 server.** Create a bucket `results`, and give all
   authorized users read access to it.
4. **Copy the results.** A script that runs as a cron job (see below) copies
   the files that may leave the cluster into the bucket.
5. **Offer a web interface.** The [`spe4hd_demo` branch of the WESkit
   dashboard](https://gitlab.com/one-touch-pipeline/weskit/gui/-/tree/spe4hd_demo)
   is a lightweight web app to run and watch workflows. You can use it as a
   template for your own.
6. **Connect LS Login.** Register one service at LS Login for each of
   WESkit, the S3 server and the web interface (see the [LS Login
   guide](https://www.lifescience-ri.eu/registering-integrating-and-managing-your-service/)),
   each with its own client credentials and redirect URI. Configure WESkit for
   OpenID Connect as in its [login
   guide](https://gitlab.com/one-touch-pipeline/weskit/documentation/-/blob/master/admin/login.md).
   For MinIO, see [Using LS Login](../operators/ls-login.md).

!!! note "MinIO"
    The MinIO repository is no longer maintained: its README says so. Any
    S3-compatible server can hold the results. The script below uses the
    MinIO client `mc`.

### Results copy script

WESkit writes the file `log.json` into the log folder of a run when the run
has finished. The script looks for new finished runs, uploads their file
`results.csv` to the bucket if the run made the plot `plots/quals.svg`, and
marks the run with the file `upload_token`
after a successful upload, so that it uploads each run only once and retries
failed uploads. Replace `USERNAME` and `PASSWORD`, and
adapt the paths and files to your workflow.

```bash
mc config host add local http://localhost:9000 USERNAME PASSWORD;

BASE_DIR=/minio_data/data

process_directory() {
    local dir="$1"
    local bucketname=$(basename $dir)
    if [[ ! -f "$dir/upload_token" ]]; then
      if [ -f "$dir/plots/quals.svg" ]; then
          mc mb --ignore-existing local/results/$bucketname &&
          mc cp $dir/results.csv local/results/$bucketname &&
          touch "$dir/upload_token";
      else
          touch "$dir/upload_token"
      fi
    fi
}

for dir in "$BASE_DIR"/*/*/; do
  for logsdir in "$dir".weskit/*/; do
    if [ -d "$logsdir" ]; then
      if [ -f "$logsdir/log.json" ]; then
        process_directory $dir
      fi
    fi
  done
done
```
