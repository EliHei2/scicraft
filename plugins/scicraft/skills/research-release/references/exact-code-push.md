# Pushing exactly the code that produced the numbers

When a paper's numbers come from code that has since moved on (a benchmark metric, an evaluation script, a
preprocessing step), the public release of that code is the code that ran: "no new stuff or correction ...
reproducible 1:1", "exact metric, no new stuff". Fixes and new functions are separate decisions for the author.

Recovering code that survives only as compiled bytecode, and recomputing published values with it, is the
`integrity-audit` skill. This file is the push.

## Before the push

- **Name the branch, the commit and the date** of every state you talk about. "Wait new GitHub or old GitHub?
  Which one?" came when "the GitHub code" changed the same day. A small table with one column per state (old head,
  new head, side branch) and rows for function identity, command-line defaults, other functions that differ and the
  date made public. Run `git ls-remote origin <branch>` before stating the current head.
- **Command-line defaults change only when the author decides, and the release note says so.** Otherwise give
  the run value in the rerun instruction as the benchmark setting (`--min-<unit> <value>`). In the instance the
  published setting differed from the function default. Mention a default only when it explains
  someone else's failed rerun, and then as a rerun instruction. Never describe the difference as a discrepancy in
  the paper. The `integrity-audit` skill owns this rule (`integrity-audit/references/tracing.md`, step 9).

## The recipe

1. Clone the remote into a scratch folder and branch from the target branch:
   `git clone <url> "$SCRATCH/push" && git -C "$SCRATCH/push" switch -c <release-branch> origin/<base>`.
2. Take files from other refs with `git show "${REF}:path/file.py" > path/file.py`. **Brace the variable**: in zsh,
   `$B:s` is read as a substitution modifier, and the redirect had already truncated the file when the error showed.
3. Strip every function the run did not contain, and verify identity against what ran. In the instance:
   0 bytecode differences across all 141 code objects against the compiled files archived from the run, plus the
   file size and the line number of a known runtime warning. Where source of the run exists, `cmp` against it.
4. Tests in a clean environment with pinned versions:
   `uv venv -q --python 3.11 venv && uv pip install -q --python venv/bin/python <pinned versions> pytest`, then
   `PYTHONNOUSERSITE=1 venv/bin/python -m pytest`. A stub package root (real submodules, an empty top-level
   `__init__`) lets CPU tests run when the package imports a GPU stack at the top.
5. `git status --short` and `git diff --stat`: only the intended files changed. `git ls-remote origin <base>`: the
   remote tip has not moved since the fetch.
6. Commit and push fast-forward only. Never force.
7. Download the pushed file back from the host (`curl -sL <raw url> -o check.py`) and verify it again against what
   ran.
8. Run the public command line end to end on one real input with a fresh agent. In the instance this showed that
   the branch's data loader was older, so a full run needed a loader from another commit. That was reported, not
   ported: "Porting it was not part of what you authorised, so I left it."
9. Record the branch, commit, date and the identity check in the project's notes and in the paper's code
   availability statement.

## Guaranteeing that a job runs the shipped code

Set `PYTHONNOUSERSITE=1`, put the source first on `PYTHONPATH`, call `"$PY" -m <pkg>` instead of a console script,
and assert inside the job that `<pkg>.__file__` lies under the source folder you shipped. An editable install can
shadow `PYTHONPATH`, and a stale tracked copy of the package at the repository root shadowed `src/<pkg>` whenever
the working directory was on `sys.path`.
