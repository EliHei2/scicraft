# Hand-off to a cluster-side agent

When an agent session runs on the cluster (it can submit, the laptop agent cannot), the laptop
writes its brief. The author moved heavy work into fresh sessions with a brief more than eight
times ("make a handoff.md and I'll start a fresh chat not to make mistakes"). The template is
`assets/handoff_brief.md`; this file gives the reason for each part. Brief writing in general
belongs to `prompt-writing`.

## Delivery

- The brief is one self-contained file. The chat gets one line:
  "Read <dir>/BRIEF.md in full and carry it out, starting with stage 0. Do not open PHASE2.md until
  the brief tells you to." `scripts/push_brief.sh` checks every file is non-empty, opens one ssh
  control connection, creates the directory, sends the files and prints that line.
- Results come back by copy into a local inbox: `scripts/pull_results.sh HOST OUTBOX results/inbox`
  moves only new or changed files, deletes nothing, refuses a destination outside an inbox, and
  prints the first 40 lines of the cluster's STATUS.md. It stops with "PULL STOPPED: no STATUS.md
  found, nothing copied" when the cluster session has not reported yet.
- When the remote agent must run analysis code, ship the code itself in the staged folder, never
  pointers to it. Add a path map for every script that hard-codes a local path (103 of 1,249
  scripts did in the source work). Send it with one rsync into a new subfolder, so nothing the
  remote agent edited is overwritten.
- A brief carries a version and a date and says that it replaces every earlier copy.

## The skeleton, and why each part is there

1. **The job and done-tests.** The deliverable in one sentence, the author's words that set the bar,
   and "done when these N checks pass", each a command someone can run. A second version of one
   brief moved the done-tests to the top a day after the first. Also: what is running and must not
   be touched, and what this job is not.
2. **Names and places.** Every path and id once, in a table, with its rule (read-only, shared,
   quota). The exact checkpoint, commit and config of record.
3. **Rules, numbered.** Disk (measure first, a floor, caps, ask above a cap); deletion (only folders
   this job made); privacy (what never leaves); claims (who may write numbers); compute (check the
   queue first, job-name prefix, no arrays where forbidden, resume-safe launchers, the environment
   block); no pushes; gates ("passed means the command prints the value; fail means stop that
   front"); scope (ideas go under Proposals).
4. **How to work.** STATE.md for context resets; DECISIONS.md, one line per open choice; a lead and
   at most three helpers, one per front; check each helper's gate yourself; one pair of hands per
   shared artifact; cheap models for mechanical work; fresh agents for audits.
5. **Stage 0.** Orientation reads in order, with precedence stated ("X wins over Y on every
   conflict"; superseded drafts named and quarantined); then **the one gating measurement** with a
   stop rule ("If it is already at or below the floor, say so immediately and stop. Report this
   number before proceeding."); golden outputs or the noise floor recorded before any change.
6. **Work units.** Goal, method, gate with a number, "Falsified if:", out-of-scope items each with a
   reason, traps each with its incident ("Do not write anything you care about to /tmp. A previous
   session lost an entire workflow's output that way."). Contested decisions get the ruling and a
   dissent clause: "if you disagree after reading both, say so explicitly rather than silently
   picking."
7. **Order.** Serial, then concurrent, then conditional. "If you can only run one thing:". A
   give-up order.
8. **Hand-off channel.** The folder tree both ways, the allowed transfer verbs (copy with checksums;
   never sync with delete, move or purge), what never travels.
9. **Final audits by fresh agents** without the brief: a newcomer run, a break-it run, a leak scan,
   numbers traced to files.
10. **Report contract.** One file. The gating number first. Per item kept, killed or inconclusive
    with the run that settles it. Wall time and peak GPU memory per arm. "Do not synthesise a
    conclusion the numbers do not support."
11. **Ask the operator**, only under named conditions (a cap or floor would be crossed, a gate cannot
    be met, a semantic decision is needed).

## Protecting what is running

A brief that changes code a running campaign uses:

- builds every new mechanism behind a switch whose default is the current behavior;
- proves equivalence first: with every switch off, the new code reproduces the old outputs
  bit-identically, before anything is submitted;
- launches new arms under their own tag and directory ("One TAG per arm, never reused"; never clean
  another namespace);
- keeps the floor arm (the control that tells signal from noise) as non-optional;
- reports a verdict per mechanism.

## The pick-up brief (watch a gate, then launch)

For an agent that takes over right after the operator submitted something:

1. Role and moment: "You are picking up X right after the operator did Y. Your job: read the logs,
   decide go or no-go, and if go, launch and watch."
2. Capability limits: "You cannot ssh, rsync or submit from this laptop. The operator runs commands
   or pastes log excerpts. Ask for exactly the command output you need, one command at a time." The
   fix loop: edit, test locally, commit, the operator syncs, resubmit.
3. Read before acting: a short list.
4. "Go only if ALL hold": numbered checks with numbers (no error; the GPU busy fraction at or above
   a threshold; peak GPU memory fits the card; every loss finite; step time x steps fits the
   window).
5. Pre-staged fallbacks, one override each, mapped to failure regimes; a conservative configuration
   as the last resort, which is a different run, not a resume.
6. What to run after.
7. "Report outcomes faithfully: if a guard fired, say which and what the log showed; if a check was
   skipped, say so."

## The numbers worker

When the laptop stays the writer and the cluster only computes:

- first line: "The laptop stays the writer. From you: numbers from stored records only, no
  re-encoding, no training, no text";
- one `.md` and one `.json` per task, written as soon as each is done so partial results can be
  fetched;
- each task headed by the operator's decision and its date, with the exact columns wanted, "do not
  re-run, only re-adjust", and "say plainly where the records do not allow it".

## Taking results back

- Take facts and measurements from the cluster session, never its prose. Check each quoted number at
  its source before using it; a background agent that reports "completed" with an empty result
  produced nothing.
- One writer per artifact. The same instruction sent to both sessions produced two versions; compare
  with `cmp` before reassuring anyone, and say in the first line where the author's version is.
- When data is missing on the laptop, hand over a paste-ready fetch list ("tell me what to get from
  the cluster"), never an estimate.
- **When a fetch needs the user's password, write a script the user runs in one line**:
  `scripts/fetch_capped.sh`. It fetches the small notes first, then measures the rest with
  `rsync --dry-run`, and stops without downloading if the total is over a cap or the download would
  leave less free disk than a floor (6 GB each in the instance). It can resume, and it ends by
  printing `FETCH DONE` or a one-line reason. Run its `--self-test` and a `--source-dir` run on a
  local mock of the remote tree with the laptop's own tools first: on macOS the original failed
  twice, once on a file counter under BSD tools and once on an ssh option string that rsync 2.6.9
  read as a path.
- **rsync keeps the remote modification times.** Find newly synced results by change time
  (`touch stamp` before the pull, then `find . -cnewer stamp`, or `stat` ctime), never by mtime.
- **If a paste overwrites a local file, stop writing to that disk.** Restore from a local
  filesystem snapshot if one exists (on macOS, mount a Time Machine local snapshot read-only,
  check the size, copy with `cp -p`), or copy the file back from the remote side.
