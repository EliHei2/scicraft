<!--
Report of a regression hunt, written before any code is changed. Delete these comments before use.
-->
**Symptom.** [metric] went from [last-good value] ([run, date, commit]) to [current value] ([run, date,
commit]). [How it was measured; same data and same command, or not.]

**First output that differs.** [artifact, for example the raw predictions table before aggregation]:
[the number in each run, for example its row count]. Everything upstream of it matches:
[what was compared].

**Code between the two versions.** `git log [last-good]..[current] -- [paths]`: [N] commits. The ones
that touch the stage above: [sha subject], [sha subject].

**Hypotheses, most likely first.**

| # | Hypothesis | Evidence so far | Check that settles it | Cost |
|---|---|---|---|---|
| 1 | [cause] | [file:line, diff hunk, count] | [one command] | [minutes] |
| 2 | [cause] | [evidence] | [command] | [minutes] |

**Not yet ruled out.** [environment, package versions, data version, stale results computed with old
code, different filters between the runs.]

**Proposed fix, not applied.** [The smallest change to the divergent stage only; later intentional
fixes kept.] Waiting for a go.
