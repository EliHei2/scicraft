# Checking a brief before it is sent

The receiver cannot ask what you meant. Every gap in the brief becomes a guess, and a guess comes back reported
with the same confidence as a finding. Check in this order.

## 1. Scripted

```bash
python3 scripts/check_brief.py BRIEF.md --kind long-run
python3 scripts/check_brief.py lane_03.md --kind lane --max-lane-lines 6
python3 scripts/check_brief.py CLAUDE.md --kind claude-md
python3 scripts/check_brief.py --list-kinds
python3 scripts/check_brief.py BRIEF_v2.md --previous BRIEF_v1.md --dropped-ok rc1/ --dropped-ok 450
python3 scripts/check_brief.py --self-test
```

The script reports `ok`, `MISS` and `warn` lines and exits 1 on any miss. What it checks:

| Check | Kinds | Why it exists |
|---|---|---|
| required elements (done-tests, reading order, precedence, stage 0, stop rule, numeric gate, falsifier, out of scope, traps, dissent, report contract, output path, writing as it goes, ask list, state file, dated words) | per kind, see `--list-kinds` | the anatomy in SKILL.md section 1 |
| unfilled `[placeholders]` | all (off with `--template`) | a skeleton sent unfilled |
| home paths, emails, API keys, private keys | all | briefs travel to other machines and sessions |
| lines ending in a backslash inside code blocks | all, warning | a pasted two-line command overwrote a 9.9 GB file |
| "the latest checkpoint", "the current version" | all, warning | a vague reference gets whichever one the receiver finds |
| output written to `/tmp/` | all, warning | a workflow's output was lost on reboot |
| lane prompt length | lane | lane prompts stay at 3 to 6 lines; the rest belongs in the contract |
| word count and numbered rules | claude-md | CLAUDE.md loads every turn: 200 to 500 words, up to ten non-negotiables |
| guardrail ids, the short goal or the definition of done quoted | long-run, pickup, worker, contract, audit, handoff; warning | a helper does not read the repository unless told to, so the brief carries the lines that bind its task |
| paths, file names and numbers lost in a rewrite (`--previous`) | any | each rewrite of a release brief was checked this way; a dropped path or number changes the job without anyone deciding it |

The element checks are keyword searches. A hit says the element is mentioned. It does not say the element is
right.

## 2. Read against the sources

- **Every assertion in shared text has a source**, and you have read the source. Diff the preamble's claims
  against the raw outputs. A preamble that contradicted its own table sent six agents to confirm a false claim.
- **Every number in the brief has the file it came from.** Thresholds have the measurement they were set from
  (the noise floor, a stage-0 value).
- **Every quotation of the author is verbatim and dated.** Search the log for it if you wrote it from memory.
- **A rewrite lost nothing by accident.** Keep the old version and compare the two by script:
  `check_brief.py NEW.md --previous OLD.md`. It lists every path, file name and number of the old file that the
  new one lacks. Name each token dropped on purpose with `--dropped-ok`; put every other one back. In the source
  work this check ran on every rewrite of a release brief, because a rewrite that tightens the prose also drops a
  cap, a folder or a threshold without anyone deciding it.
- **The lines that bind the task are quoted**: the short goal, the guardrail ids with their text, the definition
  of done (the documents are defined in the sibling skill, `project-structure/references/governing-documents.md`).
  The final check of each unit runs against `GUARDRAILS.md`.
- **Every external fact was verified.** That includes facts from another chat model, a pasted colleague note, or a
  citation written from memory.

## 3. Read as the receiver

Open the brief in a fresh view and assume no memory of this conversation.

- Is every name defined: symbolic paths, run ids, roles, the operator?
- Is every path absolute or a declared symbol? Does it exist on the receiver's machine?
- Is "done" checkable by the receiver alone?
- Does the stage-0 measurement have a threshold and a stop?
- Does each work unit have a gate with a number and a "Falsified if" line?
- Is the report contract fixed: where it goes, what comes first, how long it is?
- Is it clear what the receiver must not touch: running jobs, other sessions' folders, files outside its own?
- For a lane prompt: does it point at the contract, name the lane, the files owned, the output, and the neighbor's
  scope?
- For a polish pass: is the base file named, and is a rebuild forbidden?
- For reader-facing work: is there a vocabulary block and a list of words that must never print?

## 4. Delivery

- One live version. The superseded file is renamed, and the version line is current.
- The paste line names the file, the first step, and what must not be opened yet.
- Commands for the user are one line each, or one `bash <script>` line, and you say what success prints.
- A prompt that will run with the user's credentials was read line by line. It has a hard scope (one destination,
  copy-only), a dry run that writes PLAN.md first, and stop conditions (a size cap, a destination outside scope,
  any replace).
- The same request is not going to two sessions.

## 5. Say what was not checked

Name each gap in your message to the user. Examples: a path not verified on the remote machine, a command in the
brief that was not run, a threshold not yet measured. "Never claim a gate passed when it is still running" applies
to briefs too. If an earlier version of the brief was audited, say which checks cover this exact version.
