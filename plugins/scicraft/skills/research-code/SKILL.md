---
name: research-code
description: Writes and changes research software with an agent (features, refactors, ports, regression hunts, tests, commits, pull requests, command docs) so the owner's scripts keep working and reviewers can read the diff. Use it whenever code in a research repository is added, changed, debugged, tested, committed or documented, even unnamed: "add a flag for X", "port this from the old branch", "it used to work, what changed", "results got worse since last week", "write tests", "make a PR", "split this into PRs", "strip the AI trailer", "push this so my colleague can run it", "document the CLI". Holds what agents get wrong: renamed flags, new dependencies, filtered raw output, defaults that change results, fixes before diagnosis, tests that cannot fail, positional joins, oversized or mixed PRs, attribution in shared history. Prefer project-structure for repository layout, research-release for a public release, cluster-jobs for heavy runs, ml-evaluation for metric design.
---

# research-code

How to write and change research software with an agent so that the owner's months of scripts still run, the
numbers stay comparable, and a reviewer can read every pull request in one sitting. Distilled from a year of one
researcher's work: a graph-neural-network package taken from a research fork to a stack of upstream pull requests,
a foundation-model training codebase, benchmark harnesses and the regression hunts between them. Almost every rule
below exists because its absence broke a run, hid data or cost a review.

> **PRIME DIRECTIVE: change only what was asked, in a way that leaves every existing call, flag, default and output
> row exactly as it was, and prove it with a diff before handing over.**

Three failures cost the most time. Guard against them from the first minute:

1. **Changing more than asked.** A "minimal" prefilter change that also renamed flags and added detection logic
   flooded the owner's runs with warnings; a flag moved between commands made a cluster command fail with
   `Unknown option`. Inventory the interface first and diff it after (sections 1 and 2).
2. **Patching before diagnosing.** When results get worse, the cause sits in one stage between a last-good
   version and now. A fix written before that stage is found adds a second change to the hunt. Inspect, rank
   hypotheses, wait for a go (section 4).
3. **Silent data loss.** Filters that delete rows from the raw output, joins by position after a filter, and
   defaults that drop a few percent without a message all produced plausible numbers and no error. Annotate,
   count and assert (sections 2, 3 and 5).

## 0. Before starting

Collect by reading the repository. Ask only for what cannot be found, in one message:

- **The reference version.** Which branch is the package of record (usually upstream `main`), which worktree or
  repository holds only scripts, and whether the work goes to a branch of the owner's own repository, a lab's
  shared repository or an upstream project. The destination decides tests, size budget and attribution
  (section 7).
- **The callers.** The owner's run scripts, notebooks and job files that call the code. They define the
  interface that must not move.
- **Earlier implementations.** Old branches, forks, sibling worktrees, the owner's other repositories and
  `__pycache__` folders. The owner has often solved the problem before (section 1).
- **Where code may run.** On a laptop without the accelerator or the data, "test" means write the tests and run
  only small CPU checks; anything heavy becomes a command for the cluster (`cluster-jobs`). Running the package
  locally once crashed the machine.
- **What is in scope.** The one change asked for. Everything else you notice goes in the report as a finding.

## 1. Read before you write

- **List the public interface before editing**: command-line flags with defaults, public functions with
  signatures, output files with their columns. Save `--help` output of the reference install. The owner drives
  everything from scripts, so a renamed flag breaks months of runs.
- **Search for the owner's earlier implementation first.** "I told you just pick the best technologies I already
  developed in other branches, you picked sth that is super slow." Search old branches, forks and scripts, report
  what you found, and compare it with any new idea on speed and stability. The older, proven version wins unless
  a measurement says otherwise.
- **Recover curated work; never reinvent it.** A curated set of 8 validation metrics was replaced by an invented
  set of 3 and had to be recovered from one commit and compiled bytecode. Before writing a module from scratch,
  search `git log --all -S`, sibling worktrees and `__pycache__` (`references/change-discipline.md` has the
  recovery commands).
- **Read the consumer's spec before naming outputs.** Match the column names, id conventions and file layout of
  the tool that reads the output, and look at how the other methods in that ecosystem produce theirs.
- **Choose a method after timing it.** Time candidates on a realistic slice, report wall time, then pick. Prefer
  methods the field already trusts over a random repository. A startup that takes 30 minutes is a regression.
- **Trust the code and the config, never the prose.** One knob had four values in the documents and one in the
  code. Read the default from the reference branch's source before stating it.

## 2. Change discipline

The rules that keep a change reviewable and the owner's results comparable. Detail and code patterns are in
`references/change-discipline.md`. A typical case: adding a confidence threshold to the prediction step of an
evaluation harness. The flag defaults to "off", the predictions table keeps every row with a `keep` column and
the threshold value, the scoring step reads `keep`, and the old scripts produce byte-identical output.

| Rule | Reason |
|---|---|
| **Keep the interface; change internals only.** If a flag must move, keep an alias or ask first. | Scripts call the old names; a moved flag failed with `Unknown option` on the cluster. |
| **A rename asked for is done everywhere at once**: code, long and short flags, scripts, tests, docs; then grep the old name and expect zero hits. Touch only the folder named. | "rename everything properly in the code also in the docs"; "I want no changes in flags/usage ok?" |
| **Change files with the file tools; the shell runs programs and git.** Batch related edits and commit once. | Two heredoc writes failed on a wrong working directory, and a 16-file scripted rewrite left no reviewable diff: "why shell man?" |
| **A script that writes results runs only under its `main()` guard**, takes the output path as an argument and never defaults to a banked file. | Importing a bare script for one helper regenerated and overwrote a banked results file. |
| **Add no new dependency.** Reuse what the package already imports; a library that is truly needed becomes an optional extra. | "work with what [the package] already have, even if it means changing the strategy." |
| **Minimal-diff porting.** When moving code from one place to another, the diff is confined to imports, data path and save path: no renames, no helpers, no type hints, no clean-up. | A port that also restyles cannot be checked against its source. If the output differs, the diff was too large: revert and re-minimize. |
| **Do not reformat untouched lines.** | Style churn hides the change and makes review hard. |
| **New options default to the old behavior.** A default that changes results is stated in the PR message and filed as a separate fix. | "make the defaults in a way that we don't have any behavioural difference from the main branch." |
| **Never filter raw output in place.** Keep every row, add a boolean `keep` column and record the threshold used; apply the filter where it takes effect, at export. | Dropped rows cannot be recovered or audited, and a threshold change then needs a rerun. |
| **Report every filter with its count.** Log rows in and rows out at each filter. | About 7 million rows were left out by filters before anyone noticed; a minimum-count default of 10 dropped cells nobody asked to drop. |
| **Fail loudly when a hard requirement is missing.** No silent fallback to a slower or different path; never fix a crash by loosening the check. | A quiet fallback runs a different program; `strict=False` would have loaded the wrong readout and corrupted a metric. |
| **Unknown config keys and disabled features fail at step 0.** Echo the resolved config into the run log. | A misspelled key silently reverted to its default; a run trained with a grounded feature switched off. |
| **Keep analysis code out of the package.** | Paper-specific scripts in the package confuse users and reviewers. |
| **Progress bars, never banner prints.** Use the logging and progress style the package already has. | "never! ever! add prints like '\nHPO complete! ...'" |

A new mechanism is a switch whose default is the current behavior, and the default path is bit-identical to the
old one: write an equivalence test (section 5). A default chosen after looking at results is declared as a
post-hoc choice wherever the result is reported.

## 3. Rows, keys and counts

The costliest bug class in the source work: wrong joins that raise no error. The same bug appears wherever
predictions are joined back to labels after invalid rows were dropped, in a tabular benchmark as much as in a
point table of a billion measurements.

- **Assign the row index on the raw table, before any filter**, carry it through every write, and join on it.
  A streaming join that dropped the row key placed records a median of 125 µm from their true location with
  0.2% agreement. A scorer that indexed after filtering, while the producer indexed before, landed labels on the
  right row 0.065% of the time and raised nothing.
- **Never join by position.** Refuse a positional fallback unless a flag allows it.
- **Assert exact invariants, never ratio bounds.** The count of output rows that point at discarded input rows
  must be 0. A guard of 0.9x passed a 0.25% offset.
- **Check that each row has exactly one id after any secondary assignment** (a recovery pass, a merge, a dedup).
- **Mind the key's type.** A `UInt32` row index caps near 4.29 billion rows.
- **Every method in a comparison sees the same filters and the same decision stage** (thresholded against
  thresholded). Record the filter settings next to each results table.

## 4. Regression hunt

When results get worse or a run "used to work" (a benchmark score below last week's, a training curve that no
longer matches the old run, fewer detected objects than before), follow the procedure in
`references/regression-hunt.md`:

1. **Inspect only until told to fix.** "don't change anything, just inspect why." Explain before you patch.
2. **Get the last-good version**: date, commit or branch, and the run it produced. If the owner does not know,
   find the commit that matches the date of the good results.
3. **Find the first stage whose output differs.** Compare artifacts in pipeline order (raw output before
   aggregation, aggregation before plots). "the problem shows up already at the initial predicted assignments."
4. **Diff only the code of that stage** between last-good and now: `git log <last-good>..HEAD -- <paths>`, then
   `git diff`. Check the environment and package versions after the code.
5. **Rule out stale results.** A comparison table may mix results computed with old code or different
   pre-filtering. One revert was itself reverted when the "regression" turned out to be external methods
   scored with the old metric version.
6. **Treat a coincidence as a bug until a one-line check clears it**: identical numbers across splits, a count
   off by an order of magnitude, a method suspiciously similar to the baseline, 8 GPUs requested that move like 1.
   Each of these was a real bug.
7. **When the user sees a contradiction in a picture, check the labels against geometry and counts first.**
   An agent defended an export whose labels were swapped.
8. **Report** with `assets/regression_report.md`: symptom, first differing output, commits in range, hypotheses
   ranked with the check that settles each. Then wait for a go, fix only the divergent stage, keep later
   intentional fixes, and confirm against the old numbers.

## 5. Tests for research code

Detail, patterns and the stub runner for GPU-only packages are in `references/testing.md`; a runnable template
is `assets/test_research_code.py` (numpy and pytest).

- **Shapes and dtypes** for every public function, including the empty input and the one-row input.
- **Determinism.** Same seed gives identical output; a different seed changes the draw. A seeded run once gave
  different scores because an unordered group-by fed the seeded permutation, and one package had no seeding at
  all, so a "replicates" claim was retracted.
- **Tiny golden values**: a 3-row input whose output is computed by hand or by the trusted version, committed as
  literals. For refactors and releases, golden files with a tolerance measured by running the code twice, never
  guessed.
- **Joins with filtered rows interleaved.** Without low-quality and control rows between good ones, raw and
  filtered indices coincide and the bug of section 3 is invisible to every test.
- **Planted structure.** Synthetic inputs with a known answer (three separated clusters give three groups; a
  known foreign fraction gives that fraction).
- **Degenerate inputs and failure paths**: collinear points, float ids, empty groups; the output schema is the
  same on the failure path as on the success path.
- **Skewed inputs as well as uniform ones.** A masking step budgeted per unit inverted on inputs where a few units
  held most of the points; uniform fixtures hid it. Keep one heavy-tailed fixture.
- **Default equivalence**: the new option at its default reproduces the old output exactly, checked against a
  frozen reference output.
- **The study's contract as tests before the first full run**: one test per promise the analysis makes. Tests
  that need a heavy optional package or downloaded weights skip with a reason (`pytest.importorskip`).
- **A test counts only if it bites.** Revert the fix or flip a sign and watch the test go red. Two tests in the
  source work were decoration until this check, and tidy-up fixes to minor findings twice caused worse bugs.
- **Test the shipped expression, never a copy of it**, and name each test as the claim it checks
  (`test_labels_land_on_their_own_rows_when_low_quality_rows_are_interleaved`).
- **By destination**: a full local suite for internal branches; no tests in a minimal upstream PR unless the
  maintainers ask, and local tests never count against the size budget. On a laptop without the accelerator,
  write the tests and run only the CPU ones.

## 6. Commands handed to the user

- **Real paths, never placeholders**, resolved from the owner's scripts and notes. "is this hardcoded or you
  give me an example?"
- **Every flag checked against `--help` of the exact install that will run**, on the exact branch.
- **No hard-coded resources.** Memory, GPUs and budgets are explicit overrides in the command; a script aborts
  when one is missing (`cluster-jobs` has the job side).
- **Copy-paste ready**: one block, no prose inside it.

## 7. Commits and attribution, by destination

Detail and recipes are in `references/git-and-prs.md`.

| Destination | Assistant trailers (`Co-Authored-By`, "Generated with") | Agent files (`CLAUDE.md`, `.claude/`) |
|---|---|---|
| Your own private repository | the owner's policy; the author stripped them | as the owner likes |
| A lab or team repository others read | none, unless its owners want them | local only, through `.git/info/exclude` |
| An upstream project's pull request | none, unless its maintainers want them | never in the diff |
| A public release | none; authored as the person releasing | never |

The repository owner's policy decides. Where others read the history, write no AI trailer unless they want one:
"people won't trust it if it has your sign all over it." When a tool adds a trailer by default, remove it for
those destinations. `.git/info/exclude` keeps agent files out without the committed `.gitignore` naming them.

- **The subject names the decision or finding, not the file**; the body says why, with the measured motivation.
  Lab-facing repositories use a plain imperative sentence ("Relax the pandas pin and drop the unused reader").
  Never "Update docs and code".
- **Commit only what was asked**: "push changes on src ... not docs or results".
- **An accumulated tree committed in one go says so**: the message opens "Committed from an accumulated working
  tree, not authored in this session. The descriptions below are read off the diff."
- **Check sizes before committing**: nothing over 100 MB (the hosting limit), and look at anything over 50 MB.
- **Never push, open a pull request or post an issue unless asked.** An issue posted upstream without being
  asked had to be deleted. A post to an upstream project is drafted as a file headed `DRAFT, not yet posted`.
- **A standing instruction counts as asking.** When the owner has said to push after each milestone ("push the
  latest changes", said about 30 times on one project), push the code changes (results or docs only when named)
  to the agreed branch once a figure or analysis settles, and give the commit hash in the report.
- **Push your own research repository at least once per working day and before any risky change**, code, ops
  and docs folders only: "you have not pushed anything to github today?????" Before pushing a repository that holds
  private material, run the pre-push audit in `references/git-and-prs.md`.

## 8. Branches and pull requests

- **Never touch the shared `main`** unless its owner says to push there (a one-day team sprint did; record the
  instruction in the repository notes). "do not push anything to main!!!!" Bring `main` into feature branches;
  never the other way without a review.
- **One change per branch.** "in general top 1 big change per branch!" Branch each from `main`; stack only when a
  real dependency exists, and then set the PR base to the parent.
- **Size limit: under 400 new code lines per branch**, docstrings, comments, help text, tests and docs excluded;
  under 500 changed lines for a minimal upstream PR, and less is better. A 1,000-line I/O fix was split per
  platform reader.
- **Fixes and features on separate branches.** A broken reader or a hard-coded constant is a fix; a new
  capability such as platform detection is a feature.
- **No branch behind `main`.** Rebase a branch only you use; merge `main` into a branch others have pulled.
- **Never rewrite shared history.** No force-push to a shared branch. Join unrelated roots with
  `git merge --allow-unrelated-histories -s ours`; keep stale branches in an `archived` branch (an octopus
  `-s ours` merge) plus `backup/*` tags before deleting them.
- **Run `scripts/branch_check.py` and `scripts/interface_diff.py` on every branch** before calling it ready.
- **The PR message** follows `assets/pr_message.md`: 3 to 5 short paragraphs, what it adds with commands in
  backticks, the output files and their columns, defaults and opt-in flags, what is left out, "No new
  dependencies." No headings, no fluff, no dashes as punctuation, every identifier in backticks. Write one file
  per branch outside the repository; the commit message equals the PR body.
- **For a decomposition**, deliver a branch tree with merge order and a one-line defense per PR, an
  `integration/all` branch that merges everything so the owner can run it, and paper-only experiments on a
  `paper/` branch outside integration (`references/git-and-prs.md` has the procedure).
- **A fix to geometry or to an algorithm carries its check in the PR, with a number**: adversarial toy inputs (a
  concave shape, a thin arc, an empty case) and the common case, which must be unchanged.
- **Code handed to a colleague is the smallest slice that reproduces their result**: one entry function whose
  default selects everything, one plotting module, a three-point README, in the receiving repository's layout
  ("very very minimal LOC ... no fluff"). `references/git-and-prs.md` section 8 has the procedure.

## 9. Documentation

`references/documentation.md` has the detail; `assets/command_doc.md` is the per-command template.

- **One file per command**, most important first: idea, minimal input, steps, output with columns, parameters
  with the effect of raising and lowering each, measured time and memory, common errors.
- **Guidance from benchmarks, never results.** "don't explicitly mention any result (other than expected
  time/vram) from benchmarks. only deduce guidelines from it."
- **The README gets the minimal runnable input** and a pointer to the docs folder, in the repository's existing
  style, a few lines.
- **Docstrings are terse** and give the rationale; a shape comment (`# (B, N, D)`) on tensor lines.
- **A paper-to-code map plus a test beats prose.** Each equation or claim of the paper names the function that
  computes it and the test that checks it.
- **Defer doc sweeps** to a trigger ("update docs"), except docs that describe a decision, which go in the same
  commit as the decision.
- **The project's governing documents** (`NARRATIVE.md`, `GOALS.md`, `GUARDRAILS.md`, `GUIDELINES.md`, the
  knowledge base) are defined in the sibling skill, `project-structure/references/governing-documents.md`. The
  documents written under this section are about code: command docs, README, docstrings, the paper-to-code map.
- **Run the `humanizer` skill** on README and PR prose where it is installed. "you added so much ai fluff."

## 10. Check before handing over

In this order:

1. `python3 scripts/interface_diff.py --repo . --old <reference> --paths <package>`: zero FAIL lines, or each one
   asked for by the user.
2. `python3 scripts/branch_check.py --repo . --base <main> --destination shared|private`: zero FAIL lines.
3. The tests that can run here pass, and each new test was seen red once.
4. Read the whole diff yourself: only the asked change, no reformatting, no new import outside the package's
   dependencies, every new option defaulting to the old behavior, every filter logging its count.
5. Every command handed over was checked against `--help` of the install that will run it.
6. Say what was not run (GPU paths, the full pipeline, the cluster job) and why.

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a refactor that renamed flags | "keep the cli flags and api the same? only internally change things" | internals changed, interface diffed |
| a new library for one feature | "why do we even need opencv bro? ... don't add new stuff" | what the package already imports |
| a fresh design over an existing one | "pick the best technologies I already developed in other branches" | the owner's earlier version, compared |
| changes beyond the request | "I told you literally not to change anything other than that prefiltering!!" | one change, one diff |
| rows deleted from the raw output | "add a column ... keep true and false ... but don't filter anything out" | a `keep` column, filtered at export |
| a patch before a diagnosis | "don't change anything, just inspect why" | ranked hypotheses, then a go |
| an explanation of a too-good match | "it looks suspiciously similar numbers..." | a one-line check first |
| placeholder paths in commands | "is this hardcoded or you give me an example?" | real paths, flags checked against `--help` |
| a 1,000-line branch | "the review will be hard otherwise!" | under 400 new code lines per branch |
| two big changes on one branch | "no 2 big changes on each" | one change per branch |
| AI trailers in shared history | "people won't trust it if it has your sign all over it" | the owner's policy per destination |
| an issue posted upstream | "please kill the issues posted" | nothing posted unless asked |
| a PR message with fluff | "proper git tone human", "don't forget ` `" | the PR message spec |
| banner prints | "add progress bar as [the package] already has" | the package's own progress style |
| an invented metric set | "don't do this to me... recover those" | the curated set, recovered from history |
| file edits through heredocs and rewrite scripts | "why shell man? why do you have to run things????" | edit and write calls the user can review |
| a long first README in a sprint repository | "make super on point 1-2-3 main points" | three points and one hero figure on top |

## Reference files

- `references/change-discipline.md`: read before any change to a package. Interface inventory, command-line
  design and renames, reuse and recovery commands, porting, defaults and the frozen reference output, the `keep`
  column, filter counts, loud failure, style, applying a reviewed fix list, file tools.
- `references/regression-hunt.md`: the hunt step by step, git commands, first-differing-artifact table,
  coincidence checks, stale results, the report.
- `references/testing.md`: what to test in research code, golden values and tolerances, tests that bite, stub
  runners for GPU-only packages, skipping heavy dependencies, the study contract as tests, tests by destination.
- `references/git-and-prs.md`: commit messages, attribution, branch names, history recipes, PR decomposition,
  the message spec with an example, drafts of upstream posts, pushing and the pre-push audit, handing a slice to a
  collaborator.
- `references/documentation.md`: per-command docs, README, the README of a sprint repository, docstrings and the
  paper-to-code map, doc sweeps, recording lessons.
- `scripts/branch_check.py`: base, behind count, new-code size, whitespace churn, trailers, agent files, big
  files, mixed fix and feature.
- `scripts/interface_diff.py`: public functions, signatures, defaults and command-line options between two refs
  or two saved `--help` outputs.
- `assets/test_research_code.py`, `assets/pr_message.md`, `assets/command_doc.md`, `assets/regression_report.md`:
  templates.
