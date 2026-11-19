# Commits, branches and pull requests

## Contents

1. Commit messages
2. Attribution by destination
3. Branch names and roles
4. History rules and recipes
5. Pull-request decomposition
6. The PR message, checks in the PR, drafts of upstream posts
7. Pushing, the pre-push audit and sizes
8. Handing a slice to a collaborator's repository

## 1. Commit messages

- **The subject names the decision or the finding, not the file.** `loss: use the variance regularizer, drop
  the contrastive term` (the form; the content is invented), or as a claim: "VRAM was set by the rarest batch in the group; cap it, and B fits".
  Never "Update docs, scripts, and metrics": that style was abandoned.
- **Lab-facing repositories**: a plain imperative sentence with no prefix ("Relax the pandas pin and drop the
  unused reader"). Upstream projects: follow their convention (`fix(io): ...`, `feat(cli): ...` where used).
- **The body explains why**, with the measured motivation, and records what is not recoverable from the diff.
- **Docs that describe a decision go in the same commit as the decision.**
- **Commit only the scope asked for**: "push changes on src and other code things (not docs or results)", then
  "just src actually please".
- **A preregistration is committed before the result** it governs, with the time stamped in the message from
  `date` in the same command. A mistyped time is corrected by a separate commit with "no content change".
- **An accumulated tree committed at once** gets one commit whose message opens: "Committed from an accumulated
  working tree, not authored in this session. The descriptions below are read off the diff." Then one paragraph
  per area and a `STATUS.` line with what is known to be broken.

## 2. Attribution by destination

The repository owner's policy decides. Where others read the history, no AI trailer unless they want one.

| Destination | Trailers and tool lines | Agent files |
|---|---|---|
| your own private repository | as the owner likes; the author stripped them from their own repositories | as the owner likes |
| a lab or team repository | none unless its owners want them | `.git/info/exclude` |
| an upstream pull request | none unless the maintainers want them | never in the diff |
| a public release | none; authored as the person releasing | never; a leak scan treats them as errors |

The reason, in the author's words: "this is a mix of your coding and mine, but people won't trust if it has all
over your sign." When the tool adds a trailer by default, remove it for the destinations above. Before pushing to
a shared destination:

```bash
git log origin/main..HEAD --format='%h %an <%ae>%n%B' | grep -inE 'co-authored-by|generated with|claude|anthropic'
git ls-files | xargs grep -il 'claude\|anthropic' 2>/dev/null       # tracked files that mention the tool
cat .git/info/exclude                                               # CLAUDE.md and .claude/ listed here
python3 scripts/branch_check.py --base origin/main --destination shared
```

Excluding agent files through `.git/info/exclude` keeps them local without the committed `.gitignore` naming
them. Rewording commits that are already on a shared branch rewrites shared history (section 4): strip trailers
before the first push.

In their own repositories the author asked for this at least three times across projects: "only src for now to be
pushed indeed and strip off claude in the pushes", and for an organization repository "keep claude stuff local,
and strip off claude from contribution". When the owner asks for a code-only remote ("no resutls/just code"),
push code and small configs only, and keep results, manuscript sources and large outputs out through
`.gitignore`.

Never post issues, open pull requests or comment upstream unless asked. "please kill the issues posted I don't
want any issue posting!!"

## 3. Branch names and roles

| Name | Role |
|---|---|
| `main` | the reference; not committed to directly on a shared repository unless its owner says so ("master? what is it 2012?") |
| `feat/<thing>` | one feature, branched from `main` |
| `bugfix/<thing>` | one fix, branched from `main` |
| `paper/<experiment>` | paper-only experiments and ablation flags; not size-bounded, kept current with `main`, outside integration |
| `integration/all` | merges every open branch so the owner can run everything at once |
| `archived` | stale branches preserved by an octopus `-s ours` merge |
| `backup/<name>` tags | taken before deleting or rewriting anything |
| `<machine>/local-changes-<YYYYMMDD-HHMMSS>` | a snapshot of uncommitted local state before a big operation |

Names describe the role (`<feature>-alg` for the algorithm, `<feature>-writer` for its output step). One worktree per feature as a sibling folder is
convenient; say which worktree is the package of record and which holds scripts only, and verify paths with
`git ls-tree <branch>` before writing, because a monorepo subfolder and a standalone branch look alike.

## 4. History rules and recipes

- **Never rewrite shared history.** No force-push to a branch someone else has.
- **Bring `main` into feature branches**, never the reverse without review:

```bash
git fetch origin
git rev-parse origin/main                     # note it
git rebase origin/main feat/<thing>           # a branch only you use
git merge origin/main                         # a branch others have pulled
git rev-parse origin/main                     # unchanged
```

- **Join unrelated roots without a force-push** (a local repository whose history never shared a root with the
  remote):

```bash
git merge --allow-unrelated-histories -s ours origin/main   # keeps your tree byte for byte
git push origin main                                        # now a fast-forward
```

- **Preserve stale branches before deleting them**:

```bash
for b in <old-1> <old-2>; do git tag backup/$b $b; done
git checkout -b archived main
git merge -s ours <old-1> <old-2> <old-3>     # octopus merge; the tree stays main's, the history keeps all
git push origin archived --tags
git push origin --delete <old-1> <old-2>      # only after the owner agrees
```

  In the source work 27 stale branches went into one `archived` branch this way.
- **Check `git remote -v` before any push.** An rsync from a cluster copy overwrote `.git/config` and the `origin`
  remote vanished twice in one session; the URL survives in `.git/FETCH_HEAD`. Exclude `.git` from every rsync.
- **List curated assets before any merge** (a hand-picked metric set, a tuned config). A merge once lost a
  curated set of 8 metrics.
- **After a revert, diff the tree against the commit before the change**: a revert once failed to restore files
  that a move had swept into an attic folder (`git checkout <commit> -- <dir>` restored them).
- **Moving a file into an untracked attic stages the attic copy**; undo with `git restore --staged _attic/...` and
  commit only the deletion.

## 5. Pull-request decomposition

For a body of work that grew on a research fork and now goes upstream (the source case became about 20 branches,
including a 9-PR stack for one export feature):

1. **Inventory** every change across local repositories and branches, including uncommitted fixes and stashes.
2. **Drop** anything already on `main` ("make sure none of the features are redundant").
3. **Classify** each change as fix or feature:

   | Change | Kind |
   |---|---|
   | a broken or missing reader for a supported format | fix |
   | a hard-coded constant made configurable at the same default | fix |
   | a guard against empty input or a degenerate array | fix |
   | silent row loss in a step | fix |
   | automatic detection of the input format | feature |
   | a new command or export target | feature |
   | an optional new input field | feature, default off |

4. **One branch per change, from `main`**, under 400 new code lines (docstrings, comments, help text, tests and
   docs excluded). Over budget, split by unit (one reader per branch, one module per PR in a stack). One cohesive
   algorithm slightly over budget can stay whole when the PR says so.
5. **Do not stack unless a real dependency exists** ("do not depend stuff on each other (build on top) if not
   necessary"). A stack sets each PR's base to its parent, and its tip should be byte-identical to the monolithic
   branch it came from.
6. **No branch behind `main`.** "make sure no branch is behind main! that was our deal."
7. **Defaults off**: no behavior change on `main` from any PR unless the PR is the fix that changes it.
8. **Write one PR message per branch** in a folder outside the repository (`pr-descriptions/<branch>.md`); do not
   open the PR ("don't make a pr, but make the pr message so if I wanna make a pr it's there").
9. **Deliver a branch tree** with the merge order and one defensible sentence per PR:

```
main
├─ bugfix/<a>            independent
├─ bugfix/<b>            independent
├─ feat/<c>              independent, default off
└─ feat/<d>-core ── feat/<d>-cli      stack: set the base of -cli to -core
```

10. **Make `integration/all`** that merges every branch so the owner can run the whole thing; keep ablation code
    on `paper/` outside it; collect superseded branches into `archived`.
11. **Run the checks** on every branch: `scripts/branch_check.py` (base, behind, size, churn, trailers) and
    `scripts/interface_diff.py` (no public name or default moved).
12. **Strip attribution** for the destination, push branches only, never push `main`, never open issues.

For a minimal upstream feature PR: read the maintainer thread and implement only the agreed minimum; match the
consumer's naming spec and resolve id-column clashes the way the consumer does; shrink the diff in audit rounds
toward the target (under 500 changed lines); no tests; README a few lines; reply to review comments in plain text
with identifiers in backticks.

## 6. The PR message

Template: `assets/pr_message.md`. Rules, from a cycle of more than 20 corrections on one PR message:

- 3 to 5 short paragraphs. No headings, no tag on the left, no bullet lists of features, no dashes as punctuation.
- **What it adds**, with the command in backticks and how the CLI is used.
- **The outputs specified**: file names, columns and their types, keys the consumer needs, coordinate space.
  "spec the columns of these dataframes man, mention what [the consumer] needs."
- **Defaults and opt-in flags**, stated correctly (a positional argument that is not required is not a default).
- **Steps that change data** (a merge, a join) named.
- **What is deliberately left out**: "No full [ecosystem] object yet; that is a later PR."
- "No new dependencies. Closes #N."
- **Every identifier in backticks.** This was corrected four times in one day.
- Careful wording about compatibility: "compatible with X's spec", never "is an X object".
- Human git tone: short, professional, no fluff. Run the `humanizer` skill on it where installed.

An example in that shape (a general instance, not from the source work):

> Adds `pkg export predictions`, which writes the model's per-row predictions next to the input table so
> downstream tools can read them without the training environment.
>
> `pkg export predictions -i run/ -o out/` writes `out/predictions.parquet` with columns `row_index` (uint32,
> index into the input table), `pred` (int, class id), `score` (float32, softmax probability) and `keep` (bool,
> `score >= --min-score`). Rows are never dropped; consumers filter on `keep`.
>
> `--min-score` defaults to `None`, which sets `keep` to true for every row and reproduces the previous output.
>
> Not in this PR: calibration of the score. Review: `src/pkg/export/predictions.py`.
>
> No new dependencies. Closes #12.

**A fix to geometry or to an algorithm carries its check in the PR, with a number.** Run it on adversarial toy
inputs (a concave shape, a thin arc, an empty or degenerate case) and on the common case. State the measured
result for each, and say that the common case is unchanged. In the source work a hand-written ring tracer was
replaced by a library polygonizer, and the PR showed an L-shape returning a valid concave polygon at 0.65 of its
convex-hull area, while ordinary shapes did not move.

**An internal review copy may use headings**, in this order: What (commands first), Why these choices (the
deliberate scope cuts), Files (with added lines per file), Correctness note, Verification, Follow-ups. The
upstream message keeps the no-heading form above; the internal copy was the earlier, longer version of the same
PR.

**An issue or a post to an upstream project is drafted as a file first.** Head it `DRAFT, not yet posted`. Give
the context and what the project produces (files, keys), quote the maintainer's earlier guidance from the thread
("Per your note in the thread ..."), then one explicit question on its own line ("Ask: would you accept ...?")
and an offer to open the PR. It is posted only when the owner says so.

## 7. Pushing, the pre-push audit and sizes

**When to push.**

- **Never push unless asked, and a standing instruction counts as asking.** When the owner has said to push after
  each milestone ("push the latest changes", repeated through months of one project), push the code changes
  (results or docs only when named) to the agreed branch once a figure or analysis settles, and give the commit
  hash in the report. Without such an instruction, nothing is pushed.
- **Push your own research repository early and often**: at least once per working day and always before a risky
  change, only the code, ops and docs folders. "you have not pushed anything to github today?????"; "before any
  change push tho!"
- **A one-day team repository whose owner says to push straight to `main`** ("from now on whatever arrives push
  directly to the repo main"): record that instruction in the repository notes, pull before every push so the
  branch stays mergeable, and never force-push.

**The pre-push audit**, for a repository that holds private material (drafts, reviews, data, keys) or that is
about to change visibility:

```bash
gh repo view --json visibility,isPrivate                       # is the remote what you think it is
git remote -v; git branch -a
# secrets anywhere in history, with a token boundary; add the key prefixes of the services you use
git log --all -p -G'(^|[^A-Za-z0-9])sk-[A-Za-z0-9]{20,}' --format='%h %s'
# blobs over 50 MB anywhere in history, including deleted files
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob" && $3>50000000'
git for-each-ref --format='%(refname)' | grep -v '^refs/heads/'   # non-branch refs that a mirror push would carry
ls .git/hooks | grep -v sample                                     # hooks someone added
git branch --no-merged origin/main                                 # the only branches worth pushing
git status --porcelain                                             # uncommitted files the push leaves out
```

- Push the current branch and only the branches with unique commits. Never merge a diverged `main` without asking.
- In zsh a variable holding several refspecs is passed as one argument: `git push origin ${=refs}` splits it,
  `git push origin $refs` does not.
- Report the uncommitted files left out, and any file the sync excludes (a large array file, say) that the push
  would delete on the other side.
- For a public release, publish from a clean snapshot (`research-release`); do not flip a working repository to
  public.

The recipes above were run on a scratch repository with a planted key, a deleted 2 MB blob and two branches.

**Sizes.**

- Never commit a file over 100 MB (the hosting limit); look at anything over 50 MB first.
- A 230 MB push failed with HTTP 408 and succeeded with:

```bash
git -c http.version=HTTP/1.1 -c http.postBuffer=524288000 push origin main
```

- In zsh, `${PIPESTATUS[0]}` is empty: capture `$?` directly after the push, without a pipe, or a failed push
  reads as success.

## 8. Handing a slice to a collaborator's repository

Code shared so a colleague (or a colleague's agent) can reproduce one result is the smallest slice that produces
it. The owner's words: "very very minimal LOC ... no fluff".

- **One entry function whose default selects everything**, for example `embed_table(df, which="all")`, and one
  plotting module (`vis.py`) that reads its output and redraws every figure.
- **A README of three points**: why, how to run, what comes out. `documentation.md` section 2 has the sprint
  README.
- **The receiving repository's own layout**, usually a subfolder of its `scripts/`, on a branch of that
  repository; never a separate repository.
- **Left out**: the research harness, the generators of the whole figure set, agent files and skills ("not a
  skill, do not emit any of skill"). Tests stay home when the owner says so ("dont push tests tho!").
- **Push every script the colleague needs to rerun the figures**, and nothing else.
- **Pull the target branch first** so the branch merges without conflict ("could you make the branch mergebale by
  pulling?").
