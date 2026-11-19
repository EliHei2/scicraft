# Choosing the skill set

## Inputs, by weight

1. **The author's named requests**, numbered in the state file. In the original build they arrived in
   six messages over one day: the whole package; then named crafts (prompt making, QC, humanizing,
   poster, presentation, paper making, journal methods writing, ML paper writing, updates to existing
   skills); then sharing with two labs and keeping cluster material internal; then how to organize a
   project; then "every hard skill and piece of work must be somewhere in the set"; then where and how
   to share. Each request became a skill, a section, or a step of the build.
2. **Candidate skills across findings files** (section 8 of each). Run:

   ```bash
   python3 scripts/tally_findings.py [ws]/findings --json [ws]/tally.json
   ```

   The table gives rules, procedures and failures per file; the candidate list gives every name that
   more than one file proposed, with its count. Names differ between miners ("brief-writing",
   "prompt making skill"): merge by what the candidate must contain, not by its name.
3. **Tag counts.** A theme tag with many rules across files and no candidate is a skill nobody named.
   A tag with few rules folds into a neighbor.
4. **The author's existing skills.** Each is ported whole (when it is already the model), merged with
   another (two schematic skills became one with two primitive packs), or retired with its useful
   habits moved elsewhere. Never leave an old skill and a new one covering the same task.

## Boundaries

Write one sentence of scope per skill, then check every pair that could overlap. The cuts that held:

| Pair | Split |
|---|---|
| process and style | one skill develops a figure from claim to panels; another owns the plotting style |
| writing a brief and running agents | one owns the text of the brief; the other fan-outs, recovery, cost |
| a single gate and a multi-agent audit | the everyday check before handover; the finder and verifier campaign |
| a general method and a dated field snapshot | general evaluation method; a separate dated skill of one field's tools and traps |
| core and institute | the scheduler-neutral cluster method in core; queues, storage and hosts in the internal plugin |

Every brief lists all siblings by name, so a writer points to the owner instead of repeating it. The
original build carried 46 names in that list.

## Plugins

Group skills by who installs them (tiers in `references/tiers-and-integrity.md`): a core plugin, one
plugin per field, an internal plugin in a separate package that never goes public. In the original
build: a core of 31, an ML plugin of 9, a biology plugin of 5, and an internal plugin of 1.

## The spec

One row per skill. `assets/skill_spec.example.json` has the shape; `scripts/make_briefs.py` turns it
into briefs.

| Field | Holds | Example of a good value |
|---|---|---|
| plugin | the tier it ships in | `ml` |
| scope | one sentence: what it is for, for whom | "Evaluating and comparing models: metric design and trust, controls, benchmark fairness, leaderboards" |
| must | the list of what it must contain, specific enough to check | "a metric a trivial solution can win is not a metric; planted-truth tests; floor, ceiling and null controls; ..." |
| primary | findings codes read fully (one to five) | `["K4", "A6"]` |
| secondary | `"CODE: rules tagged X"` or `"CODE: R12-R18, P3"` | `"H4: R22-R27, P5"` |
| existing | files to port, each with what to keep and what to strip | "the existing deck skill: copy whole, strip institute names" |
| notes | decisions already made: the lead example, what moves to a sibling, the integrity guard, what to run | "Lead with tabular examples; wording of statistics lives in the stats skill" |

- **Name the integrity guard in the notes** of every skill whose findings record a request to hide or
  dilute results (section 10 of those files). Writers then encode the honest form without having to
  find the request themselves.
- **Say what to run.** "Render two demo panels from synthetic numbers and look at the PNG" is a
  decision; "test it" is not.
- **Secondary sources are cheap to name and expensive to read.** Name rules or tags, so the writer
  greps instead of reading a whole file.

## When the set changes during the build

Late findings add skills (in the original build, a dated snapshot skill for one model family and a
distribution-comparison skill came from the second wave). Add the row, regenerate only that brief with
`--only`, and queue it. A skill split or merged after briefs went out needs a message to every writer
whose sibling list changed.
