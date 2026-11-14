# Funnel

[Funnel](https://github.com/calypr/funnel) is a [GA4GH TES][ga4gh-tes]
service. It runs tasks on a cluster through a backend, such as Slurm or
PBS.

## Role in the deployment

Funnel is the TES service for Nodes with an HPC or HTC cluster. After you
deploy it, register it in the [Cloud Registry][elixir-cloud-registry] (see
[Onboarding](../onboarding.md)).

## Docs

- [Funnel docs](https://calypr.org/tools/funnel)
- [Funnel repository](https://github.com/calypr/funnel)

## Notes for the deployment

- The ELIXIR On-Cloud documents Funnel with Slurm and with OpenPBS (below).
  For other backends, such as HTCondor or Grid Engine, see the Funnel docs.
- Place the `funnel` binary on a server that can submit jobs to the
  cluster: a login or submission node of Slurm or PBS.
- Put the config file on the same server. For Slurm, [this
  file][funnel-config-slurm] is a starting point.
- If everything works, Funnel listens on port `8080`.
- Funnel's service info can't be set yet
  ([calypr/funnel#1493](https://github.com/calypr/funnel/issues/1493)), and
  this deployment refuses its environment, `development`: register it by
  hand (see [Manual entry, the
  fallback](../service-info.md#manual-entry-the-fallback)).

## Funnel with OpenPBS

Funnel's `pbs` backend submits each task as a job with `qsub` and cancels it
with `qdel` (see [PBS/Torque][funnel-pbs] in the Funnel docs). It renders
the job script from a template, with the variables `TaskId`, `WorkDir`,
`Cpus`, `RamGb`, `DiskGb` and `Zone` of the task, and `Args`, which points
the worker to a copy of Funnel's config in the work directory. The worker
in the job reports the state of its task to the Funnel server.

1. Write the job script template, e.g., to `/etc/funnel/pbs-template.txt`.
   The [template of the Funnel docs][funnel-pbs-template] uses the resource
   syntax of PBS/Torque (`-l nodes=1:ppn=…`). OpenPBS requests resources by
   chunks (`-l select=…`), so adapt it, e.g.:

    ```text
    #!/bin/bash
    #PBS -N {{.TaskId}}
    #PBS -o {{.WorkDir}}/funnel-stdout
    #PBS -e {{.WorkDir}}/funnel-stderr
    #PBS -l select=1:ncpus={{if ne .Cpus 0}}{{.Cpus}}{{else}}1{{end}}{{if ne .RamGb 0.0}}{{printf ":mem=%.0fgb" .RamGb}}{{end}}

    funnel worker run {{.Args}} --taskID {{.TaskId}}
    ```

    Add the queue (`#PBS -q …`) and the account or project options that
    your cluster requires. Mind what the template leaves out or rounds:

    - **Disk:** OpenPBS has no standard resource for the free disk space of
      a job, so the template ignores `DiskGb`.
    - **Zone:** it ignores `Zone`, the zone that a task asks for, too. The
      Funnel docs suggest it as a queue name (e.g., `{{if .Zone}}#PBS -q
      {{.Zone}}{{end}}`); add that only if your queues should be chosen by
      the users of your service.
    - **Memory:** OpenPBS takes whole units, and templates can't round up:
      `%.0f` rounds `RamGb` to the nearest GB, so a task that asks for
      1.4 GB gets 1 GB, and one that asks for less than 0.5 GB gets
      `mem=0gb`. If tasks of your users ask for fractions, set a default
      memory per job in the queue, or add a margin in the template.

    The `funnel` binary must be on the `PATH` of the jobs on the execution
    hosts too, e.g., on a shared file system.

2. Point Funnel's config file at it, and keep the reconciler off, as it is
   by default (see the warning below):

    ```yaml
    Compute: pbs
    PBS:
      TemplateFile: /etc/funnel/pbs-template.txt
      DisableReconciler: true
    ```

3. Put Funnel's work directory (`WorkDir` in the config file), which also
   holds the job's `funnel-stdout` and `funnel-stderr` and the config for
   the worker, on a file system that the submission host and the execution
   hosts share: the worker of a task runs on an execution host and needs
   the task's files there.

!!! warning "Not tested here"
    These steps follow the Funnel docs, Funnel's code and the OpenPBS
    resource syntax; they haven't been tested on an OpenPBS cluster for
    these docs. Funnel's backend was written for PBS/Torque. Its reconciler,
    which marks a task as failed when its job fails without the worker
    reporting it, reads the XML output of `qstat -x` of Torque; in OpenPBS,
    `qstat -x` lists finished jobs instead, in plain text. With the
    reconciler off, a task whose job fails that way (e.g., killed for
    exceeding its limits) may keep its last state: check such jobs with the
    tools of OpenPBS. Please report what works on your cluster to the
    [admins][elixir-on-cloud-email].

[funnel-pbs]: <https://github.com/calypr/funnel/blob/v0.12.3/docs/compute/pbs-torque.md>
[funnel-pbs-template]: <https://github.com/calypr/funnel/blob/v0.12.3/website/static/funnel-config-examples/pbs-template.txt>
