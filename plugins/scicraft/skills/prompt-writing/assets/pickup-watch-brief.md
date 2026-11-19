You are picking up [the repository, with its path] (read its CLAUDE.md first) right after the operator [synced it
to the cluster and submitted the gate job `[job script]`]. Your job: read the gate's logs, decide go or no-go, and
if go, help launch and then watch [the run]. Constraints you must respect:

- You cannot [ssh, copy files or submit jobs] from here. The operator runs commands or pastes log excerpts. Ask for
  exactly the command output you need, one command at a time.
- Never run [training] on this machine. Local verification is `[test command]` (about [n] minutes, CPU). Any code
  fix goes: edit, test, commit ([no attribution lines]), the operator re-syncs, resubmit.
- Binding, quoted from the project's governing documents: short goal [S<n>] "[text, with its gate]";
  guardrails [G<n>] "[rule text]", [G<m>] "[rule text]". `GUARDRAILS.md` wins over every other document.
- Read before acting, in this order: `[what changed and why]`, `[the plan]` sections [n], `[the log keys and
  guards]`, `[job scripts]`. [Document] wins on any conflict.

## The gate ([log and metrics files])

Go only if ALL hold:
1. No error in the log. [What is new in this run and where a failure would show. A dtype or shape error here is a
   code bug: fix it, add the failing case to the tests, rerun them, commit, re-sync, resubmit.]
2. `[gpu_busy_p50]` at least [0.6]. Below it the loader starves the GPU. Fixes in order: [one override each].
3. `[peak memory p99]` fits the card at [batch size] ([card]: [n] GB). If not: [override].
4. Every loss finite; [named health signals within named ranges]; no guard record.
5. `[ms per step]` times [planned steps] fits the [time window].

If any check fails, say which, with the number, and propose the fix from the list above. Do not launch.

## Launching

`[launch script]` with [the placeholders filled: environment, config, held-out data]. It is resume-safe: [what a
requeue does, where it resumes from, which checkpoint is kept as best].

## Watching ([log file] every [n] steps)

- Fatal guards stop the job with `[guard:<kind>]` in the log: [list, each with what it means]. Warnings: [list].
  Read [the regime table] before reacting.
- Pre-staged fallbacks, one override each, resumed from `[resume checkpoint file]`:
  - [failure regime and how to recognize it, with numbers] -> `[override]`
  - [failure regime] -> `[override]`
- The conservative configuration ([the objective exactly as before date X, proven bit-identical]):
  `[overrides]`. Use it only if the new parts misbehave in a way the fallbacks do not fix. It is a different run,
  not a resume.

## After the run

[The evaluation commands, in order, and which scorer is of record.]

Report outcomes faithfully: if a guard fired, say which and what the log showed; if a check was skipped, say so.
