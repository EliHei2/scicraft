# Release by distillation

The release repository is a new repository built from the research repository at one commit, pruned until only
what the release configuration reaches is left, and accepted round by round against golden files frozen from the
original code. It never is a cleaned copy of the research repository with its history.

The instance it comes from: a foundation-model paper whose research repository had grown to about 11,600 lines
of code, many ablation arms, a benchmark harness, operations scripts and dozens of internal Markdown files. The
author asked for "a cleaned up repo and on github, so people can read it and work on it, wihtouht all of our
crazy md files and what not. keep it clean ... and keep code minimal, but make sure it reproduces the good
restuls".

## Contents

1. Stage 0: export the code and pin what was run
2. Golden files before any change
3. Prune by evidence
4. Gates after every round
5. Fresh history and the repository name
6. Release candidates and the hand-off folder
7. The brief for a remote build agent
8. Dates and the give-up order
9. Disk caps

## 1. Stage 0: export the code and pin what was run

- **Export with `git archive`, never a checkout.** Another session (a running campaign, a cluster agent) may own the
  research tree; `checkout`, `switch`, `stash` or `worktree add` would rewrite it under that session. An
  adversarial read of the release brief caught this: the brief said "read only" and still asked for code at a SHA.

  ```bash
  mkdir -p "$WORK/code_release"
  git -C "$RESEARCH_REPO" archive <CODE_SHA> | tar -x -C "$WORK/code_release"
  git -C "$RESEARCH_REPO" log -1 --format='%H %ci %s' <CODE_SHA> > "$WORK/CODE_SHA.txt"
  ```

- **Record the checkpoint, the config and the inference settings that produced the paper's numbers.** If any of
  the three cannot be identified with certainty, stop and ask. Guessing here makes every later gate meaningless.
- **Diff the snapshot the config names, not live `src/`.** In the instance, the frozen design of the reported
  model lived in a source snapshot named in the config header, while live `src/` had moved on. A distillation that
  read `src/` would have shipped a model without its training schedule.
- Check the published names before anything else: the package index (PyPI), the documentation host, the code host
  and the model hub. The import name may differ from the distribution name when the distribution name is taken.

## 2. Golden files before any change

Freeze outputs of the original code, on public inputs only, before the first line is deleted. Each later round
is accepted against them.

| Golden set | What it holds | How the tolerance is set |
|---|---|---|
| inference (`embed/` in the instance) | three public inputs at two precisions (fp32 and mixed precision), output samples, per-unit sums, input sha256 | encode the same input twice, fp32 against autocast, and take that distance |
| training (`train/`) | one batch on CPU in deterministic mode: every loss term and per-parameter gradients | run the original twice and measure its distance from itself |
| benchmark (`bench/`) | per-fold scores of the reported configuration | encode twice (fp32 against autocast) and rescore |

- **Tolerances are measured, never guessed.** The reviewer of the brief put the reason plainly: measured
  tolerances keep "a correct clean-up" from being "rejected for rounding noise", and a guessed loose one lets a
  real change through.
- Golden inputs are public, so the golden files can be committed (small tensors into `tests/`) or shipped.
- Store the command that produced each golden file beside it.

A non-ML instance: a segmentation or analysis package keeps the per-sample outputs of three public samples and the
benchmark table, with tolerance from running the original twice with different thread counts.

## 3. Prune by evidence

1. Run the release configuration under coverage: one training step plus one whole-sample inference.
   `python -m coverage run -m <pkg>.train --config configs/release.yaml --max-steps 1`, then the inference entry
   point, then `coverage report -m`.
2. Delete code that was never reached.
3. **An option whose release value is the only value kept becomes a constant.** "No dead options, no leftover
   experiment, no unexplained constant."
4. Rename to the paper's terms. The first line of each module names the part of the paper it implements.
5. Report lines of code before and after per module. The instance aimed at about half (11,600 to about 5,800),
   with the rule "never trade a gate or readability for the count".

## 4. Gates after every round

Run all gates after each pruning round. Revert the round that breaks one; do not patch forward.

| Gate | Passes when |
|---|---|
| A1 weights | the release weights load with no missing and no unexpected keys |
| A2 inference | per-element cosine at least 0.99999 against the fp32 golden output |
| A3 benchmark | every fold score inside the measured tolerance |
| A4 training | gradients within 1e-4 relative L2 (or 10 times the code's distance from itself), then 300 steps inside the health range of the last 5,000 steps of the original run |
| A5 environments | fresh installs on Python 3.10 and 3.12 and two framework versions |
| A6 field test | 20 diverse public samples with default settings and no error; the time and memory table goes into the docs |

- A gate counts only when its command, run from a clean shell, prints the measured value into the status file.
  "Never ship 'close enough'."
- A tidy-up fix to a low-priority audit finding twice produced a worse bug in the instance (a crash that killed a
  run, a broken null). Re-run the gates after small fixes too.
- A new test counts only if it fails when its fix is reverted. Two tests in the instance were decoration.

## 5. Fresh history and the repository name

- The public repository starts with fresh history. The research history holds campaign names, internal paths
  and assistant traces in commit messages.
- When the public repository should carry the project's name: rename the private research repository first
  (`<name>-campaign`), re-point every remote that pushes to it (the cluster clone included), then create the public
  one. Otherwise a routine push from the cluster sends campaign history into the public name.
- Commits in the public history are authored by the people releasing it, with no assistant attribution lines
  (section 3 of SKILL.md).

## 6. Release candidates and the hand-off folder

When one machine builds and another checks and publishes, hand over in numbered rounds: `rc1/`, `rc2/`, `final/`.
Each holds:

```
rcN/
├── <name>.bundle        git bundle create <name>.bundle --all  (the public repository)
├── SHA256SUMS           shasum -a 256 of every file here
├── hub/                 model files, model card, data samples
├── docs_html.tar.gz     the built documentation
├── FACTS.md             every number in the README and docs, with its source file
├── NOT_IN_PAPER.md      what the code discloses that the paper does not
├── REPORT.md            gates with measured values, line counts, what is open
└── LEAKSCAN.txt         the leak scan output of the build side
```

The receiving side runs `scripts/check_release.sh rcN` (checksums, clone, leak scan of repository, history, hub
and docs, sizes, clean install and tests, quickstart, docs build) and publishes only after it passes and the
author says yes.

## 7. The brief for a remote build agent

When the build runs on a cluster under its own agent, the laptop writes one brief and the cluster agent carries
it out. The skeleton that worked (see the `prompt-writing` and `cluster-jobs` skills for the general form):

1. The job, with the author's own words and the done-tests.
2. Names and places: every path and id once, in one table.
3. Rules: disk caps, nothing deleted without the author's go, privacy, provenance, no claims, compute, **no pushes
   from the cluster**, gates, scope.
4. How to work: a state file for context resets, a decisions file with one line per choice, a proposals file for
   ideas ("not into code"), one agent per front and at most three, the refactor kept in one pair of hands.
5. Stage 0 (section 1 above).
6. One front per deliverable (package, docs and notebooks, model hub files, demo, site figures), each with numbered
   gates.
7. Order and dates.
8. The hand-off layout (section 6).
9. Final audits by fresh agents that have not seen the brief: a newcomer who installs from the README, a demo user
   who then tries five inputs chosen to break it, a leak scan with zero hits, a consistency check from a clean clone,
   every number traced.
10. What to ask the author, and nothing else.

Work that is not the release (an internal model, in-house outputs) goes into a second file the agent opens only
after the release candidate is handed over. Before sending, one read-only reviewer reads the brief cold; verify each
of its factual claims in the code before applying it. On a rewrite, keep v1 and diff mechanically for lost paths,
file names and numbers. Then say where the agent will find the brief and give the one line to paste into its chat.
"Where can the cluster one find these??" was the correction when that step was missing.

## 8. Dates and the give-up order

Write dates as "day N after start", with a final-files date and a launch date. Name what is dropped first when time
runs out: extra figures and later notebooks go first; the gates, the quickstart, the model files, the docs build
and the demo never do.

## 9. Disk caps

On a shared quota: a status line on disk use at every milestone, never below 15% free, caps per front (in the
instance: clean repository 100 MB, environment 12 GB, temporary environments 15 GB, golden files 20 GB). "Delete
your own intermediates once a result is verified. Report what you removed."
