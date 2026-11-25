---
last_verified: 2026-11-25
---

# TESK

[TESK](https://github.com/elixir-cloud-aai/TESK) is a [GA4GH TES][ga4gh-tes]
service for Kubernetes. It runs each task as a Kubernetes Job.

## Role in the deployment

TESK is the TES service for Nodes with a Kubernetes or OpenShift cluster.
After you deploy it, register it in the [Cloud
Registry][elixir-cloud-registry] (see [Onboarding](../onboarding.md)). End
every upgrade or change of it by checking that sync updated its entry (see
[After a deployment or an
upgrade](../using-cloud-registry.md#after-a-deployment-or-an-upgrade)).

## Docs

- [TESK docs](https://tesk.readthedocs.io/)
- [Helm chart and its values](https://github.com/elixir-cloud-aai/TESK/tree/dev/charts/tesk)

## Notes for the deployment

- TESK runs on Kubernetes and OpenShift (see [OpenShift and other
  restricted
  clusters](https://tesk.readthedocs.io/en/latest/deployment/#openshift-and-other-restricted-clusters)).
- The cluster needs a default storage class (or the chart's
  `storageClass`). TESK uses persistent volume claims as temporary storage
  for the files of a task; from chart 0.3.0 on, the TESK docs say that
  `ReadWriteOnce` is enough (see
  [Requirements](https://tesk.readthedocs.io/en/latest/deployment/#requirements)).
  A `ReadWriteMany` volume is needed only for the shared file system
  backend (`transfer`, for `file:` URLs; see [Shared file
  system](https://tesk.readthedocs.io/en/latest/deployment/#shared-file-system)).
- From chart 0.3.0, set the service info in the chart's values
  (`serviceInfo`), so that the registry can import and sync it (see
  [Prepare Your Service Info](../service-info.md#tesk)).
- For a step-by-step setup, see the [Node onboarding
  tutorial](../node-onboarding-tutorial.md).
- To use the Node's S3 storage (see [Onboarding](../onboarding.md)), set the
  chart's `storage` value to `s3` and follow
  [S3](https://tesk.readthedocs.io/en/latest/deployment/#s3) in the TESK
  docs.
