# TESK

[TESK](https://github.com/elixir-cloud-aai/TESK) is a [GA4GH TES][ga4gh-tes]
service for Kubernetes. It runs each task as a Kubernetes Job.

## Role in the deployment

TESK is the TES service for Nodes with a Kubernetes or OpenShift cluster.
After you deploy it, register it in the [Cloud
Registry][elixir-cloud-registry] (see [Onboarding](../onboarding.md)).

## Docs

- [TESK docs](https://tesk.readthedocs.io/)
- [Helm chart and its values](https://github.com/elixir-cloud-aai/TESK/tree/master/charts/tesk)

## Notes for the deployment

- TESK has been tested with Kubernetes, OpenShift and Minikube.
- The cluster needs a `ReadWriteMany` storage class, for example NFS or
  CephFS. TESK uses persistent volume claims as temporary storage for the
  files of a task and deletes them when the task ends.
- To use the Node's S3 storage (see [Onboarding](../onboarding.md)), set the
  chart's `storage` value to `s3` and follow the chart's README.
