# Brief kinds: what each skeleton adds and why

Every kind uses the anatomy in `anatomy.md`. This file covers what each kind adds, what it leaves out, and how
to choose between kinds. The skeletons are in `assets/`.

## Choosing

| Question | If yes |
|---|---|
| Will the receiver run for days, or lose its context? | long run: add STATE.md, STATUS.md, a date table |
| Is the receiver on a machine you cannot reach? | long run or pick-up: add capability limits and a hand-off folder |
| Has the job just been launched, so the next step is to read logs and decide? | pick-up and watch |
| Does a writer session need numbers from records it cannot open? | numbers worker |
| Are three or more agents doing parts of one artifact? | shared contract plus lane prompts |
| Is the job to find faults, not to build? | adversarial audit (read-only) or fact check |
| Is the artifact built and close to delivery? | proofreading round, looped with a fresh agent each time |
| Is the text the author's own craft? | polish pass, never a rebuild |
| Is this chat crowded, and is the next step "decide, then build"? | fresh-chat hand-off |
| Will code call a model many times with the same instructions? | system prompt |
| Will an image model draw a figure from the prompt? | figure-drawing prompt, in two parts |

## Long run on another machine (`assets/long-run-brief.md`)

Source: a release brief (450 lines, version 2) and a model-redesign brief (about 200 lines). Both were sent with
a script that printed one line to paste.

It adds:
- **Names and places** with read-only marks and quotas.
- **Rules** for disk, deletion, privacy, provenance, claims, compute, pushes, gates and scope.
- **How to work**: STATE.md for resets, DECISIONS.md, the agent policy (a lead plus at most three agents, one per
  front; it checks their gates itself; one pair of hands per shared artifact; a cheaper model for mechanical work
  such as link checks, leak scans and notebook execution), and the reporting cadence.
- **The hand-off channel**: a folder tree in both directions (`from_cluster/` with STATUS.md and release folders
  `rc1/`, `rc2/`, `final/`; `from_laptop/` with NOTES.md), with the allowed transfer verbs listed. Use copy and
  check only, with checksums, and never sync, move, delete or purge. Say what never travels.
- **Final audits by fresh agents without this brief**: a newcomer who uses only the public docs, a break-it pass,
  a leak scan with zero hits, consistency from a clean clone, and every number traced to its file.

Why the fresh auditors must not see the brief: an agent that has read the brief knows what the docs meant to say,
and it will fill in for a gap that a newcomer would trip on. The rule for the fixes: "Every stumble is fixed in
the docs or the package, not explained away."

Process weight: the release brief cut the ceremony of the earlier campaign on purpose. Keep pre-registered
decision criteria for gates whose data has not arrived yet (write the criteria before the data, with a noise
floor such as "a move under 2x SE is noise"). Leave out stewards and judges for engineering jobs.

## Pick-up and watch (`assets/pickup-watch-brief.md`)

Source: a 69-line brief for an agent that read the logs of a gate job, decided go or no-go, and watched a training
run.

It adds:
- **Role and moment**: "You are picking up the repository right after the operator synced it and submitted the
  gate job."
- **Capability limits**: "You cannot ssh, rsync or submit from here. The operator runs commands or pastes log
  excerpts. Ask for exactly the command output you need, one command at a time." Then the fix loop: edit, test,
  commit (no attribution), operator syncs, resubmit.
- **"Go only if ALL hold"**: numbered checks with numbers. For example: no Python error; GPU busy at the median
  at least 0.6; 99th-percentile memory fits the card at the planned batch size; every loss finite; no guard record;
  milliseconds per step times the planned step count fits the time window.
- **Pre-staged fallbacks**: one config override each, mapped to a failure regime (collapse, a diffuse blob, the
  field turning into a lookup table). Add one conservative configuration that is known to be bit-identical to the
  old objective, labeled "a different run, not a resume".
- **Watching**: which log keys, how often, which guards are fatal and which only warn.
- **Close**: "Report outcomes faithfully: if a guard fired, say which and what the log showed; if a check was
  skipped, say so."

## Numbers worker in a writer and worker split (`assets/numbers-worker-brief.md`)

Source: round prompts sent to a cluster session during a paper revision, while the laptop session wrote the text.

It adds:
- **Roles in the first line**: "The laptop stays the writer. From you: numbers from stored records only, no
  re-encoding, no training, no text."
- **Output layout**: one `.md` and one `.json` per task, plus a one-page index. "Write each file as soon as it is
  done."
- **Vocabulary and forbidden comparisons.**
- **Tasks**, each headed by the operator decision that caused it and its date, with the exact columns wanted, "do
  not re-run, only re-adjust" where that applies, the writer's own value for a cross-check, and "say plainly where
  the records do not allow it".
- **A last task that checks the writer's new statements** against the records.

Why the roles: one message once went to both sessions and came back as two versions, and the author feared an
overwrite. The writer takes facts from the worker and never text.

## Shared contract plus lane prompts (`assets/shared-contract.md`, `assets/lane-prompt.md`)

See `fan-out.md`. Named roles seen in lane prompts: surgeon, de-AI editor, narrator ("not a critic: your job is to
understand why the authors did each thing"), red team of one, design director, statistics referee, talk coach,
fresh-context auditor, camera-ready auditor.

## Adversarial audit or refutation (`assets/adversarial-audit-brief.md`)

Source: a refutation preamble used in a design audit, a book audit-and-fix contract, and a two-lens audit of
rebuttal replies.

It adds:
- **Identity and posture**: "You are the adversarial phase. Read-only on src/; write ONLY into OUT." Then
  "Posture: refutation. A mechanism that 'could learn' X has not survived."
- **Why you exist**: what was done upstream, what has had no review, and what being wrong costs ("the last thing
  standing between a pile of self-consistent reasoning and a cluster run that costs a day").
- **Budget discipline as requirement number one**: quote existing outputs and do not re-measure; run something only
  if a verdict hangs on a missing number (one small script, output committed); write incrementally; verdict
  sections first; "Attack, do not summarize."
- **Known corrections**, flagged "do NOT report this as a finding".
- **Measured results in hand** as a table to quote.
- **Output schema per finding**: `quote` (exact text), `problem`, `severity` (blocker, major, minor),
  `evidence` (source text with page or line), `fix` (exact replacement or DELETE).
- **For audit-and-fix variants**: "minimal fixer: repair only those places, with the smallest edit that restores
  compliance. Text that is compliant stays exactly as it is." Log before and after with the rule and the source
  line.
- **Reviser step** (a separate agent or the lead): "Verify each one yourself. Apply every blocker and major
  finding that holds, and minor ones that are clearly right. Return the findings applied, and the findings
  rejected with the reason."

Each new round targets what earlier rounds did not cover (for example efficiency and comparison with working
models after two rounds on correctness). The loop itself is `adversarial-audit`.

## Fact check (`assets/fact-check-brief.md`)

Source: a fact-check brief reused across several rounds. The yields it recorded were 87 statements with 0 wrong and
10 imprecise, and 140 statements with 1 wrong.

It adds: "trust nothing you are told"; counts of CONFIRMED, WRONG, IMPRECISE and UNVERIFIABLE; the true
replacement wording for each imprecise item; the sha256 of the audited file; ranks recomputed by script from the
printed table, not read from the text. Confidentiality line for unpublished material: "Work only from local files.
Do not use web search or web fetch, and do not send any of it to an external service."

## Proofreading round (`assets/proofread-round-brief.md`)

Source: a zero-defect loop on a revised paper and its replies. Round 1 found 10 defects, and round 2 found 15
(mostly bold lead sentences that claimed more than the cited lines showed).

It adds:
- A snapshot folder: the built PDF, its `pdftotext -layout` text with line numbers, the replies, the reviews.
- One fresh agent per round. "Impartial and somewhat adversarial ... You did not write any of it and you owe the
  authors nothing."
- The passes: (A) every labeled point answered, part by part; (B) every number, table, figure and line range
  checked at the cited place; (C) the document against itself (counts against figures, captions against what the
  figure draws, one name per thing, unexplained markers); (D) only quotable items a human reader would hold
  against the authors.
- Out of scope: new content, new experiments, framing and tone.
- The round number and what is expected from it: round 2 is "a second round on a corrected version, so a short
  report is fine"; round 3 is "a confirming round ... do not pad, and do not re-raise the excluded items below".
- Give voice its own pass or its own reader. Three proofreading rounds checked facts and missed awkward machine
  sentences that the author caught in minutes.

## Polish pass (`assets/polish-pass-brief.md`)

Source: the rejected rebuild and the brief that replaced it. After the rejection, each audit was briefed: "This
is a final polish. Do NOT propose a rebuild, a new structure, new sections or a new style."

It adds: the base file (the author's last version, found by listing every version in the log with its turn and
length); the allowed edits; the frozen parts ("do not recompute the tables, they were accepted"); the rules file;
a list of every change against the base. If the agent thinks a rebuild is needed, it says so in one line and
stops.

## Fresh-chat hand-off (`assets/handoff-fresh-chat.md`)

Source: at least eight hand-off files written when a thread turned from discussion into "decide and then build":
"instead of changing the code here generate a clean prompt for another code-focus chat ... as it's cleaner, not
so crowded"; "make a handoff.md and I'll start a fresh chat not to make mistakes".

It adds: the goal, the constraints the author has set (the guardrail ids that apply, quoted with their text, and
the short goal, as defined in the sibling skill, `project-structure/references/governing-documents.md`; then any
constraint set in the chat, dated), what has been tried with links to the
result files, the open decision points with the options, and the exact deliverables (a script, a table, images).
The new chat starts from one line: "HANDOFF_<topic>.md: read it in full and go."

## System prompt (`assets/system-prompt.md`)

Suggested, not yet tested in real work. No system prompt for a model called from code appears in the evidence.
The skeleton carries over the parts of the anatomy that do not need a file system: the job and the done-test, the
vocabulary, the rules, the output schema, the refusal path ("if the input does not allow an answer, return
`{"status": "insufficient", "missing": [...]}`"). Test it the way the anatomy tests a brief: a set of inputs with
known answers, scored by a script, never by the model itself.

## Figure-drawing prompt for an image model

Source: one episode of four prompts, written over two days for an architecture figure drawn by an external image
model. The author asked first for a short prompt, "just the architecture and the SSL", with no word of the home
field and the data called points. Then the author asked for "more technical details", and that figure came back "too
complicated". The form that worked: "provide all the details in the model to desribe then describe what to draw".

Two parts, in this order:

```
A. The model. [Inputs as tokens, with their shapes.] [The encoder and predictor blocks.] [The attention pattern:
   who attends to whom.] [The masking: what is hidden and how it is chosen.] [The losses and where each is
   computed.] [What is frozen or updated by moving average.]
B. What to draw. [Number of panels and what each shows.] [What to leave out: every detail below this level.]
   [The exemplar figure to imitate, by citation and figure number.] [Palette: three or four colors plus black,
   as hex.] [Font and the smallest size.] [Vector output.]
```

- **Write part A in full.** A short spec gave a vague figure; the drawing model invents what it is not told.
- **Keep part B spare.** Detail belongs in A; B says how little of it to show: "show really highlevel ... not
  every detail but a sign of every step".
- **Write both parts domain-neutral**: points, elements, regions, fields, never the objects of the home field. The
  figure then shows the architecture alone.
- **Name the exemplar** instead of describing a look in adjectives (see `taste.md`).
