import dataclasses
import subprocess
import sys
from datetime import datetime

from roach.slurm import hold
from roach.slurm.clusters import marlowe

LOCAL = dataclasses.replace(marlowe.MARLOWE, submit_host=None)

KINDS = {
    "1gpu": dict(
        resources=dataclasses.replace(
            marlowe.H100_PREEMPT, gpus="1", exclusive=False, exclude="n26", time="1:00:00"
        ),
        per_round=4,
        hours=set(range(24)),
        refill_when_empty=True,
        cap=192,
        idle_exit_secs=600,
    ),
    "8gpu": dict(
        resources=dataclasses.replace(marlowe.H100_PREEMPT, exclude="n26", time="4:00:00"),
        per_round=2,
        hours={0, 4, 8, 12, 16, 20},
        refill_when_empty=True,
        cap=24,
        idle_exit_secs=900,
    ),
    "batch8": dict(
        resources=dataclasses.replace(marlowe.H100, exclude="n26"),
        per_round=1,
        hours={9, 21},
        refill_when_empty=False,
        cap=4,
        idle_exit_secs=7200,
    ),
}


def waiting(name: str) -> int:
    out = subprocess.run(
        ["squeue", "-h", "-u", subprocess.getoutput("id -un"), "-n", f"hold-{name}", "-t", "PENDING", "-o", "%i"],
        capture_output=True, text=True, check=True,
    ).stdout
    return len(out.split())


def submit(kind: str, why: str) -> None:
    k = KINDS[kind]
    name = f"pool-{kind}"
    w = waiting(name)
    if why == "empty" and w:
        return
    n = max(0, min(k["per_round"], k["cap"] - w))
    print(f"{datetime.now().isoformat(timespec='seconds')} {name} ({why}): {w} waiting, cap {k['cap']}, submitting {n}")
    for _ in range(n):
        hold(k["resources"], cluster=LOCAL, name=name, log_root="~/scratch/marlowe-pool/logs", idle_exit_secs=k["idle_exit_secs"])


def reap() -> None:
    names = ",".join(f"hold-pool-{kind}" for kind in KINDS)
    ids = subprocess.run(
        ["squeue", "-h", "-u", subprocess.getoutput("id -un"), "-n", names, "-t", "REQUEUE_HOLD", "-o", "%i"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    if ids:
        subprocess.run(["scancel", *ids], check=True)
        print(f"{datetime.now().isoformat(timespec='seconds')} reaped {len(ids)} held: {' '.join(ids)}")


def tick() -> None:
    reap()
    now = datetime.now()
    for kind, k in KINDS.items():
        try:
            if now.minute < 5 and now.hour in k["hours"]:
                submit(kind, "round")
            elif k["refill_when_empty"]:
                submit(kind, "empty")
        except RuntimeError as e:
            why = next((l for l in str(e).splitlines() if "error:" in l), str(e).splitlines()[0])
            print(f"{datetime.now().isoformat(timespec='seconds')} pool-{kind}: submit FAILED: {why.strip()}")


if sys.argv[1] == "tick":
    tick()
else:
    submit(sys.argv[1], "round")
