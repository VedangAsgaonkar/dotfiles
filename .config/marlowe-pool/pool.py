import dataclasses
import subprocess
import sys

from roach.slurm import hold
from roach.slurm.clusters import marlowe

LOCAL = dataclasses.replace(marlowe.MARLOWE, submit_host=None)

KINDS = {
    "1gpu": dict(
        resources=dataclasses.replace(
            marlowe.H100_PREEMPT, gpus="1", exclusive=False, exclude="n26", time="1:00:00"
        ),
        per_round=4,
        rounds_per_48h=48,
    ),
    "8gpu": dict(
        resources=dataclasses.replace(marlowe.H100_PREEMPT, exclude="n26", time="4:00:00"),
        per_round=2,
        rounds_per_48h=12,
    ),
}


def waiting(name: str) -> int:
    out = subprocess.run(
        ["squeue", "-h", "-u", subprocess.getoutput("id -un"), "-n", f"hold-{name}", "-t", "PENDING", "-o", "%i"],
        capture_output=True, text=True, check=True,
    ).stdout
    return len(out.split())


def main(kind: str) -> None:
    k = KINDS[kind]
    name = f"pool-{kind}"
    cap = k["per_round"] * k["rounds_per_48h"]
    w = waiting(name)
    n = max(0, min(k["per_round"], cap - w))
    print(f"{subprocess.getoutput('date -Is')} {name}: {w} waiting, cap {cap}, submitting {n}")
    for _ in range(n):
        hold(k["resources"], cluster=LOCAL, name=name, log_root="~/scratch/marlowe-pool/logs", idle_exit_secs=900)


main(sys.argv[1])
