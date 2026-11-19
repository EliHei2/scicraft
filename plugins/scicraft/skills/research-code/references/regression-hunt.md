# Regression hunt

The procedure for "it used to work", "the numbers got worse", "this does not match what we had last week".
The hunt in the source work took about 20 prompts over one day because the agent first explained from memory,
then patched, then found the cause at the first stage of the pipeline.

## 1. Inspect only until told to fix

The default mode is read-only. "don't change anything, just inspect why"; "don't add anything, just give me some
answers to probe what might have gone wrong." Every patch made during the hunt is a second change between the
last-good state and now, and makes the hunt longer. Fix only after the owner says go.

## 2. Pin both ends

| End | What to collect |
|---|---|
| last good | the run folder, its date, its config or command line, the commit (from a stamped commit file, the run manifest or the date), the environment |
| now | the same for the failing run |
| symptom | the one number that moved, its value in both runs, how it was measured |

If the owner gives a date ("what changed in comparison to 3-4 days ago"), find the commit:

```bash
git log --all --since='<date> 00:00' --until='<date> 23:59' --format='%h %ad %d %s' --date=iso
git rev-list -1 --before='<date of the good run>' <branch>      # the commit that was current then
```

Check the comparison is fair before reading code: same data, same command, same filters, same metric version.
Results computed with old code are a common confounder. In the source work a metric rewrite was reverted, and
the revert itself was reverted when the "regression" turned out to be the external methods' scores computed
with the old implementation. Record the code version and filter settings next to every results table so this
can be checked.

## 3. Find the first stage whose output differs

Compare artifacts in pipeline order and stop at the first one that differs:

| Stage | What to compare |
|---|---|
| input after reading | row count, columns, value ranges, null counts |
| after each filter | rows in and out (section 6 of `change-discipline.md`) |
| model or algorithm output (raw table) | row count, assigned fraction, distribution of scores |
| post-processing (thresholds, recovery, merges) | rows changed, ids per row |
| aggregation (tables, matrices) | totals, per-group counts |
| metrics and plots | the symptom |

"the problem shows up already at the initial predicted assignments ... not anndata." Everything downstream of
the first differing stage is a consequence; do not read it.

## 4. Diff the code of that stage only

```bash
git log --oneline <last-good>..<now> -- <paths of that stage>
git diff <last-good> <now> -- <paths of that stage>
git diff <last-good> <now> -- '*.py' | grep -nE '^[-+].*(default|threshold|scale|filter|min_|max_)'
```

Read the reader, filters, graph or feature construction, scaling, thresholds and defaults. The hypotheses the
owner raised in the source hunt ("maybe the scaling? maybe points in polygon") were the right places to look.
Then compare against upstream `main` as well, since a local branch may carry an unreviewed change.

When the range is long and the stage output is cheap to produce on a small input, let git bisect find the commit:

```bash
git bisect start <now> <last-good>
git bisect run python3 check_stage.py      # exits 0 when the stage output matches the good run, 1 otherwise
git bisect reset
```

`check_stage.py` runs only the divergent stage on a small fixed input and compares one number with the good
value. Suggested, not yet tested in real work: the source hunts diffed by hand.

Check the environment and package versions only after the code ("could it be a version problem??").

## 5. Coincidences are bugs until cleared

When outputs match too well, or a magnitude is off, write a one-line check and run it before explaining anything.
Each row below was a real bug in the source work:

| Observation | One-line check | What it was |
|---|---|---|
| identical statistics for every split | count overlapping row keys between split outputs | splits that shared rows |
| 8 GPUs requested, speed of 1 | grep the log for the device count the job actually used | all shards ran on one GPU |
| a method suspiciously close to the baseline | compare cell or object sizes and the mode used | the wrong mode for compact objects |
| fewer objects than the baseline where more are expected | check labels against geometry and counts | swapped labels in an export |
| "1 billion rows" in the data, "11 million" in the report | read the row count from the row index | a wrong count in the report |

A flat or lopsided result (a volcano plot with no hits, far more positive than negative effects) is treated the
same way: check normalization, the unit of replication and the n per group before any interpretation.

When the owner sees a contradiction in a picture ("I see it!"), believe the picture and check labels against
geometry and counts first. An agent once defended an export whose labels were swapped.

## 6. Report, then fix

Write `assets/regression_report.md`: symptom, first differing output, commits in range, hypotheses ranked with
the check that settles each and what it costs, what is not yet ruled out, the proposed fix. Then wait.

After the go:

1. Fix only the divergent stage.
2. Keep later intentional fixes ("without touching the fixed reader filtering").
3. Rerun the stage and compare with the old numbers; state any remaining difference and its cause.
4. Write the cause into the project's docs or lab notebook so it is not hunted twice.

## 7. Answering pushback on results

When the owner says a result "simply can not be true", recompute it from the raw metric on the same data and
show the computation. Do not search settings until the preferred method wins. A choice made after seeing results
(a threshold picked because it matches the baseline) is allowed only when declared as post-hoc wherever the
result is reported. `stats-reporting` and `integrity-audit` cover reporting the outcome.
