---
name: result-reporting
description: Standards for writing up experiment or sweep results - saving a
  reusable result object per run, generating the results markdown from those
  objects rather than by hand, and the provenance file that maps every reported
  number back to the job, node and commit that produced it. Use when presenting
  experiment results, building a results table or report, collating runs of a
  sweep, or deciding what run metadata to record.
---

# Reporting experiment results

Standards for any experiment, not a recipe for a particular one.

1. **Every run saves its own result object** (pickle) in its experiment
   directory: the metric, the predictions, the labels and the config. Results
   must be reusable later without rerunning anything.
2. **Reports go in `results/`** in the task directory.
3. **Tables are generated from the result objects by a script, never typed by
   hand.** The report states which script produced it, when, and from where,
   and says not to hand-edit it. Any number quoted in prose is read from the
   generated file.
4. **The report names the paths to both trees**: the result objects, and the
   slurm log directory — the logs hold per-run metadata worth keeping (the
   submitted arguments, the dependency lock, and stdout with the job id, node
   and commit). Alongside the report, generate a **provenance file** (below).
5. **Say what an uncertainty is.** Distinguish std over repeats from the
   standard error of the mean.
6. **Anything incomplete or mixed is stated in the report**, not left implicit:
   missing repeats, runs from different code or hardware, results excluded from
   a table.

## Provenance file

A generated CSV, **one row per run attempt** — not per result. Failed attempts
stay in it: they explain gaps, and they localise a failure mode that a summary
would hide.

| group | columns | why |
|---|---|---|
| point | the experiment's own axes (seed, size, variant, ...) plus the dataset/task key | so a row joins to the results table; a number with no path back to a job is not reproducible |
| job | `run_id`, `job_id`, output dir or arm name | the handle for `sacct`, and for finding the logs |
| where | `node`, and card/accelerator type if the sweep used more than one | two runs differing only by hardware differ numerically; you need to be able to see that |
| what | `commit`, path to the dependency lock | a sweep assembled over several waves mixes code versions |
| outcome | did this attempt produce a result, state, elapsed | distinguishes "failed" from "never submitted", and an outlier elapsed usually means it ran somewhere unintended |
| paths | stdout log, submitted-arguments file, dependency lock | the report points at them rather than copying their contents |

Summarise the distinct nodes and commits in the report itself — if either has
more than one value, say so where the tables are, not only in the CSV.
