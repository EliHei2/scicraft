# Manuscript against data

Checks behind SKILL.md sections 1, 8 and 9.

## 1. The number inventory

```bash
python3 scripts/extract_numbers.py main.tex supplement.tex > numbers.tsv
python3 scripts/extract_numbers.py main.tex --kinds value,percent --format md > numbers.md
python3 scripts/extract_numbers.py README.md --words          # also "five seeds", "twice", "half"
```

Each row has an ID, file, line, kind, token, value, unit and the full sentence, plus empty `source` and `verdict`
columns to fill. Kinds: `value`, `percent`, `reference` (a figure, table, section or equation number), `year`
(in a citation), `year?` (a four-digit number that may be a year), `word`. In TeX the preamble, comments and the
keys of `\label`, `\ref`, `\cite`, `\url`, `\includegraphics` and `\authoraction` are skipped; in Markdown code
blocks, inline code and link targets are skipped. Table rows and headings end a sentence.

Fill `source` with the file and line of the record (master table row, log line, code at a commit) and `verdict`
with the class from SKILL.md section 4. A number with no record is a finding: "no record".

## 2. One authority per number

- **The master table is canonical.** Each metric is computed once, in one module, into one table; figures read
  from it. For any metric that also appears in the master table, a local analysis pulls the master's canonical
  row (the default run), never whatever sweep run it used. Readers cross-check main figures against the
  supplement, and two values that differ in the second decimal read as an error. State plainly when the rest of a
  panel uses a different run.
- **One run and one setting across a report.** One audit found the same method was a different run in different
  figures, so one ratio disagreed between panels; some panels labeled with the paper's metric had been computed at
  another floor. Fix: one config module imported by every panel script; a caption line names the run when the
  paper's own run is not available.
- **An authority order between sources**: the latest manuscript wins on any number, the supplement on procedure.
  Keep a retired-numbers list ("delete on sight") and grep the documents for it at every intake.
- **Generate numbers into the text.** A block written by a script, and a preflight that fails when the block is
  stale. Every number not generated carries `[VERIFY]`. The rule exists because hand-copied counts drifted twice
  in two days. A results page or website gets the same check: its build fails when a number on it is no longer the
  paper's.
- **A registry of canonical runs** (`RUNS.md` or a provenance table): dataset, run path, code commit, repository.
  Ask "which version is this?" before computing; never pick a run by guessing.

## 3. Completeness

Before any comparison figure, a method by dataset table with a status per cell:

| status | meaning |
|---|---|
| done | completed on the full input; value from the master table |
| OOM, TIMEOUT | failed; drawn as a failure mark, never as a value |
| SUBSET | ran on part of the input; counts as not run |
| NOT_ATTEMPTED | never launched |
| missing | the value exists somewhere; the deliverable is a fetch list (paths, log names, commands) |

Parity: if a value is unrecoverable for one method, drop that dataset for every method so all cover the same set.
A gap is reported in text and filled only with a measured value of the same scored run (and the caption names the
instrument). No imputed or estimated value is drawn, not even as a hollow mark.

## 4. What the figure really shows

For every figure and table cited in the text:

- The plotted quantity is what the label says (a figure labeled "% cells" plotted % transcripts).
- The caption names the exact statistic and n. A separation count was labeled with the wrong test once; Kendall's
  τ was reported where the computation was Spearman on 3 to 4 methods.
- The figure, its caption and the text use the same run and the same number. Recompute the caption's numbers from
  the figure's source table.
- Fold changes are not compared across metrics with different floors.
- "Equals" means equal; give the gap when there is one.

## 5. The text alone regenerates the numbers

"From the supplementary, it should be reproducible. That's the point."

1. Extract every sentence about the metric or procedure from the main text and the supplement.
2. Give them, and only them, to an agent that has not seen the code. It implements from the text.
3. Diff its outputs against the published values.
4. Write each gap as a sentence to add ("state the floor as run", "say the mean is weighted by X", "name the
   feature set behind the totals"), never as "the paper is wrong".

One such reimplementation reproduced [n] benchmark runs and exposed three missing details: the floor as run, a
weighted-mean step, and the feature set behind the unit totals.

## 6. Claim scope

For each summary sentence, name the datasets, conditions and baseline it covers. Overclaims caught this way:

| As written | As supported |
|---|---|
| returns no score on these data | returns no score on the three datasets it was run on |
| a fivefold rise | a fivefold rise in the excess over 1 |
| clean units score 0 | clean units score near zero (give the range) |
| follows the error more closely | the rise is larger; the ordering is not preserved when dirtier units are sparser |
| all units, all datasets | the datasets actually checked |
| first GNN for the task | what a referee would accept, after checking prior work |

Classify each claim the author wants: **TRUE**; **NARROWER**, with the wording that holds; **FALSE**, dropped. Put
the allowed wording in the brief of every later writer so rewrites keep it.

## 7. The safety net after any rewrite

A merge, restructure, de-slop or humanizer pass can drop a fact without anyone noticing.

```bash
cp paper.tex backup/paper_pre_<pass>.tex
# ... the pass ...
python3 scripts/extract_numbers.py --diff backup/paper_pre_<pass>.tex paper.tex    # exit 1 if a token was lost
diff <(grep -o '\\label{[^}]*}' backup/paper_pre_<pass>.tex | sort) <(grep -o '\\label{[^}]*}' paper.tex | sort)
diff <(grep -o '\\cite[a-z]*{[^}]*}' backup/paper_pre_<pass>.tex | sort) <(grep -o '\\cite[a-z]*{[^}]*}' paper.tex | sort)
grep -c '\\begin{equation' backup/paper_pre_<pass>.tex paper.tex
```

`--diff` uses the multiset `Counter(re.findall(r'\d+(?:\.\d+)?', text))` of the procedure it came from. In one
merge it caught two facts that lived only in dropped text. A collaborator's returned version was adopted only after
the same diff: no label or citation lost, 18 of 18 equations, the numeric multiset within 3 small integers. A
humanizer pass usually lengthens text by 3% to 5%; if it got shorter, it deleted facts.

Table checks: slice at `\label{tab:X}`, not at `tab:X`, and match both math delimiters (`$...$` and `\(...\)`).
Delimiter style alone produced 16 false alarms in one run.

Build: `pdflatex && bibtex && pdflatex && pdflatex`; zero undefined references or citations, zero duplicate labels.
`grep -E 'Citation .* undefined|Reference .* undefined|^! ' main.log` returns nothing.

## 8. Author actions

- In TeX: `\input{authoraction}` (from `assets/authoraction.tex`) in the preamble, then
  `\authoraction{B07}{text says X at line N; the launch log says Y}`. Drafts show a red tag; `\showauthoractionsfalse`
  hides every note. Keep the existing macro if the document has one.
- In Markdown or docx: `FILL IN (B07): ...`, or a non-printing `% AUTHOR ACTION` comment.
- `AUTHOR_ACTIONS.md`: one row per ID with the quote, the location, both sources, the options, and the status.
  Group items "only you can settle" (credits, number mismatches between figure and text, permissions).
- For citations, match the main text's string and list the mismatches.
- Close each flag against the record when possible. Delete a note when the records answer it.

## 9. Fact-checking a section in place

When the author asks for the facts in one section to be fixed:

1. Convert inputs without executing them (`pandoc X.docx -t plain --wrap=none`; scripts that read downloads run
   under `python3 -I`).
2. Map the structure (`grep -n '\\section\|\\subsection\|\\paragraph'`) and find the target line range.
3. Diff later drafts if any; use them as leads only.
4. Identify the exact code (section 2 of `tracing.md`) and read the CLI for the arguments actually passed.
5. Fan out read-only fact-check agents by area. Brief: "READ-ONLY: do not modify, move or delete any file; do not
   run heavy compute; small read-only inspection scripts are fine." They return a table: claim, text says, records
   say, verdict, evidence path; plus open questions.
6. Draft the corrected section in scratch from the verified code while they run; fold results in as they return;
   re-confirm the biggest ones yourself (for example, grep a setting across all run logs).
7. Check citation keys against the `.bib`.
8. Compile a stub document (the original preamble, stub labels for external references, the new section) when the
   whole document cannot build; grep the log for errors and overfull boxes; render the pages and look.
9. Splice in place: record the original's md5; rebuild the file as lines before, new section, lines after; before
   overwriting, confirm the md5 is unchanged (no concurrent edit); after writing, verify prefix and suffix are byte
   identical.
10. Mark open decisions with author actions; delete notes the records now answer.
11. Final message: what was touched ("nothing else in the file was changed"), corrected facts by area, conflicts
    with the author's instructions first, mismatches found outside scope.

When the author asks "tell me first, don't edit yet", the deliverable is the claim table; editing waits.
