---
name: marlowe-pool
description: The standing pool of roach holds on Marlowe (1 GPU and 8 GPU on preempt, a daily 8-GPU hold on batch billed to pm07) — check what is queued or idle and when the next one starts, claim one, submit a job into it, keep an idle one alive with USR2. Use whenever a Marlowe GPU is wanted soon, or the user asks about holds, their availability or ETA.
---

# Marlowe hold pool

A cron on Marlowe login-02 (`*/5 * * * * marlowe-pool tick`, code in `~/.config/marlowe-pool/pool.py`) keeps roach holds queued, so a GPU is often already allocated when work arrives. Every command below works from ILC (it goes over `ssh marlowe`) and on Marlowe itself. Check `ssh -O check marlowe` first; if there is no master, ask the human to run `! ssh marlowe true`.

| kind | partition / account | shape | submitted | released after idle | cost |
| --- | --- | --- | --- | --- | --- |
| `1gpu` | preempt / marlowe-m000137 | 1 GPU, 14 cpu, 1 h | 4 every hour, more when none are waiting | 10 min | free; preempted any time |
| `8gpu` | preempt / marlowe-m000137 | whole node, 4 h | 2 every 4 h, more when none are waiting | 15 min | free; rarely starts |
| `batch8` | batch / marlowe-m000137-pm07 | whole node, 2 days | 1 daily at 09:00, at most 2 waiting | 2 h | **billed: 8 GPU-hours per hour held, idle or not** |

## See what is there

```
marlowe-holds --plain                 # every hold: state, node, time left, idle countdown, est. start of queued ones
marlowe-holds --plain --kind batch8   # one kind; the summary line has the next estimated start
marlowe-holds --json --kind batch8    # the same as JSON: state, est_start, left_s, idle_s, idle_limit_s, extendable, steps, claimed
```

A running hold with no `steps` is free. `est_start` is slurm's guess and moves.

## Use one

```
id=$(marlowe-hold-pick batch8)        # claims an idle running hold (most time left) and prints its id; exit 1 if none
```

then from the project's roach environment:

```python
submit(..., cluster=marlowe.MARLOWE, resources=<shape that fits the hold>, inside=id)
```

`1gpu` -> `dataclasses.replace(marlowe.H100_PREEMPT, gpus="1", exclusive=False)`; `8gpu` -> `marlowe.H100_PREEMPT`; `batch8` -> `marlowe.H100`. Submit within the idle window of the claim.

- Work inside a hold dies with it (preemption, its time limit) and nothing requeues it: only resumable work, resubmitted by `run_id`.
- Holding or extending `batch8` spends pm07's shared GPU-hours: use it, and extend it, only for work the human asked to run on Marlowe.

## Keep an idle hold a while longer

```
marlowe-hold-extend <id>              # SIGUSR2 to the hold: its idle clock restarts (2 h for batch8)
```

It refuses holds submitted before holds handled USR2, where the signal would end the hold instead. USR2, not USR1: roach jobs use USR1 to wrap up and checkpoint, so never send USR1 to a hold or to the jobs in it.

## Let a hold go

```
marlowe-hold-release <id>             # running: TERM to the hold only; it releases once no job is running in it. queued: scancel
```

In the live view (`marlowe-holds` in a terminal): up/down selects a hold, `e` extends it (USR2), `t` terminates it after a y/N prompt (the same as marlowe-hold-release). Release only holds you claimed or the human asked to let go.

## Not yours to change

The pool's schedule, caps and kinds are the human's. Logs: `marlowe:~/scratch/marlowe-pool/{cron.log,logs/hold_pool-<kind>_<id>.out}`.
