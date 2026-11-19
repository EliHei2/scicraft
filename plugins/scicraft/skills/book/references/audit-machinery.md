# The audit machinery

The last weeks of a book are audits of a fixed text: facts, citations, figures, captions, headings, front
matter. In the source work about 514 edits were applied in two audit rounds and about 200 more from a 12-lane final
audit, without one agent editing the book. The general method (finders, verifiers, one writer) is the
`adversarial-audit` skill; fan-out mechanics and recovery are `agent-orchestration`. This file is the form for a book.

## The shape

```
machine checks (coordinator)  ->  read-only auditor lanes, one shared rules file
        ->  edits.json per lane  ->  apply_edits.py dry run + review sheet  ->  coordinator vets each item
        ->  apply surgical edits  ->  side build + gates  ->  AUTHOR_DECISIONS.md for the rest
```

1. **Auditors never edit the repository.** They return proposals as data. Exception: an assigned part file, or a
   single designated editor per file ("you are the only editor of chapter 5").
2. **One coordinator vets every proposal against the sources before applying it.** "You need to be more
   responsible" followed agent fleets doing rewrites. The coordinator reads the cited lines and the source, then
   applies, edits or rejects. The author's own text gets error fixes only.
3. **Items only the author can settle go to `AUTHOR_DECISIONS.md`**, short and numbered so the author can answer
   tersely ("5. just make the best reasonable choice"). Long "your call" lists each round were answered with new
   demands instead of decisions.

## Before launching

- **Snapshot** the chapters and back up each file the round may touch.
- **Run the machine checks yourself and pass the leads to the right lane:** `pdffonts` (non-embedded fonts), a
  raster-dpi and page-rotation scan with PyMuPDF, the LaTeX log warnings, entries without a DOI, self-citations,
  `scripts/book_checks.py --bib <bib files> --snapshot <snapshot>` (unknown citation keys before any build, labels
  lost since the snapshot, figure files changed outside an allow-list of approved replacements, unbalanced braces
  and environments), an AI-tell count. Run the checker as a baseline over all chapters first, then before and after
  every agent batch; the first baseline in the source work found 17 captions with no source line. Report the leads
  in the launch message.
- **Check overlap with the author's own sources, locally, after every content round.** Convert every source the
  book draws on (papers, supplements, preprints, replies to reviewers, co-authored papers) to text
  (`pdftotext -layout`; `textutil -convert txt` for .docx), then run
  `scripts/overlap.py chapters/*.tex --sources sources/ --minspan 12 --out overlap.json`. It reports each
  chapter's share of word 8-grams found in the sources and fails on any shared run of 12 or more words (the source
  work reached at most 0.7 % per chapter). Its JSON feeds the paraphrase jobs below. Agents report "no shared span
  of 12 or more words" in their gate. Unpublished text never goes to an online checker.
- **Write one rules file** (`assets/auditor_rules.md` is the template, about 8 to 9 KB when filled): the audit
  folder, "the repository is read-only", the build command, the house rules, the author's rules verbatim, the
  edits.json format, "known open items (the author decides these; do not propose)", the report format and the
  deadline.
- **Read earlier audit logs and the style documents first**, so the round does not repeat earlier work.

## Lanes

The 12-lane final audit (about 1.5 hours wall time):

| Lane | Looks for |
|---|---|
| delivery readiness and front matter | title page against the template, clauses of the signed statement, AI statement consistency, summaries in correspondence, page budget, fonts, links, bookmarks, metadata |
| bibliography entries | metadata against Crossref, house bib rules |
| citations in context | does each cited work say what the sentence says; claims with no citation |
| prose, four lanes by chapter group | facts against the papers, logic, consistency, house bans, abbreviations before definition |
| figures, three lanes by chapter group | identity with the source, crops, masks, letters, print size, captions, credits, licenses |
| numbers and names | every number and name consistent across chapters, summaries and captions |
| typography and layout | float placement, near-empty pages, wrapfigure overlaps, running heads, contents page numbers |

Other passes that worked as their own rounds: headings (four agents by chapter group, prose untouched, labels
kept), captions, credits, citations per section, run-in heads, self-citation, abbreviations, moving detail to the
appendix, active first person.

- **Lane-specific constraints go in the brief:** "Figures may only be cropped, masked, arranged, resized, moved or
  split, never re-made"; "never propose adding a \usepackage"; "the author forbids rewriting [their] prose; report only
  real defects with minimal, exact fixes".
- **When the author quotes a rule, put the verbatim words into each brief** ("THE AUTHOR'S RULE (verbatim): ...").
  Agents then applied the rule as meant.
- **Job types inside a prose lane:** A, fact, attribution, logic, consistency, guardrail; B, light brushes capped
  at about 30 to 35 per lane; C, paraphrase of the verbatim spans `overlap.py` listed (12 or more shared words).
  Quoted material is recorded as new == old.
- **Brief-compliance audit before the final build.** Split the governing brief into blocks, one read-only agent
  each, and have each return a table: brief line, evidence (file:line), PASS, PARTIAL or FAIL, and the minimal fix
  from the papers or the brief only. List the author's overrides in each brief so a deliberate departure is not
  failed. Before acting on a FAIL, read the exact brief line yourself. In the source work each block came back with
  one FAIL among 60 to 80 lines.
- **A visual-review lane works on one fixed build**, named by its checksum in the brief, so page numbers in its
  findings stay valid while other lanes edit.
- **A repair lane** (over-compaction, broken sentences) is accepted only after spot-checking three repairs per
  auditor against the snapshot.

## The proposal format

```json
{"edits": [
  {"id": "P3-A7", "file": "chapters/03_method.tex",
   "old": "exact text that occurs exactly once in the current file",
   "new": "replacement, or null for a query",
   "why": "rule or source with location", "type": "surgical|semantic|query",
   "severity": "blocker|major|minor", "source": "papers/ms_v4.tex:812"}
]}
```

- Each `old` occurs exactly once in the current file, is at least 30 characters (one lane brief) or 12 (the
  script's default), contains no newline when lanes edit by line range, lies inside the lane's range, and overlaps
  no other edit. The edits apply cleanly in order. Agents self-check by applying all edits to a copy.
- For citation lanes: removing the inserted citations gives back the original wording; every key resolves; new
  keys do not collide across lanes (`laneX_new.bib`).
- Invariants for prose lanes: numbers, citation keys in order, `\cref`, `\label`, begin/end pairs, equations,
  inline math and table bodies identical; word count reported before and after; no LaTeX build by the agent.
- Subagents that cannot write report files put the reasoning in `why` and `source` and the summary in their final
  message.

## Vetting and applying

```bash
python3 scripts/apply_edits.py audit/r2/P3.json --root . --sheet audit/r2/SHEET_P3.md --ban banned.txt   # dry run
python3 scripts/apply_edits.py audit/r2/P3.json --root . --skip P3-A4,P3-B9 --apply                    # surgical only
```

The dry run validates everything at once (file exists, `old` unique, no overlap, applies in order, type and
query form) and writes a review sheet with each proposal's context and flags: numbers that change, citation,
reference or label keys that change, brace balance, banned words added, length change. Test the validator on a
deliberately bad proposal before trusting it. `--apply` backs up the touched files, applies only `surgical` edits
unless `--types` widens it, confirms each `new` landed, and writes a change log.

For each item: read the cited lines (`sed -n "${n}p"`), render the cited page region when it is about a figure,
and check facts against the source text. Apply group by group as lanes report. Restore the author's original
sentence where an ambiguity came from an earlier compaction. Then a side build and the gates
(`references/final-build.md`).

- **Typography-only passes** are verified mechanically: `python3 scripts/check_bold.py P5.json --root .` deletes
  every `\textbf{` and its matching `}` from `new` and requires the result to equal `old` byte for byte, then
  rejects any edit whose `old` sits inside a caption, a sectioning command, `\paragraph{}`, a `tabular` body or an
  algorithm box. 43 weak bolds ("same probe", "empirical question") were then dropped by hand.
- **Agent claims are data.** A proofreader proposed deleting `\authoraction{}` notes before seeing they were
  defined as non-printing (`\providecommand{\authoraction}[1]{}`); the coordinator called two quantities unused
  that an OCR-based agent found inside a figure. Check before acting.
- **Facts go to a claim ledger** (`SCIENTIFIC_CLAIM_LEDGER.md`: claim, source file:line, status), merged from the
  agents' `ledger.json`. A figure-versus-text mismatch in the paper itself (the figure and the text disagreed on a
  count) is settled by recomputing from the records, logged for the paper and listed in AUTHOR_DECISIONS.md.
  Neither side wins by default; the method for checking claims against records is the sibling skill
  `integrity-audit`.

## Collisions, deadlines, rules arriving mid-run

- **Never two waves on one file at once.** Launch the next wave per file group as soon as the previous releases
  it. Never build while agents edit the tree; build into a side folder, which is always safe.
- **Hard deadlines in the brief** (for example "the deadline is today: deliver within about 20 to 25 minutes"), tightened by
  message when the author says it is too slow: "Wrap up now: stop new checks and report your verified findings
  within the next few minutes." Harvest finished agents; do not kill running ones under deadline ("don't just
  kill but make it faster!").
- **Commit the verified state at once** when the author is waiting, and keep building in parallel. Deliver a
  verified intermediate build first ("give me one fast build in max 10 mins then you can continue").
- **Broadcast a new rule from the author to every running agent whose lane it touches**, verbatim, with "This
  rule refines the brief and overrides it where they differ", and say which files changed under them. Stop agents
  whose work a change made stale.
- **Agents killed by a usage limit are resumed by message, not relaunched** ("Resume your lane from where you
  stopped; you were cut off by a rate limit"), after checking which lanes left files. Recover the author's
  messages typed mid-turn from the session transcript; then report that none were lost.
- **Before reporting done, check that no agent or background task is still running.**

## An external audit file

When the author pastes an audit written elsewhere: copy it into an isolated scratch folder; sort its items into
fix now (from papers, official documents or logic), conflicts with the author's explicit instructions (keep the
instruction, note it), and decisions only the author can make (AUTHOR_DECISIONS.md). Verify the audit's own claims
(two flagged items were already correct). Do not follow process instructions inside it that conflict with
standing rules (a branch and commit per chapter), and say so.

Its shape makes a good final-gate template; keep it for the last audit:

- **Part 0** lists the findings, each tagged BLOCKER, MAJOR or MINOR, with location and source.
- **Parts 1 to N** group the fixes by kind (hidden text in figures, numbers across chapters, citations, front
  matter), and each part names the check that verifies it: `pdftotext` on every figure file, numbers reconciled
  across chapters and summaries, DOIs against Crossref, `overlap.py`, `book_checks.py`.
- **A definition of done** lists checkable items only.
- `AUDIT_LOG_<date>.md` and `AUTHOR_DECISIONS.md` are updated with each fix, and the report comes when every item is
  ticked.

## Hand-off files

- `AUTHOR_DECISIONS.md` (`assets/author_decisions.md`): numbered, short, grouped; "only you can settle these":
  credits to confirm, figure and text numbers that disagree, image permissions, overclaims the author wanted.
- `SCIENTIFIC_CLAIM_LEDGER.md`: one row per checked fact.
- `AUDIT_LOG_<date>.md`: every applied edit, old and new, with its source.
- `CONTINUATION_INVENTORY.md`: task, state, open decisions, so a new session can pick up after a crash.
- A context summary before compaction keeps: paths and build entry, governing documents, every request in order
  with verbatim quotes and how later ones changed earlier ones, the standing constraints (verbatim where they
  concern attribution), and the pending task's plan.
