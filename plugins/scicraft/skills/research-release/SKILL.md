---
name: research-release
description: Releases the code, weights, notebooks, supplementary tables and data of a paper: a fresh public repository distilled from the research code and accepted against golden files, docs and notebooks tested like code, an exactness ledger, whitelisted reference tables, a data deposit with manifest and checksums, a leak scan before every push. Use it whenever work goes public, even unnamed: "clean up the repo for release", "make it public", "put the model on the hub", "docs like scvi-tools", "upload the reproducibility data", "supplementary tables", "push the exact benchmark code", "camera-ready code by Friday", "release our skills plugin". Holds what agents get wrong: copying the research repo, guessed tolerances, per-unit dumps passed off as tables, install lines never run, secrets and agent traces in history, licenses chosen before ownership is settled. Prefer integrity-audit to trace a number, paper-code-parity to keep code and paper in step, project-structure for layout, paper-website for the page.
---

# research-release

How to release what a paper was built on (code, weights, notebooks, supplementary tables, data) so that a
stranger can install it, reproduce the numbers and build on it, and nothing private leaves the machine. Distilled
from the author's release of a foundation model's code and weights, the reproducibility notebooks and data deposit
of a benchmark paper, and the public push of a benchmark metric that had to be the exact code that ran.
The author's standard: "a cleaned up repo and on github, so people can read it and work on it ... keep code minimal, but
make sure it reproduces the good restuls".

> **PRIME DIRECTIVE: a release is built fresh from the exact code and data that produced the paper, accepted only
> by measured gates, and scanned for leaks before every push. Nothing goes public before the author has settled
> who owns it and under which license.**

Three failures cost the most time. Guard against them from the first minute:

1. **Releasing a cleaned copy of the research repository.** History full of campaign names and agent traces,
   internal Markdown, dead options, a frozen design that lived in a snapshot while the distillation read live code.
   Build a new repository from `git archive` and prune against golden files (sections 2 and 3).
2. **Delivering the wrong kind of file.** Dozens of per-panel CSVs (embedding coordinates, per-unit tables) were
   uploaded as "supplementary tables" when the co-authors' example held a few short reference tables, and the
   author rejected them. Open the existing example, match its type and count,
   stage by whitelist (section 7).
3. **Publishing what cannot be taken back.** A token, a home path or a co-author's draft in a public history, or a
   permissive license on code the institute had a say in. Scan every push; settle license and IP first (sections 1
   and 10).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **What is released**: code, weights, notebooks, supplementary tables, data, a demo, a skills package. Each has
  its own destination and section below.
- **The exact state that produced the paper**: repository, commit, checkpoint, config and inference settings, the
  results table every figure reads. If any cannot be identified with certainty, ask before building.
- **The existing examples**: the co-authors' tables already on the shared drive, an earlier deposit, a package
  whose documentation the author likes (scvi-tools and ComplexHeatmap were the author's picks).
- **Who decides**: ownership, the institute's policy, the license; whether in-house data or an internal model
  exist; who may push and publish.
- **Where the build runs**: the laptop, or a cluster under its own agent; disk quotas; the deadline and what may
  be dropped first.

Work in a release folder beside the research repository, never inside it:

```
<project>-release/
├── code_release/      git archive of the research commit, pruned into the new repository
├── golden/            frozen outputs of the original code, with the command for each
├── inbox/rcN/         release candidates handed over by the build side
├── checks/rcN/        results of scripts/check_release.sh
├── deposit/           data deposit with MANIFEST.tsv and SHA256SUMS
├── stage_tables/      staged supplementary tables (scripts/stage_whitelist.py)
└── FACTS.md, NOT_IN_PAPER.md, EXACTNESS.md, license_ip_checklist.md
```

## 1. Settle license and IP first

The license is a decision for the author and the institute; the agent collects facts and blocks publishing until
the questions are answered. A permissive release cannot be withdrawn: "One can open up later, never close again."

- **Work through the questions in `references/license-ip.md`** with the author (fillable copy in
  `assets/license_ip_checklist.md`): who owns code and weights, the institute's policy, grant conditions, what is
  already disclosed and where grace periods apply, what the code discloses beyond the paper, patents, dependency
  and dataset terms, one license per artifact, what stays private.
- **Never give legal advice and never pick a license.** Give facts with sources and say that the technology-transfer
  office or an attorney gives the binding answer.
- **Until decided, the license is one open parameter** in every brief and draft, and no sentence promises free or
  commercial use.
- **List what the code discloses beyond the paper** in `NOT_IN_PAPER.md` (`assets/not_in_paper.md`) before anyone
  decides. Code reveals the recipe the paper summarizes.

## 2. Distill a fresh repository

Detail, numbers and the gate table are in `references/distillation.md`.

- **Export with `git archive`, never a checkout**:
  `git -C "$RESEARCH_REPO" archive <CODE_SHA> | tar -x -C "$WORK/code_release"`. Another session may own the
  research tree, and a checkout rewrites it under that session.
- **Diff the snapshot the config names.** A frozen design can live in a snapshot while live `src/` has moved on.
- **Freeze golden files before the first deletion**, on public inputs: inference outputs at two precisions,
  one deterministic CPU training batch with every loss term and gradient, per-fold benchmark scores.
- **Measure every tolerance by running the original against itself** (fp32 against mixed precision, twice with the
  same seed). Guessed tolerances either reject a correct clean-up for rounding noise or pass a real change.
- **Prune by coverage**: run the release config for one training step and one inference under `coverage`, delete
  what was never reached, turn single-valued options into constants, rename to the paper's terms. The instance
  went from about 11,600 to about 5,800 lines: "never trade a gate or readability for the count".
- **Gates after every round; revert the round that breaks one**: weights load with no missing or unexpected keys;
  per-element cosine at least 0.99999; fold scores inside the measured tolerance; gradients within 1e-4 relative L2
  (or 10 times the self-distance) and 300 healthy steps; fresh installs on Python 3.10 and 3.12; a field test on 20
  public samples.
- **Check the name first** on the package index, the docs host, the code host and the model hub, before any
  repository or account is created (`references/public-repo-and-docs.md`, section 7).
- **Fresh history.** Rename the private research repository and re-point its remotes before the public one takes
  the name, so no routine push sends campaign history into it.

For a non-ML package the same holds with other golden files: per-sample outputs of three public samples and the
benchmark table, with tolerance from two runs of the original.

## 3. What the public repository holds

| In | Out |
|---|---|
| README, LICENSE, CITATION.cff, pyproject.toml, CHANGELOG.md, THIRD_PARTY.md | benchmark harness, ablation arms, comparators |
| `src/<pkg>/`, each module's first line naming its paper part | operations and scheduler scripts, campaign documents |
| `configs/`: the release recipe and one tiny test config | internal Markdown and agent files (CLAUDE.md goes in `.git/info/exclude`) |
| `docs/` with the notebooks | the internal checkpoint, in-house outputs |
| `tests/`: CPU, under 2 minutes, small committed golden tensors | data, results, files over 50 MB |
| CI: tests, docs build, package publishing | code under non-commercial or copyleft licenses |

- **No assistant attribution in anything a lab or the public reads.** "people won't trust it if it has your sign
  all over it." Commits are authored by the people releasing them.
- **The four done-tests**: a newcomer installs and gets a result and a figure from six pasted lines in one minute;
  a fresh agent with only README and docs completes the main tasks in ten minutes; two minutes on the demo;
  "nothing needs an apology" (no dead option, leftover experiment, unexplained constant or file of unclear purpose).
  Run the first two with fresh agents and fix every stumble in the product.
- **A release that invites continued training ships what it needs** (target encoder, predictor, optimizer state in
  a second weights file), and the author is told those become public too.
- **When in-house data exist, keep two models**: a public checkpoint trained on public data, and an internal one
  that never leaves the cluster.
- Files, model card, demo and versions: `references/public-repo-and-docs.md`.

## 4. Documentation and notebooks, tested like code

- **Docs gates**: `sphinx -W` (warnings are errors) and linkcheck pass; every public name has a docstring with an
  example that runs under doctest; every notebook runs from a fresh kernel; a Troubleshooting page lists each error a
  user can meet with its fix; the field-test time and memory table is in the docs.
- **Notebooks are the reproducibility record and the tutorial at once.** One percent-format builder per notebook;
  the paper build sets `PAPER_*` flags, the tutorial build turns them all off (asserted) and runs the method. Each
  notebook starts from the data download and a command-line run at a pinned commit and writes a standard format.
  Build both with `scripts/nb_build.py` (`--tutorial` for the second); when only markdown changed, copy outputs
  with `scripts/transplant.py`, which refuses when any code cell differs.
- **Tutorial limits**: six notebooks, one question each, under 5 minutes on one 24 GB GPU, at most 15 code cells of
  at most 10 lines, data through `pkg.datasets.<name>()` with a pinned md5, under 2 MB with outputs. Helpers belong
  in the package.
- **Clean outputs before commit** with `scripts/clean_notebook_outputs.py` (`--check` as a gate).
- **Mark what was not run.** Every install line, platform or command you could not run gets `UNTESTED` beside it in
  the docs and a line in the report.
- Procedure and rules: `references/notebooks-and-exactness.md`; docs stack and pages:
  `references/public-repo-and-docs.md`.

## 5. The exactness ledger

- **One row per reproduced figure or table value**: paper value, notebook value, status (exact, printed precision,
  differs, not reproducible here) and why. Template in `assets/exactness_ledger.md`.
- **Ship on the ledger, then iterate.** Chasing a 0.4% difference past the deadline drew "frustrated by
  over-iteration".
- **A difference stays in the ledger with its size.** A recompute never silently replaces a printed value; the
  difference goes to the author, and a suspected cause is marked `UNCONFIRMED` until shown.

## 6. The hosted demo

- **Specify it as the visit**: a cached example on opening, a preview in seconds, one button, views that appear in
  turn, recoloring without recomputing.
- **Its checks**: ten broken inputs each give a one-sentence fix; two sessions at once; phone and desktop.
- **Give it a sunset date**: paid hardware is usually offered for a fixed period, so plan the end date and make
  sure it still runs as a page on free hardware afterwards. The paid tier fits the largest input users will bring.

## 7. Supplementary tables by whitelist

- **Open the co-authors' existing tables first** and match their type, granularity and count (10 to 15 files in the
  instance). List each example with rows and columns and one line on what kind of thing it is.
- **A reference table holds what the analyses use and the paper does not print**: feature or gene lists, pairs used
  by a metric, default parameters, dataset and split tables with identifiers, licenses and URLs, software versions,
  parameter sweeps. Never per-unit plotted values, raw tables or README padding.
- **"what we see in paper should be what we see in the csvs"**: build each table from the paper's own sources and
  proofread every value against the paper.
- **Stage by explicit whitelist** with `scripts/stage_whitelist.py` (`assets/whitelist.example.tsv`); show the staged
  list to the author before asking for approval.
- Names in the co-authors' scheme, numbered by first citation in the latest manuscript. When tables are missing,
  `scripts/supptables_from_tex.py` lists the citation order and turns each labeled LaTeX table into a CSV
  (procedure in `references/deposits.md`, section 1).

## 8. Data deposits with manifest and checksums

- **Tables and data go to separate destinations**, each with its own manifest. "tabeles are sth but data are sth
  else."
- **Every deposited file can be read on its own.** An output holding only row indices into another table ships with
  that table. One combined file per dataset worked well.
- **Write the manifest and checksums** with `scripts/make_manifest.py` (size, md5, sha256, pinned md5, URL,
  `SHA256SUMS`, upload commands); pass the md5 pins the notebooks check, so a re-exported file fails until re-pinned.
- **Dry run, then copy, then a one-way checksum check** (`rclone check --one-way --checksum`); never `sync`, `move`
  or `delete` into a shared folder; never touch files you did not write.
- **Check link permissions** before handing out a shared folder, and say what it exposes.
- Bulk uploads from a cluster agent, credentials and transfer details: `references/deposits.md`.

## 9. Push exactly the code that ran

When published numbers came from code that has since moved on, the public push is that code: "no new stuff or
correction ... reproducible 1:1".

- **Name branch, commit and date** for every code state you mention; `git ls-remote` before stating a head.
- **Strip what the run did not contain and prove identity** (in the instance: 0 bytecode differences over 141 code
  objects, plus file size and the line of a known warning). Command-line defaults change only when the author
  decides, and the release note says so; otherwise the run value goes into the rerun instruction as the
  benchmark setting.
- **Fast-forward only, never force**; check the remote tip has not moved; download the pushed file and verify it
  again; run the public command line end to end once and report, not fix, what it needs.
- In zsh, brace refs: `git show "${REF}:path"`. Full recipe: `references/exact-code-push.md`.

## 10. Leak scan before every push

- **Run `scripts/leak_scan.py` before every push, upload and deploy**: on the repository with `--git` (history and
  authors), on hub files, on built docs and on every deposit.
- ERROR (exit 1): home and cluster paths, scheduler directives, review-process words, assistant traces, tokens and
  keys (printed masked), every `--private` pattern, the bytes of every `--forbid` file. WARN: leftovers, emails,
  claim words, image metadata, wording under `--style`, every commit author.
- **The project's own names go in a private pattern file outside every repository** (`assets/leak_private.example.txt`).
- **Test the scanner before trusting it**: on the research repository it must light up; on a scratch folder with
  one planted string per class it must report each one.
- What it cannot see (unpublished numbers, a person named in prose, a figure of unpublished data) needs a person
  reading the diff. Detail: `references/leak-scan.md`.

## 11. When the build runs elsewhere

When a cluster agent builds the release, the laptop writes one brief and checks what comes back.

- **Brief**: the job in the author's words with the done-tests, every path once, rules (disk caps and a 15% free
  floor, nothing deleted without the author's go, **no pushes from the cluster**), a state file, one front per
  deliverable with numbered gates, golden files and measured tolerances, dates with a give-up order, final audits by
  fresh agents. Work that is not the release goes in a second file opened only after the release candidate.
- **Say where the agent finds the brief** and give the one line to paste into its chat.
- **Check each candidate** (`rc1/`, `rc2/`, `final/`, each with a git bundle and `SHA256SUMS`) with
  `scripts/check_release.sh`, and publish only on the author's yes.
- Skeleton and hand-off layout: `references/distillation.md`; general brief writing: the `prompt-writing` and
  `cluster-jobs` skills.

## 12. Releasing a package of agent skills

A skills package is released like code: license, leak scan with `--skip "assistant trace"`, version, citation file.
The documented options (public repository as a marketplace, private repository, project settings, organization
rollout, the official directory, versioning with `plugin.json` and `claude plugin tag`, `CITATION.cff` and a Zenodo
DOI per release), checked on 2026-11-18, are in `references/skill-packages.md`. Re-read the official pages before
relying on a detail.

## 13. Check before anything is handed over

In this order:

1. `bash scripts/check_release.sh <rc folder>` with `PKG=<import name>` (and `QUICKSTART`, `PRIVATE`): checksums,
   clone, leak scan of repository, history, hub and docs, sizes and files over 50 MB, clean install and tests,
   quickstart, docs build with warnings as errors. Zero FAIL.
2. `python3 scripts/leak_scan.py` on every other folder that will leave the machine (deposit, staged tables,
   built site). Zero ERROR; every WARN read.
3. `python3 scripts/make_manifest.py` on the deposit: zero MISMATCH or MISSING.
4. `python3 scripts/clean_notebook_outputs.py docs/notebooks/*.ipynb --check` and a fresh-kernel run of each.
5. Distillation gates A1 to A6 with measured values in the status file.
6. Look with your own eyes: the quickstart figure, the rendered README and docs Home, every staged table against the
   paper, the demo on a phone.
7. The license checklist has no open row, and the author has said yes to publishing.
8. In the report, say what was not run (every `UNTESTED` line, skipped steps, platforms not tried) and what the leak
   scan cannot see.

## 14. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| the research repository with its history, cleaned | "wihtouht all of our crazy md files and what not" | a fresh repository from `git archive`, pruned against golden files |
| docs that overwhelm | "not overwhelming, minimal examples, obvious what to do" | docs in the scvi-tools style, tested like code |
| leftovers and odd corners | "code has not hole or werid things!" | the fourth done-test: nothing needs an apology |
| dozens of per-panel CSVs as supplementary tables | "it should be not more than 10-15 files we need max!!!" | reference tables of the co-authors' type, staged by whitelist |
| raw per-unit tables in the tables folder | "tabeles are sth but data are sth else" | a separate data deposit with manifest and checksums |
| ported extras in the metric push | "no new stuff or correction ... reproducible 1:1" | the exact code, identity proven, fast-forward push |
| assistant attribution in shared history | "people won't trust it if it has your sign all over it" | commits by the people releasing, a scan that fails on traces |
| chasing a 0.4% mismatch | "frustrated by over-iteration" | ship on the exactness ledger, then iterate |
| low-resolution notebook plots | "low quality on the ipynb??" | publication-quality inline figures |
| a release message of headings and lettered options | "don't make it such AI ..." | a plan in the author's voice with three questions at the end |
| a brief that stayed on the laptop | "where can the cluster one find these??" | the brief delivered, with one line to paste |
| a checkout in a tree another session used | an adversarial read of the brief | `git archive` of the commit, unpacked into the release folder |

## Reference files

- `references/distillation.md`: stage 0, golden files and tolerances, coverage pruning, gates, fresh history,
  release candidates, the brief for a remote build agent, give-up order, disk caps.
- `references/public-repo-and-docs.md`: in and out, done-tests, docs stack and gates, files every release carries,
  model files, the hosted demo, versions, attribution, the release message.
- `references/notebooks-and-exactness.md`: one source with paper and tutorial builds, the builder and the
  transplant, tutorial limits, output cleaning, the exactness ledger.
- `references/deposits.md`: supplementary tables and building missing ones from the manuscript, whitelist
  staging, data deposits, rclone setup and transfers, cluster-agent uploads, link permissions.
- `references/exact-code-push.md`: naming code states, the push recipe, guaranteeing a job runs the shipped code.
- `references/leak-scan.md`: classes, the private pattern file, testing the scanner, what it cannot see.
- `references/license-ip.md`: the license and IP questions to settle before anything is public.
- `references/skill-packages.md`: distribution options for agent skills and plugins, directory, versioning, credit.

Scripts (Python 3.9 or later, standard library; Pillow optional for image metadata; `check_release.sh` needs bash,
git, shasum and network access for a clean install unless `PIP_ARGS` points elsewhere):
`scripts/leak_scan.py`, `scripts/check_release.sh`, `scripts/make_manifest.py`, `scripts/stage_whitelist.py`,
`scripts/clean_notebook_outputs.py`, `scripts/nb_build.py`, `scripts/transplant.py`,
`scripts/supptables_from_tex.py` (the last three answer `--self-test`). Assets: `assets/CITATION.cff`,
`assets/exactness_ledger.md`, `assets/not_in_paper.md`, `assets/license_ip_checklist.md`, `assets/leak_private.example.txt`,
`assets/whitelist.example.tsv`.
