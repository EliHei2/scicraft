# The laptop writes, the remote computes

## Roles

- The laptop holds the working copy: code, configs, documents. The author "develops code locally on their Mac but
  never runs the project locally". No local installs of the heavy stack; local checks are `python -m py_compile` and
  import. A verification step in a plan says "on the remote".
- The remote runs jobs and holds data and results. Code reaches it by sync; results come back by sync.
- Scheduler commands, job scripts and resource requests belong to `cluster-jobs`.

## Sync

```bash
scripts/sync.sh up   -n  .                       "$REMOTE"          # preview
scripts/sync.sh up       .                       "$REMOTE"          # code up
scripts/sync.sh down     "$REMOTE_RESULTS"       results/runs/      # results down
scripts/sync.sh up --exclude '*.pt' . "$REMOTE"                     # extra excludes
```

| Rule | Why |
|---|---|
| `rsync -rtvu` both ways | `-u` never overwrites a newer file on the receiving side |
| never `--delete` | a file on the other side may be the only copy |
| never `.git` | an rsync from the remote overwrote `.git/config` and `origin` vanished twice in one session |
| up excludes `__pycache__ *.pyc .DS_Store data runs results scratch _attic *.egg-info .pytest_cache .venv` | outputs and caches stay where they were made |
| down writes into the results tree only | the script refuses a destination that holds `.git` |

The original laptop-to-remote script carried the comment "never overwrite newer cluster files; never --delete".

When `origin` is gone: `git remote add origin <url>` with the URL from `.git/FETCH_HEAD`. Run `git remote -v` before
every push.

## One writer

- When two sessions (one on the laptop, one on the remote) work on one deliverable, one writes and the other supplies
  facts and audit findings. Take facts from the other session, "never its text".
- The remote's fetch can overwrite a laptop file of the same name. Keep separate mirror folders for what comes from
  each side, compare with `cmp` before reassuring anyone, and say in the first line of a reply where the author's
  version is.
- The author told the laptop session: "you are the writer". The remote builds; the laptop words README, docs and
  model card, and publishes. No pushes from the remote.

## Drop folders

For hand-offs through shared storage:

```text
from_remote/   STATUS.md, rc1/, rc2/, final/, review/
from_laptop/   NOTES.md, paper/
```

- Allowed transfer verbs: `about lsf lsjson size mkdir copy copyto check`, always with `--checksum`. Never `sync`,
  `move`, `delete` or `purge`: "Only new or changed files move; nothing is deleted."
- After a pull, print the head of `STATUS.md`.
- Before handing out a shared link, check its permissions and say what it exposes: anyone with an edit link can
  delete everything in the folder, and a remote job may later write unpublished data into it.
- Never put a secret in a chat or a log. Run credential steps in the user's own terminal, and check them with
  commands that print only "set" or "EMPTY".
