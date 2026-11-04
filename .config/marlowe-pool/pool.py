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
        every_h=1,
        idle_exit_secs=600,
    ),
    "8gpu": dict(
        resources=dataclasses.replace(marlowe.H100_PREEMPT, exclude="n26", time="4:00:00"),
        per_round=2,
        every_h=4,
        idle_exit_secs=900,
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
    cap = k["per_round"] * 48 // k["every_h"]
    w = waiting(name)
    if why == "empty" and w:
        return
    n = max(0, min(k["per_round"], cap - w))
    print(f"{datetime.now().isoformat(timespec='seconds')} {name} ({why}): {w} waiting, cap {cap}, submitting {n}")
    for _ in range(n):
        hold(k["resources"], cluster=LOCAL, name=name, log_root="~/scratch/marlowe-pool/logs", idle_exit_secs=k["idle_exit_secs"])


def tick() -> None:
    now = datetime.now()
    for kind, k in KINDS.items():
        scheduled = now.minute < 5 and now.hour % k["every_h"] == 0
        submit(kind, "round" if scheduled else "empty")


if sys.argv[1] == "tick":
    tick()
else:
    submit(sys.argv[1], "round")
