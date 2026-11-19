---
name: qc
description: The gate before anything is handed over (a figure, a paper or book build, a rebuttal reply, a deck, a web page, a report, a data deposit), ending in a short report of what was checked and what was not. Use this skill whenever work is about to be sent, uploaded, posted or shown, even when no check was asked for, and when the user says "make sure there are no mistakes", "0 discrepancy", "this is QC", "proofread it", "check everything before I send it", "camera-ready tonight", or asks what is still open after a crashed session. Holds the order that worked (scripted checks, then the render looked at, then every request traced, then what was not checked), the request ledger rebuilt from a transcript, the zero-defect proofread loop with its four-part brief, checklists per deliverable, report-only auditor roles, the report shape, and the rules to match the example and never overwrite a seen file. Prefer adversarial-audit for a large multi-agent audit and integrity-audit to verify numbers and claims.
---

# qc

How to hand work over so that the person receiving it finds nothing to fix. Distilled from a year of deliveries
under deadline for one demanding author: two rounds of rebuttal for a machine-learning conference paper, a book
delivered the morning after a twelve-lane audit, decks, a project website, a model release and a data deposit for
a journal. Each slip the author found personally cost trust in everything they had not yet looked at ("no mistakes
allowed anymore", "this is QC"), so every rule below is either a check that caught something or the fix for a slip
that reached them. Where the author of the work at hand states their own rule, it wins: write it into the ledger
(section 2) and check it like the others.

> **PRIME DIRECTIVE: nothing leaves until the scripted checks pass, the rendered result has been looked at, every
> request in the ledger is traced to what answers it, and the report says plainly what was not checked.**
> The order matters: scripts first because they are cheap, eyes second because scripts cannot see meaning, the
> ledger third because a request is the thing most easily lost, the report last because it is the only part the
> author reads.

Three failures cost the most time. Guard against them from the first minute:

1. **The slip the author finds personally.** A clipped label, a number that is not in the table it cites, a word
   they banned last week. The author stops trusting what they have not checked. Sections 3 and 4.
2. **The lost request.** Notes arrive faster than they can be applied; sessions get compacted; "I remember that
   one" is how a request vanishes for a day. Section 2.
3. **The wrong deliverable, or the seen one destroyed.** 73 per-panel data files were uploaded where five to
   fifteen short reference tables were wanted ("understand the context"); a figure the author liked was renamed and
   deleted with no copy left. Section 7.

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The deliverable and how it is built**: the build command, the output path, what the author will open (PDF on
  a phone, the deck, the live URL, the upload folder).
- **The example**, if one exists: a colleague's tables, the venue's template, last round's package, the earlier
  deck the author liked. It fixes the type, granularity and count of what is delivered (section 7).
- **The requests**: the conversation, the session transcript if it was compacted, notes pasted from elsewhere, the
  house rules file of the project.
- **The records behind every number** that will be stated, and the source of every quoted sentence.
- **The limits**: page budget, character limit per comment, file size cap of the upload or of the channel it is
  sent through, word limits, the deadline.
- **What may not leave**: unpublished results, private data, secrets; who will see the deliverable.

## 1. The order

Run these in order, every time, even under a deadline (the scripted part takes minutes):

1. **Wait, then build into a new name.** No build while a render or encode is still running (a deck built during
   an encode embedded a broken clip). Build into a scratch folder or a new file name, never over the file the
   author has open (section 7).
2. **Scripted checks** for this kind of deliverable (section 3 and its checklist). Zero problems, or each one named
   in the report with the author's own instruction that causes it.
3. **Look at the render** (section 4): every changed unit at working resolution, then the whole on one sheet, then
   crops of fine detail.
4. **Trace the ledger** (section 2): each request ticked against something you looked at, or listed as not done.
5. **Facts**: every number against its record, every quotation against its source, every cited line or page
   against the built document. For a full number and claim audit use `integrity-audit`.
6. **The proofread loop** (section 5) when the stakes are high (a paper, a reply, a release) and time allows.
7. **Report** (section 8), with what was not checked stated plainly. Before writing it, confirm no agent or
   background job is still running ("is that on purpose or is it stagnant").

## 2. The request ledger

Every instruction the author gives, in their words, with its time, in order, in `REQUESTS.md` beside the
deliverable. Append before acting. `references/ledger.md` has the format, the reading rules and the recovery
procedure; `assets/REQUESTS_template.md` is a blank one.

- **Tick a line only after looking at the thing that answers it.** A line ticked from memory is how the author's
  own three motivation points went missing for a day.
- **A later note overrides an earlier one; strike the earlier, never delete it.** A specific note beats a general
  rule ("max 25 words" yields to a sentence the author dictated for that slide); say so in the report.
- **Standing rules go at the top and into a guard.** A rule stated once ("no semicolons", "one name per thing",
  "light blue for every change") becomes a grep or a build check so it cannot come back.
- **A rule given for one place holds everywhere.** Sweep the whole deliverable, then add the guard.
- **Recover from the transcript, not from memory.** When a session was cleared, compacted or stalled, rebuild the
  ledger before doing anything new:

```bash
python3 <skill>/scripts/ledger_from_transcripts.py ~/.claude/projects/<project>/<session>.jsonl --since 2026-11-17T05:00 --out REQUESTS.md
```

  A terminology rule given at one o'clock and lost by five was found again this way, by searching the transcript
  for the author's earlier message.

## 3. Scripted checks

Scripts catch what can be measured, in seconds, every round. Run the ones for the deliverable at hand:

| Deliverable | Gate | Checklist |
|---|---|---|
| figure | text boxes measured for collisions and clipping, smallest type at print size, fonts embedded, numbers unchanged by a relabel | `references/checklist-figure.md` |
| paper or book build | four passes, 0 errors, 0 undefined, 0 overfull, no "Rerun", page budget, fonts embedded, line references re-resolved | `references/checklist-latex.md` |
| reply, message, prose | characters per comment, count of comments, quotations verbatim, every number found in the built PDF, banned strings | `references/checklist-text.md` |
| slides | words, gray or small type, overlaps, clips decode, package opens, size cap | `references/checklist-slides.md` |
| web page | overflow and one-word last lines at 390 to 1440 px, behavior checks, leak scan before every push, live check after | `references/checklist-web.md` |
| data deposit | type and count against the example, each file readable alone, identifiers checked, dry run, checksums after | `references/checklist-data-deposit.md` |
| report | opens offline with a double click, summary first, every conclusion backed by a number | `references/checklist-report.md` |

Scripts in this skill (Python 3.9 or later; PyMuPDF for `page_stills.py`; pdflatex, bibtex and poppler for
`latex_gate.sh`; poppler's `pdftotext` for PDF input to `sweep_terms.py`):

| Script | Does |
|---|---|
| `scripts/ledger_from_transcripts.py` | the author's instructions out of one or more session transcripts, as a checklist |
| `scripts/latex_gate.sh` | builds a LaTeX document in a scratch folder with four passes and fails on errors, undefined references, a pending rerun, overfull boxes or a wrong page count |
| `scripts/page_stills.py` | PDF pages to PNG by printed label or number, a contact sheet, a figure-to-page map |
| `scripts/text_drift.py` | sentence-level drift between two versions: proof that a pass changed only what it named |
| `scripts/apply_audit_edits.py` | checks an auditor's exact-match edits (unique, long enough, no overlap, no banned string) and applies them only if all pass |
| `scripts/sweep_terms.py` | every hit of banned or removed terms across PDF text, Word text, content files, tables and code, one line each |

```bash
S=<skill>/scripts
bash $S/latex_gate.sh paper/main.tex /tmp/gate --pages 10 --allow-overfull
pdftotext -layout /tmp/gate/main.pdf - | grep -nE '—|–|;|whisker|Holm|TODO|\?\?'
python3 $S/page_stills.py /tmp/gate/main.pdf /tmp/look --pages 1,8-10
python3 $S/page_stills.py /tmp/gate/main.pdf /tmp/look --sheet 1-24 --dpi 60
python3 $S/text_drift.py before/ after/ --show
python3 $S/sweep_terms.py --list banned.txt /tmp/gate/main.pdf reply.docx content/ tables/ code/
```

A word or pattern the author has banned goes into one list file that every build greps (the banned list of one
paper held "whiskers", "detectable", "Holm", "q" as a printed statistic, the dagger sign and the old name of a
renamed component). Scan the text extracted from the built output, never only the source: a macro can print what
the source does not show. When the author asks for something to be removed, sweep every output for it (built PDF,
Word copy, content files, generated tables, live figure code) and report each remaining hit; "removed" is written
only when the sweep is clean (`references/checklist-latex.md`).

## 4. Look at the render

The scripts cannot see that a caption describes a line the figure no longer draws, that an inset hides its own
source, that a float was stranded on a page that is 43% full, or that a picture makes no point. Render and read:

- **Working resolution.** 100 to 150 dpi for a page, 1600 px for a slide, 1440 and 390 px for a web page. Then the
  whole on one contact sheet, where a slide or page that differs from its siblings stands out.
- **Crops at two to three times** for fine labels, row annotations, legends, superscripts.
- **What to ask of each unit, in order:** the point (does the picture show what the title or caption says, to a
  stranger?); keys (is every color, marker and abbreviation explained?); collisions (does anything lie over
  anything else, touch an edge, or cover its source?); balance (equal margins, no third of the space empty, no
  lone word on a last line, panel bottoms level); sharpness (nothing soft, blocky or stretched); leftovers (a
  stand-in, an old label, a name that should not appear, a debugging mark, an unrequested revision color).
- **Look at the assembled whole, not only the part.** Crops after composition catch what the standalone panel hid.
- **Say what you looked at.** "I looked at pages 1, 8 to 10 and the changed appendix pages as stills" in the report.

## 5. The zero-defect proofread loop

For anything that will be judged by readers who owe the authors nothing (a paper and its replies, a release, a
book), loop one fresh, impartial and somewhat adversarial reader on the final build until a round finds nothing.
The author's request that started it: "run the agent again and again until 0 discrepancy is detected, and make the
agent really impartial, and a bit adversarial ... focus on human psychology and reviewer psychology".
`references/proofread-loop.md` has the procedure and the yields; `assets/proofread_brief.md` is the brief.

1. **Snapshot** into a fresh folder: the built PDF, its `pdftotext -layout` text with line numbers, the replies or
   accompanying texts, the verbatim requests it answers (reviews, the brief, the call).
2. **One fresh agent per round**, with the four-part brief:
   - **A.** every labeled point of the request has a direct answer, part by part;
   - **B.** every number, table, figure, appendix and line range cited in the accompanying text is checked at the
     cited place;
   - **C.** the document against itself on the changed pages: counts against figures, captions against what the
     figure draws, one name per thing, unexplained markers;
   - **D.** only items a human reader would quote against the authors.
   Out of scope, named in the brief: what the authors chose to include, new experiments, framing and tone.
3. **Fix, rebuild, start the next round with a new agent.** A new agent, because a reader that saw the last round
   checks its own earlier findings. The gate is zero findings.
4. **Asked for the files mid-loop?** Send the current build at once, say it is not final, and send the later fixes
   the same way (section 7 on names).
5. **Under a deadline**, stop after the round that fits, deliver, and say that the zero bar was not reached and
   what the last round found.
6. **Once the author has polished the text**, the loop ends. Run one focused audit per round on the author's draft,
   briefed "Do NOT propose a rebuild, a new structure, new sections or a new style". A swarm-fed rebuild of the
   author's own replies was rejected in full after three to four hours (`references/proofread-loop.md`, the endgame).

In the source work, round 1 found ten defects (a reply citing lines that do not hold the claim, a "full ranking"
promised in the main text and absent from the appendix, a core count that did not add up, main text and appendix
naming different tests, a caption not naming a dashed line, one target with two names). Round 2 found fifteen,
mostly bold lead sentences claiming more than the cited lines show. On a later package the third, confirming round
found one grammar slip and six one-word last lines. About fifteen minutes per round, run in the background while
packaging.

## 6. Narrow auditors that only report

When one reader is not enough (a submission, a camera-ready, a release), use auditors with **one persona and one
fault class each**, who read and report and never edit. One writer applies the fixes. The full multi-agent
procedure (lanes, skeptics, synthesis) belongs to `adversarial-audit`; the everyday form is here and in
`references/auditors.md`, with `assets/auditor_brief.md` as the brief.

- **Default to one auditor at a time; fan out only when the author asks.** Never start agents under a deadline,
  and never to make up for not looking yourself.
- **Roles that found real defects:** figure editor (every data figure against the text and tables, ranks
  recomputed), art editor (pixel level, in mm, each fix naming the code constant), register editor (every printed
  title and caption string), terms auditor (undefined, uncited or used-before-definition terms, duplicate names),
  statistics referee (one language, every test defined), fact checker (every statement against primary material,
  counts of confirmed, wrong, imprecise, unverifiable), citations in context, submission readiness.
- **The brief carries the facts and the question, never your conclusion.** A shared preamble asserted a claim
  three lines above a table that refuted it, and six agents reported the claim as confirmed. Hand an agent a
  hypothesis and expect it back confirmed.
- **Quote the author's rule verbatim in the brief** when an audit exists to enforce it.
- **Edits come back as data**: exact-match `[file, old, new, id]` items, QUERY items for the author's decision.
  Check each finding yourself against the source, then apply with `scripts/apply_audit_edits.py`. Decline with a stated
  reason where the auditor is wrong.
- **The author's taste overrides the panel.** Record a deliberate choice as a keep-as-is guard so the next round
  does not undo it.

## 7. Hand over the right thing, and never destroy what was seen

- **Match the example's type and count before delivering.** List the example files with row counts and column
  headers, write one line on what kind of thing each is, set a target count, and stage the delivery through an
  explicit whitelist. Your own reading of a category name ("source data") is not the specification; the example is.
- **Keep separate requests separate.** "Tables are something, data are something else": small curated tables and
  bulk files go to separate folders with separate manifests.
- **Never overwrite, rename or delete a file the author has seen.** Every variant and every delivery round gets a
  new name (`_r3`, `_noboxes`); back up before regenerating; check for an open-file lock (`~$Name.pptx`) and never
  open a half-built file in the author's application. A deck overwritten while open showed "the picture can't be
  displayed"; a liked figure deleted could not be recovered.
- **One delivery folder.** Move superseded deliveries to `retired/` (never delete), so the folder holds only what
  is current. Tell the author exactly which file to upload.
- **A build announced as not final** may be followed by fixes under the same names in the same folder, because the
  author was told; keep the earlier copy in `retired/`.
- **Deliver exactly what was asked.** An idea gets one line in the report, never an unrequested side deliverable
  (an extra reply to a third reviewer drew "why do you work on [that] response???").

`references/handover.md` has the staging, packaging and size-limit detail.

## 8. The report

The author reads it on a phone between other things. `assets/delivery_message.md` is the shape:

1. **What is delivered**, with paths and sizes, or whether it is live. One sentence on what was checked and what
   was not ("all gates pass; I looked at every changed page as a still; I have not opened the deck in PowerPoint").
2. **What changed**, one line per unit, in the author's words for things.
3. **What I did on my own judgment**: the running list of additions the author has not confirmed, sent with every
   delivery. A disclosure the author wrote is reported in one line and left for the author to cut.
4. **Please check**: each reading you had to guess ("I read X as Y"), each name, date or number you could not
   verify, each place where their instruction breaks a general rule and you followed the instruction.
5. **Not done**, with the reason and what it would take.

For an audit: counts by severity first ("0 critical, 2 major, 8 minor, 4 of them QUERY"), then the five most
important findings (ID, severity, file and line, problem, exact fix), then where the rest is. Per item: kept,
killed or inconclusive, with what would settle it. No praise, no list of what is fine, no explanation of the
tools, no glossary box, no bold walls. Never write that something was checked when it was not; never write a
conclusion the numbers do not support.

## 9. The gate checks honesty too

A gate that passes by hiding a problem has failed. Choosing what to lead with is presentation; changing what the
records support is misreporting, and the gate blocks it. The rules the source work kept:

- **A recompute that differs from a printed value is reported, never swapped in silently.** Find out why
  (different records, different units), tell the author, keep the print unless the print is wrong.
- **A claim is exactly as strong as the lines it cites.** "Significantly above [n − 1] of [n] comparators" where one
  comparator is not separated; delete a sentence that holds under one metric and is false under another.
- **A weak or contradicting result is never removed to make a deliverable pass.** It goes to the appendix or the
  backup with its number. A reporting threshold applies to every result alike and is stated.
- **Verify every exclusion before printing it.** "Has no fold-level scores" was false; the records held them.
- **An author's claim that does not hold is reported with the evidence**, and the version that can be verified is
  written ("two of your claims don't hold as stated, so I wrote what can be verified").

## 10. Check before this report is sent

1. The scripted gates for the deliverable ran on the final build, after the last edit.
2. Every changed unit was looked at as a render, and the whole as one sheet.
3. Every ledger line is ticked against something looked at, struck, or listed as not done.
4. Every number and quotation in the delivered text was found at its source.
5. No file the author has seen was overwritten; the delivery folder holds only current files.
6. No agent or background job is still running.
7. The report names what was not checked.

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| requests kept in memory | (a request dropped for a day, twice) | a ledger, ticked only after looking |
| one proofread and done | "run the agent again and again until 0 discrepancy is detected" | a fresh reader per round until a round finds nothing |
| a reader hunting machine-written prose | "do not fixate on AI [patterns] and focus on human psychology and reviewer psychology" | brief part D: only what a human reader would quote against the authors |
| the author as the last line of defense | "fan out many adversarial nitpicky subagent" | narrow auditors, one fault class each, before the author sees it |
| auditors that edit shared files | (clashing edits, a blocked report file) | edits returned as exact-match data, applied by one writer |
| 73 per-panel files for "source data" | "understand the context" | the example's type and count, staged by whitelist |
| a liked figure overwritten | "the previous one was so good, you killed it?" | a new name for every variant; backups before regenerating |
| six reply comments | "why do we have total of 5 instead of 4" | one comment per reviewer plus one general, counted by script |
| a dagger marking one exception | "clear AI slop flag" | the item put into the same family, or a plain reason |
| an excuse printed without checking | "why doesn't it have fold level scores?" | every exclusion verified in the records first |
| side deliverables nobody asked for | "why do you work on [that] response???" | exactly what was asked; ideas in one line |
| long reports with a glossary box | "unnecessary and total AI slop", "LESS IS MORE" | counts, top five, where the rest is |
| "done" with agents still running | "is that on purpose or is it stagnant" | a check that nothing is still open |

## Reference files

- `references/ledger.md`: the ledger format, reading notes, overrides, standing rules, recovery from a transcript.
- `references/proofread-loop.md`: the zero-defect loop, round briefs, what each round found, delivery mid-loop.
- `references/auditors.md`: auditor roles, the brief, the report and edit formats, vetting, recovery of dead agents.
- `references/handover.md`: matching the example, naming, staging, packaging, size limits, upload instructions.
- `references/checklist-figure.md`: the figure gate.
- `references/checklist-latex.md`: the paper and book build gate.
- `references/checklist-text.md`: replies, messages and prose.
- `references/checklist-slides.md`: the deck gate (detail in `talk-slides`).
- `references/checklist-web.md`: the web page gate (detail in `paper-website`).
- `references/checklist-data-deposit.md`: tables and data for a journal or an archive.
- `references/checklist-report.md`: shareable reports.
