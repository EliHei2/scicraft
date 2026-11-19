---
name: project-structure
description: Sets up and keeps order in a research project, on a laptop and a remote machine. Produces the folder tree; the four governing documents, each defined exactly (NARRATIVE.md the argument, GOALS.md long goals, the short goal and non-goals, GUARDRAILS.md the invariants, GUIDELINES.md the conventions); a knowledge base; an ignore file with a reason per block; provenance rows; the results-folder contract (config first, manifest last, lineage ids, append-only outputs, archive before overwrite); one settings object with presets. Use it whenever a user starts a repo ("set up the repo", "scaffold this"), asks for project documents ("write the guardrails", "what are our goals", "build a knowledge base"), complains about clutter ("my root is a mess", "which results folder is the real one"), asks where a file goes, syncs laptop and cluster, or says "update docs", even when the skill is not named. Holds a scaffold, a checker for the governing documents, a results store and triage scripts. Git belongs to research-code.
---

# project-structure

How to lay out a research project so that code, data, results and documents each have one home, and how to keep it
that way for a year of work on a laptop and a remote machine. Distilled from about a dozen of the author's
repositories: a model campaign that grew to about 1,460 untracked files, a figure repository, a benchmark rebuild that
replaced about 50 result folders with one lineage, a driver repository for runs of a pinned package, and a tabular
benchmark. Most rules here were learned by cleaning up after their absence.

> **PRIME DIRECTIVE: code, data and results live in separate trees, and anything that crosses from one to another
> leaves a row in a ledger.** A copied input gets a `PROVENANCE.md` row, a run gets a `RUN_MAP.md` row, a
> `config.json` at its start and a `manifest.json` at its end, a superseded output gets a reason in `MANIFEST.tsv`,
> a choice gets a `DECISIONS.md` row.

Three failures cost the most time. Guard against them from the first minute:

1. **Result sprawl.** One project root collected 36 or more timestamped benchmark folders, smoke and check folders
   beside the canonical ones, a "final" folder that turned out misnamed, seven numbered zips of the same repo, a
   65 GB tarball and three virtual environments. Nobody could say which folder fed the paper; a triage of about 50
   folders followed. Months later, with a contract in place, a second results root still ended without a manifest
   and with six sibling folders written by development scripts (sections 4 and 8).
2. **Silent drift.** Counts copied into prose by hand drifted twice in two days. An input copied without a record
   could not be traced or refreshed. Every number and every copy needs a source that a script can check (sections 2
   and 5).
3. **Writes that overwrite.** An rsync from the remote carried `.git` back and the `origin` remote vanished twice in
   one session. Regenerated galleries overwrote panels in place, and the author had to ask "bring back all previous
   figures in the gallery we need them!!!". One machine writes, files move one way per command, and what exists is
   archived before it is replaced (sections 4 and 7).

## 0. Before starting

Read before asking. Collect:

- **What exists.** `ls -la` of the root, the existing `README`, index file (`CLAUDE.md`, `AGENTS.md`), `.gitignore`,
  environment files, and `git status --short | head`. Count loose result folders and big files
  (`du -sh * | sort -h | tail -20`).
- **Where the data lives.** The raw stores, their size, who else reads them, and whether any are licensed or
  in-house (section 2, tiers).
- **Where it runs.** Laptop only, or a remote machine with scratch and persistent areas; how the user reaches it.
- **What the project delivers.** A model, a benchmark table, a figure set, a paper. One deliverable per repository
  (`references/layout.md`).
- **What the project is for.** The long goal, the next milestone with its date, and what is out of scope. They go
  into `GOALS.md` (section 5). When nobody can state them, that is the first thing to settle with the user.
- **What the author gave as input.** A brief, a build prompt, a follow-up message: each goes verbatim into `SPEC.md`
  (section 5).

Ask only what cannot be found, in one message: the raw store paths, the remote address and its result area, the
deliverable, and whether this repository will be shared (a shared repository keeps the agent index out of history;
see `research-code`).

## 1. The tree

Create it with the script, then fill the `[bracketed]` placeholders:

```bash
python3 <skill>/scripts/scaffold.py <project> --name "<Project name>" --package <pkg> \
    --raw <store>=<absolute path of raw store> --remote <user@host:/path/of/project/>
python3 <skill>/scripts/scaffold.py <project> --layout driver     # heavy runs of someone else's package
python3 <skill>/scripts/scaffold.py <project> --dry-run           # print the tree, write nothing
```

The research layout, one line per directory (the script writes these lines into the index file and README):

| Path | Holds | In git |
|---|---|---|
| `src/<pkg>/` | the method; each module's first line says what it implements | yes |
| `src/<pkg>/settings.py`, `store.py` | one config with presets; the results store (section 4) | yes |
| `configs/` | small declarative configs; `paths.env` holds every path once | yes |
| `scripts/` | thin entry points (run, submit, preflight, sync); no logic that belongs in `src` | yes |
| `experiments/` | campaign configs and `EXPERIMENTS.md`, the lab notebook | yes |
| `tests/` | fast CPU tests with small committed baselines | yes |
| `docs/` | reference documents: paper-to-code map, data availability | yes |
| `docs/kb/` | the knowledge base: `INDEX.md` first, one topic per entry, `archive/` for superseded | yes |
| `guidelines/` | topic files of `GUIDELINES.md` (workflow, results contract) | yes |
| `reference/` | frozen baselines and contract files, checked by md5 | yes |
| `data/raw/` | symbolic links to raw stores outside the project | no |
| `data/` | small copied inputs, one provenance row each | no |
| `results/runs/<profile>/` | one root per run profile under the contract of section 4 | no |
| `results/cache/`, `results/aggregate/`, `results/archived/` | downloads, cross-run tables, superseded outputs | no |
| `scratch/` | the smoke profile and throwaway checks, never cited | no |
| `_attic/` | superseded drafts, never built and never cited | no |

At the root: the index file and `README.md` (the map); `NARRATIVE.md`, `GOALS.md`, `GUARDRAILS.md` and
`GUIDELINES.md` (the governing documents); `SPEC.md`, `DESIGN.md`, `NOTES.md`; `STATUS.md`, `RUN_MAP.md`,
`DECISIONS.md`, `PROVENANCE.md`; `.gitignore`. `guidelines/RESULTS.md` states the results contract.
The scaffold never overwrites a file without `--force`, does not run `git init`, and exits 1 when a `--raw` target
does not exist on this machine (expected for a store that lives only on the remote: the link is made, the row says
"target missing when linked", and the report must say the link was not checked).

- **One deliverable and one write target per repository.** When a project grows a second deliverable (figures fed
  by a benchmark), split it into two repositories joined by one named contract file, checked by md5 on every
  regeneration. `references/layout.md` has the variants (driver repository, figure repository, upstream-results
  repository) and the contract pattern.
- **Keep the tracked set small even when the disk is a mess.** One campaign's rule became "the repo is src/ + ops/ +
  docs/ and nothing else": about 1,460 files were dropped from tracking, all still on disk and in history.
- **Superseded drafts go to `_attic/`**, untracked, never built. `git mv` into it stages the attic copy; undo with
  `git restore --staged _attic/...` and commit only the deletion.

## 2. Code and data never mix

- **Never committed:** raw data, copied inputs, run outputs, checkpoints and weights, arrays and tables (`.parquet`,
  `.h5ad`, `.npz`, `.pt`, `.ckpt`, `.safetensors`), archives, logs, compiled PDFs, virtual environments, agent-local
  settings. Small baselines that a test reads go in `reference/` and are re-included by name. GitHub refuses files
  over 100 MB; check for anything over 50 MB before a first push.
- **Every block of the ignore file says why.** The template (`assets/templates/gitignore.txt`) opens each block with
  its reason ("regenerable from tracked code and configs", "one build away from their tracked sources, and binaries
  that churn"). A deliberate exclusion carries the warning "do not fix it by re-adding a path".
- **Raw data is read in place, through links.** `data/raw/<name>` is a symbolic link to the store; the scaffold
  makes it and writes the provenance row. Only documented prep scripts read raw stores; everything else reads small
  local inputs.
- **Every copy into the project gets a row** (file, source, source mtime, copied on, md5), in the same edit:
  `python3 <skill>/scripts/provenance.py copy <source> data/<unit>/<file>`. Run `provenance.py check` before a
  result is reported: it flags a copy or a source that changed since the row was written.
- **A dataset is identified by its bytes**, never by its metadata name. A deduplication keyed on run and region names
  deleted 13 real samples; file size plus checksum found 55 folders sharing two tables. Model outputs never re-enter
  as inputs.
- **Tag every data source with a license tier** and carry the tier into checkpoint names and result tables. License
  gates release, not inclusion: in-house data may train and benchmark an internal model that never leaves the
  machine. Release decisions belong to `research-release`.

Full ignore-file reasoning, the archive-and-symlink move for large data, and the disk rules are in `references/data.md`.

## 3. One source of truth for settings

- **One configuration object with named presets holds every setting.** A dataclass in `src/<pkg>/settings.py`, one
  field per setting with a comment; presets `quick` (a laptop smoke run of about 10 minutes, written to
  `scratch/quick/`) and `full`, plus one per hardware profile. Overrides go by keyword, and an unknown key raises.
- **Scripts and notebooks read the same object.** A notebook's parameters cell is one call to `preset()`; a script
  takes `--profile` and calls the same function. In the source project a full-run script executed the notebook's
  parameters cell itself, "exactly the Parameters cell of the notebook". Never copy values into a script.
- **A variant is a parameter.** A script that switched variants by editing a constant in its source could not
  reproduce both. Paths come from the file's own location, never from the working directory.
- **Every path is set once**, in `configs/paths.env`, and every script sources it. The author's benchmark rebuild
  called its paths file the "single source of truth" for every remote path.
- **Every identifier and threshold is defined once in code** and imported. A human-readable map (`METHODS.md`, a
  methods table in the paper) is a view generated from it. "Never hardcode an ID or threshold in a runner: import it."
- **A name that appears in many places lives in one constant**, so a change is one search and replace (a model hub
  id, a release tag).
- **The code name stays stable.** An aspirational or paper-facing name lives in docs until the end; a conceptually
  new model gets a new name, never a version number ("it's another thing").

## 4. The results-folder contract

The default for any project that produces results. Every script and notebook writes through one store
(`src/<pkg>/store.py`, a copy of `scripts/results_store.py`), development scripts included.

```text
results/runs/<profile>/   config.json (first)  manifest.json (last)  catalog.parquet
                          tables/  views/<view>/ (+ _meta.json)  models/  analysis/ (+ _keys.json)
                          figures/<figN_topic>/panels/  side/<name>/ (+ SUMMARY.md)  logs/ (run.log, failures.csv)
results/cache/  results/aggregate/  results/archived/<YYYY-MM-DD>_<reason>/
```

- **One results root per run profile; two profiles never share one.** The source project wrote `results/` for the
  quick profile and `results_<hardware>/` for each full run. The whole `results/` tree is ignored by git. Never
  sibling folders such as `results_20260314_074730`, `results_final`, `results_final2`.
- **Config at the start, manifest at the end.** `config.json` is written before any data is touched. `manifest.json`
  holds config and hash, packages, platform, device, git commit with a dirty flag and diff hash, item ids, view
  metadata and failure count. **A root without a manifest is unfinished**: it is not cited.
- **One catalog row per data instance, with ids that encode lineage**: `<source>/<name>`, `<generator>/<task>/s<seed>`,
  derived `<parent>~<kind>@<level>#<seed>`. Seeds come from a hash of named parts, with disjoint ranges per purpose.
- **Per-view outputs are append-only parts with a `_meta.json`** that says how the view was made (model, checkpoint,
  layer, pooling, input). In a benchmark study, one view per model; the catalog rows are the datasets.
- **Every stage is resumable**: it asks the store what is done and skips it. "After a disconnect, Run all again:
  finished work is skipped." **A failure is a row** in `logs/failures.csv` (time, stage, id, error) and the run goes on.
  Workers of unequal speed share a view by `claim()`; `tests/test_store.py` proves resume and lineage.
- **New data enters through the contract**: an adder script writes catalog rows under a new `source`, and one
  generic top-up step fills every view's gaps. Added items are projected onto fitted spaces and never refit them.
- **Analysis tables are cached under a key** of their inputs and settings, and recomputed only when it changes.
- **Archive before overwrite, by default.** A figure folder, table or side analysis that exists moves to
  `results/archived/<YYYY-MM-DD>_<reason>/` with a `MANIFEST.tsv` row before the new one is written
  (`store.fresh(rel, reason)`, or `archive.py` from the shell).
- **Ad hoc analyses go to `side/<name>/`** with a `SUMMARY.md` headed by script, date and commit; never a sibling of
  the run roots.
- **No result without a commit behind it.** Commit development scripts the same day; a manifest with `dirty: true`
  is not cited until the code is committed. **A built distributable is rebuilt by a script from a clean tree**, or not
  tracked.
- **Smoke runs write to `scratch/`**, never beside `results/runs/`. Nothing in `scratch/` is cited.
- **`RUN_MAP.md` has one row per run root** (profile, or unit and variant), updated in the same edit as the run.
  Status: `planned`, `submitted`, `done`, `validated`, `aggregated`, or `failed`, `oom`, `archived`. An archived run
  keeps its row and its reason.

```bash
python3 src/<pkg>/store.py init results --profile full      # the tree, without running anything
python3 src/<pkg>/store.py check results/runs/full          # manifest, no stray entries, _meta per view
python3 <skill>/scripts/archive.py <old> --to results/archived/<YYYY-MM-DD>_<reason> --reason "<why>" --apply
```

When each (unit, variant) pair is its own scheduler job, keep `results/runs/<unit>/<variant>/` and put the same
contract inside each folder; `run_manifest.py` writes a manifest for runs that do not use the store. The tree entry by
entry, the store API, what drifted and why: `references/results-contract.md`. Naming and storage on a remote:
`references/runs.md`.

## 5. The documents, each stated exactly

A project's standing text has four layers, and every file owns one question. The four governing documents say
what the project is for and what binds it. They are short, and only the lead of the project changes them.

| File | What it is | Owns the question | A sentence belongs here when |
|---|---|---|---|
| `NARRATIVE.md` | the argument | why this project, why this way, what a win looks like | removing it breaks the chain from the problem to the claim |
| `GOALS.md` | the targets | where to, what next and what counts as done, what is out | it names an outcome that can be checked |
| `GUARDRAILS.md` | the invariants | what must never happen | breaking it voids a result or harms someone else's data, and nothing would look wrong |
| `GUIDELINES.md` | the conventions | how work is normally done, and what "done" means | a competent person may override it with a stated reason |

- **A long goal** is the outcome the project exists to reach, stated so that an outsider can test it: the thing
  delivered, its properties, the baseline it beats. One to three per project.
- **The short goal** is the next result that decides what happens after it: a due date, three to five
  deliverables that each carry their check, the controls, what waits until it holds, and the decision it feeds.
  One is active at a time. Steps toward it are next actions in `STATUS.md`.
- **A non-goal** is adjacent work the project refuses, with the place where that work lives.
- **A guardrail has a stable id, the failure it prevents and its check.** The source file opened: "Hard
  constraints. Each one prevents a specific silent failure that makes the result worthless or the run
  impossible." The file ends with an enforcement table (rule, enforced by, mechanism, gap). A setting with a safe
  range lives in `DESIGN.md`.
- **Guidelines open with the bar and close with the definition of done.** The source file: "These are
  conventions; the non-negotiables are in `GUARDRAILS.md`."
- **A goal or a rule is never edited away.** It is marked `SUPERSEDED` or `RETIRED` with the date and who decided.
- **A governing document changes in the same commit as the decision behind it.** In the source project the
  headline goal changed in the index, and the narrative kept the old one.
- **The knowledge base (`docs/kb/`) holds what the project knows about its field, data and methods, and how it
  knows it.** One topic per entry, `INDEX.md` read first, every claim tagged `[RUN]`, `[DOC]` or `[U]`, superseded
  entries archived with a banner. An entry is evidence; a decision is a `DECISIONS.md` row that cites it.
- **When documents disagree:** a file that a script can check beats a sentence about it; `GUARDRAILS.md` beats
  every other document; between two dated statements of the lead the newer wins; otherwise the owner of the
  question wins.

```bash
python3 <skill>/scripts/doctor.py <project>            # what is missing, unfilled, stale or unreachable
python3 <skill>/scripts/doctor.py <project> --strict   # before handing over: warnings fail too
```

Exact definitions, the shape of each file, the table that sorts a sentence into its file, who changes what and
when: `references/governing-documents.md`. Layout, entry format and upkeep of the knowledge base:
`references/knowledge-base.md`. Read both before writing or repairing any of these files. A project that already
has an index carrying everything is sorted, sentence by sentence, with section 13 of the first file; the author's
wording is moved and never rewritten.

The map, the knowledge files, the ledgers and the state:

| File | Owns the question | Rule |
|---|---|---|
| index file (`CLAUDE.md`) | where is everything, and in what order to read | 200 to 500 words: purpose, reading order, contract tree, pointers, the guardrails by id in one line each, done checklist |
| `SPEC.md` | what did the author ask for | the author's inputs verbatim as labeled parts; which part is the goal; frozen |
| `DESIGN.md` | what is the science as built | object of study; one table per choice with why it exists; test per question |
| `NOTES.md` | what was verified, and what deviates | fixed headings: environment, verified APIs, gotchas, deviations from papers, key decisions, measured runtimes |
| `README.md` | what is it, how do I run it, which file owns which question | install, the 60-second version, layout tree, the ownership table, pointer to status |
| `STATUS.md` | what works, what is blocked, what is next | dated; each component marked R exact reproduction, A approximate reproduction or E new extension, with `file.function`; `[AUTHOR ACTION]` on blockers |
| `experiments/EXPERIMENTS.md` | what was tried and what happened | one entry per attempt, newest first, failures kept, absolute dates |
| `DECISIONS.md` | why is it this way | one row per choice; superseded rows stay with `SUPERSEDED-BY #n` |
| `RUN_MAP.md` | which run produced what | one row per run with config, output, status, `Synced` |
| `PROVENANCE.md` | where did this file come from | one row per link, copy and borrowed piece of code |

- **The index file is an index.** Rule text goes in `GUARDRAILS.md` and `GUIDELINES.md` (topic files in
  `guidelines/<topic>.md`), goals in `GOALS.md`, reference in `docs/`.
  A long first version was rejected as "too reductionistic"; the counter-examples ran to 3,000 words with stale
  status checklists. The scaffold checks the 500-word limit.
- **Every question has one owning file**, the README table names it, and every document is reachable from the
  README or the index. A document that nothing points to is lost; `doctor.py` lists them.
- **A fresh session resumes from `NOTES.md` and `STATUS.md`.** The author's instruction when context runs short:
  "update NOTES.md, commit, and tell me to /clear and say 'continue from NOTES.md'."
- **Verify a spec before building on it.** Facts in a chat-generated spec were wrong more than once; research notes
  tag each claim `[RUN]`, `[DOC]` or `[U]`, and a note cites only files inside the repository (verification scripts
  left in a temporary scratchpad were lost).
- **Ledgers change in the same edit as the thing they track.** A run updates `RUN_MAP.md`; a copy updates
  `PROVENANCE.md`.
- **Failures are entries.** Outcome labels: `done`, `failed`, `inconclusive` (say what was missing), `negative`
  (answered no), `dead` (the measurement was degenerate). A changed verdict is appended, never overwritten.
- **A design record carries its status.** `LOCKED` or `SUPERSEDED-BY`, with a date; grep for later records before
  building. One session implemented a design that had been superseded the same day and had to revert.
- **No number is typed into prose by hand.** Generate it into a marked block and let a preflight fail when the block
  is stale, or tag it `[VERIFY]`. `paper-code-parity` and `stats-reporting` cover numbers that reach a paper.

Templates for these files and the reasoning behind them: `references/documents.md`.

## 6. Deferred doc sync

The author does not want shared docs edited after every change: "every now and then when I'm done with big changes
I'd like to say update docs and all stuff that need update to be updated."

- **Per-item work never edits shared guidelines.** Each ledger row carries `Synced`, `-` until folded in.
- **On the trigger phrase** ("update docs", "sync docs", "fold X back"): list every row with `Synced` at `-`, fold
  each lesson into the guideline file that owns it, refresh `STATUS.md` and the index pointers, flip the rows to
  `yes`, and commit it as one named change.
- **An explicit request wins.** "Add that to the skill" or "doc it in our md files" is done now.

The sweep step by step: `references/documents.md`, section "The update-docs sweep".

## 7. The laptop writes, the remote computes

- **Code and prose are written on the laptop**; the remote runs jobs. Local checks are compile and import only when
  the project never runs locally.
- **Push code up with `scripts/sync.sh up`** (`rsync -rtvu`): `-u` never overwrites a newer file on the remote,
  `--delete` is never passed, and `.git`, data, results, scratch and caches stay behind. Pull results down with
  `scripts/sync.sh down` into the results tree; it refuses to write into a git checkout. `-n` previews.
- **`.git` never travels.** When `origin` vanishes, re-add it from the URL kept in `.git/FETCH_HEAD`, and run
  `git remote -v` before any push.
- **One writer per file.** When two sessions (laptop and remote) work on one deliverable, one writes and the other
  supplies facts and audits. Before reassuring anyone that a file is safe, compare with `cmp`.
- **On the remote, code and inputs may sit on scratch; results go to a persistent area.** Measure free disk before a
  large write; never go below 15 % free.

Scheduler commands and job scripts belong to `cluster-jobs`. Drop-folder hand-offs and allowed transfer verbs are
in `references/remote.md`.

## 8. Triage of a cluttered root

When the root is already a mess, sort it before moving anything:

```bash
python3 <skill>/scripts/triage.py <root> --out docs/FOLDER_TRIAGE.md      # lists, suggests, moves nothing
```

1. The table suggests a class per entry: `KEEP?` (named in the project's code, tracked, or the newest of a family),
   `ARCHIVE?` (older dated or numbered siblings), `DELETE?` (smoke, tmp, check, empty, build debris, virtual
   environments), `VERIFY-FIRST` (lone archives, single files of 1 GB or more), `UNSORTED`. Find the live chain by
   reading the scripts that build the deliverable; the table marks entries named in code as `KEEP?`.
2. **The owner fills the Decision column.** Folder dates are a hint only: the misnamed "final" folder was old.
3. Move archive decisions with `archive.py ... --apply`; for big data on a full disk add `--symlink` so existing
   references keep working.
4. **Delete only what is verified as a duplicate** (match by size, then by checksum), and ask before deleting
   anything large. Unpublished data is never deleted in a tidy-up.
5. Write the new rule into the index file so the sprawl does not return: "One row per (unit, variant) in
   RUN_MAP.md; superseded outputs move to results/archived/<date>/ with a reason."

The full procedure, the classes and their evidence: `references/triage.md`.

## 9. Check before handing over

Scripted first:

1. `scaffold.py` exits 0: index file at most 500 words, ignore file covers `data/`, `results/`, `scratch/`,
   results contract files in place.
2. `git status --short` and `git check-ignore -v <a data file> <a result file>`: no data, outputs or binaries
   staged; `reference/` files tracked.
3. `provenance.py check` exits 0.
4. `store.py check results/runs/<profile>` exits 0 for every root cited in `STATUS.md` or a paper, and each has a
   `RUN_MAP.md` row. A manifest with `dirty: true` is reported as such.
5. `sync.sh up -n` lists only code and docs.
6. `doctor.py <project> --strict` exits 0: the four governing documents are filled, the short goal has a date
   that has not passed, every guardrail has its id, what it prevents and its check, every knowledge base entry
   is in the index, and no document is unreachable.

Then by eye:

7. Read the index file as a newcomer: every pointer resolves, no stale status, no goal and no rule text in it.
8. Read `GOALS.md` aloud to the user: the long goal, the short goal with its date, the non-goals. A project whose
   lead does not recognize them is not set up.
9. `ls` the root: nothing beyond the tree, the governing documents and the root ledgers.

Say what was not checked: links that point to stores on another machine, remote paths that were never reached, and
placeholders still in `[brackets]`.

## 10. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a long index file with every rule inline | "too reductionistic" | a 200 to 500 word index pointing to guidelines and ledgers |
| 36+ timestamped result folders at the root | "do not recreate the upstream sprawl" | one lineage plus `archived/<date>/` with a reason |
| everything tracked in the campaign repo | "src/ + ops/ + docs/ and nothing else" | a small tracked set; the rest untracked, still on disk |
| ignore lines with no reason | "Do not 'fix' it by re-adding a path" | a reason above every block |
| counts copied into prose | "hand-copied counts drifted twice in two days" | generated blocks, a failing preflight, `[VERIFY]` |
| editing docs after every change | "every now and then ... I'd like to say update docs" | a `Synced` column and one sweep on the trigger phrase |
| deleting unused material | "archive in the same folder the unused stuff" | `archived/` or `_attic/`, never deleted |
| rsync both ways with `.git` | the `origin` remote vanished twice | `rsync -rtvu`, no `--delete`, `.git` excluded |
| two sessions writing one file | "you are the writer" | one writer; the other side sends facts |
| a model renamed with a version number | "it's another thing" | a new name; aspirational names in docs only |
| galleries regenerated in place, versions only in log names | "bring back all previous figures in the gallery we need them!!!" | archive before overwrite (`store.fresh`, `archive.py`) |
| a results root that ended without a manifest, with sibling folders from development scripts | (found on inspection) | `side/<name>/`, a manifest per root, `store.py check` |
| development scripts left uncommitted, a distributable committed once and left stale | (found on inspection) | commit the same day; dirty flag and diff hash; `dist/` rebuilt, ignored |
| settings copied between notebook and scripts, variants made by editing source | "exactly the Parameters cell of the notebook" | one config object with presets; a variant is a parameter |
| goals stated in the index and in the narrative, one updated and one left stale | "needs the same update" | `GOALS.md` owns the goals; a change updates the narrative in the same commit |
| an index of about 3,000 words carrying goals, decisions, corrections and pointers | (found on inspection) | each kind of sentence has its file (section 5) |
| a rule learned in an incident that lived only in the chat | "add that to docs and gaurdrails too" | the guardrail is written in the same session, with the incident |
| stale knowledge base documents beside live ones | "Nothing below is stale." | archive with a banner; `INDEX.md` lists every live entry |

## Reference files

- `references/layout.md`: the tree path by path, layout variants (driver, hosted notebook with its full-run
  procedure, figure, upstream results), the contract file between repositories, environment files, names.
- `references/data.md`: the ignore file block by block, links and provenance, byte identity, tiers, archive and
  symlink, disk.
- `references/results-contract.md`: the results tree entry by entry, config and presets, catalog and lineage ids,
  views, resume and failures, what drifted and the rule it left, the store API.
- `references/runs.md`: run naming, the run map, manifests, scratch and persistent storage.
- `references/governing-documents.md`: `NARRATIVE.md`, `GOALS.md`, `GUARDRAILS.md` and `GUIDELINES.md` defined
  exactly, the table that sorts a sentence into its file, which document wins, who changes what, how an agent
  uses the set, the same set for a figure or a chapter.
- `references/knowledge-base.md`: what belongs in `docs/kb/`, layout, entry format, index, building one from a
  pile of sources, keeping it true.
- `references/documents.md`: the map, knowledge files and ledgers with their templates and reasons (index, SPEC,
  DESIGN, NOTES, STATUS, experiments, decisions), the update-docs sweep.
- `references/remote.md`: laptop and remote, sync directions and excludes, one writer, drop folders.
- `references/triage.md`: sorting a cluttered root, step by step, with the classes and what each needs before acting.

Scripts (Python 3.9 or later, standard library only, except that the catalog, views and cached tables of
`results_store.py` and `test_store.py` need pandas and pyarrow; `sync.sh` needs bash and rsync, `build_dist.sh`
bash, git and unzip):

| Script | Does |
|---|---|
| `scripts/scaffold.py` | creates the tree and writes the templates from `assets/templates/`, the four governing documents and the knowledge base included; links raw stores; copies the store and settings into the package |
| `scripts/doctor.py` | checks the governing documents, the index, the ownership table and the knowledge base of any project; reads only; `--self-test` |
| `scripts/results_store.py` | the results store (`Store`, `section`, shards and claims), and `init` and `check` from the shell |
| `scripts/test_store.py` | round-trip test of the store: resume, lineage rebuild, missing manifest, shards and claims |
| `scripts/build_notebook.py` | writes a notebook from a `CELLS` list, with host metadata and `--replace` for a full-run copy |
| `scripts/build_dist.sh` | zips a shippable folder from a clean tree and checks it against `git ls-files` |
| `scripts/install_missing.py` | installs only what a hosted runtime lacks, its core packages held by a constraints file |
| `scripts/provenance.py` | `copy` an input with its row; `check` every recorded copy for drift |
| `scripts/run_manifest.py` | writes `manifest.json` for a run, from the shell or from Python |
| `scripts/archive.py` | moves superseded outputs or large data with `MANIFEST.tsv`; dry run unless `--apply` |
| `scripts/triage.py` | lists a cluttered root as a triage table; moves nothing |
| `scripts/sync.sh` | `up` code to the remote, `down` results; never deletes, never carries `.git` |
