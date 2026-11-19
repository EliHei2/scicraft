# The workflow, step by step

Contents
1. Fact inventory
2. One home per fact
3. Draft
4. The dataset-by-analysis matrix
5. Humanizer pass
6. Self-review
7. Author-action markers, closed against the records
8. Splicing into the author's file
9. Fanning out a large supplement
10. Revising the author's own text
11. When the Methods live in a Word file
12. The report

## 1. Fact inventory

Before writing a word, extract every value, version, threshold, n, equation, citation and accession from the
source: the old draft, the Notes, the main text's Methods paragraph, and the run records.

```bash
python3 scripts/fact_inventory.py old_methods.tex old_notes.tex --out facts.tsv
```

The TSV has one row per fact with its file, line, section and sentence, and an empty `home` column. A restructure
that silently drops a number is the worst outcome of this work: in the author's supplement merge, the numeric diff
caught two facts that existed only in text that had been cut.

Add to the inventory, by hand, the facts that live only in the records: the values in the run configuration, the
software versions in the environment file, the commit of the code that produced the numbers. These are the
values the text must state (laws-and-firewall.md section 3).

## 2. One home per fact

Fill the `home` column, or write a short ownership table before drafting. Resolve every duplicated statement to one
owner.

| Content | Home | Any other section may only |
|---|---|---|
| notation, equations, the formal model | Methods, model sections | refer to the equation number |
| graph or architecture rules, dimensions, losses, decision thresholds | Methods | name the package call |
| code layout, entry points, file schemas, run artifacts, identifier glossary | Software implementation Note | refer to Methods for the algorithm |
| quality control and platform standardization | one Methods subsection | refer to it |
| per-dataset values | Datasets and preprocessing, and the matrix | state the delta |
| derivations, ablation rationale, robustness, relation to prior work | Supplementary Notes | refer to Methods |

`python3 scripts/fact_inventory.py draft.tex --homes` lists every non-trivial value that occurs in two or more
sections. Each is either a legitimate repeat (a value in a parameter table and the sentence that cites it) or a
second home to remove.

## 3. Draft

Apply the five laws (laws-and-firewall.md section 1) while writing, not afterwards.

- Start the Methods with a one-paragraph problem framing that states the task in one line and names no dataset.
- Decompose the algorithm into explicitly numbered steps when it has steps.
- Write one sentence that lists the settings a user can change ("The settings exposed to the user are the
  neighbor count, the graph radius and the similarity threshold."). Few settings is a strength worth stating.
- Each loss: name, one purpose clause, one equation. The total objective: one named weighted sum.
- Give every dataset a stable short ID at its first appearance and use only that ID afterwards.
- Write "we" for decisions, the passive for procedure.
- Draft each subsection in its own scratch file when the target document is long or is open in an editor
  (section 8).

## 4. The dataset-by-analysis matrix

When a dataset is reused across analyses with different references, subsets or settings, a reader cannot tell
the uses apart from prose. Give each dataset its ID, then build one row per (dataset, analysis) pair.

- Columns: dataset ID, analysis (by name), input and filters, configuration as a change from the default, and the
  two reference roles in separate columns. Role 1 labels or scores the outputs (cell typing, a metric reference,
  gold labels). Role 2 enters the model (a prior, an initialization, a pretraining corpus). Readers confuse the two
  roles more than anything else in a reuse-heavy supplement.
- Shared preprocessing is written once, above the matrix. The author's instruction: "summarize this before and
  not simply repeat for each dataset separately".
- Per-analysis prose states only the delta: "The generalization test reuses LUNG-A with the generic lung atlas as
  the typing reference and no prior; all other settings are as in the composition analysis."
- Every cell holds the value actually run, read from the run records. A cell the records cannot fill gets an
  author-action marker.
- Add a short Reference data subsection that lists each reference once with its version or collection ID, and the
  analyses that use it in each role.

In an ML paper the same device is a benchmark-by-analysis matrix: rows are (benchmark or task suite, analysis)
pairs such as main comparison, ablation and scaling study; columns are split and preprocessing, model and baseline
configuration, evaluation labels and metric (role 1), and any data that touches the model, such as pretraining or
tuning data (role 2). Suggested, not yet tested in real work.

The template is `assets/dataset-analysis-matrix.tex`. It needs `booktabs`, `longtable` and `array`. Keep the braces
around a first cell that starts with `[`, or LaTeX reads `\\[` as a length.

## 5. Humanizer pass

Restructuring and de-punctuating create new tells. Removing semicolons and colons welds the freed clauses back
together with `namely`, `rather than`, `so that` and `which is why`. In the author's supplement, after one such
pass, `namely` stood at 69 occurrences, `rather than` at 25 and `so that` at 15. So the pass is mandatory after any restructure or de-punctuation.

Use the `humanizer` skill and its technical register. Its density diagnostic, its adversarial-reader brief with
exact-once edits and its preservation diff do this job. Two things specific to a methods chapter:

- Read the whole document yourself for self-narration. Readers working on slices find clause welding and essay
  words well and miss self-narration almost entirely, because it only looks wrong across the whole chapter.
- A careful pass lengthens technical text by about 3 to 5 percent. If the text got shorter, it lost facts: run
  the check in step 6 before accepting it.

If the humanizer skill is not installed, apply laws-and-firewall.md sections 4 and 5 by hand and run step 6.

## 6. Self-review

Run the scripts, then read.

```bash
python3 scripts/fact_inventory.py old_methods.tex old_notes.tex --check new_supplement.tex
python3 scripts/methods_lint.py new_supplement.tex --datasets "<IDs>" --internal "<repo,package>" \
        --allow-code "<library prefixes>"
```

- `--check` must report no lost item. Each lost item is either restored, or listed in the report with where it
  went (a result moved to Results, a figure callout removed) or why it was wrong (a value the records contradict).
  Each new item needs a record behind it.
- `methods_lint.py` must report no ERROR. Read each WARN: a semicolon inside a quoted title passes, a semicolon in
  your prose does not.
- Then read for what scripts cannot see: a sentence with no fact, a caveat stated twice in different words, a
  choice justified that needed no justification, a surprising choice left unjustified, two names for one thing.
- **The regenerate-from-text test.** For a metric or a procedure the paper's numbers depend on, give a fresh agent
  only the Methods text (no code) and ask it to implement the procedure, then compare its output with the reported
  values. In the author's work, an implementation from the supplement alone reproduced [n] benchmark runs and also
  exposed three missing details: the cell floor as run, a weighting step, and the gene set behind a total. Write
  each gap as a sentence to add ("say X"), never as "the paper is wrong".
- Build the document: `pdflatex; bibtex; pdflatex; pdflatex`, then
  `grep -E 'Citation .* undefined|Reference .* undefined|multiply defined|^! ' main.log` must return nothing.
  Trim the bibliography file to cited entries if a malformed unused entry breaks bibtex.

## 7. Author-action markers, closed against the records

Anything you cannot verify (a value missing from the records, two sources that disagree, an accession nobody gave
you) becomes an inline marker, never a guess.

- In LaTeX use `assets/authoraction.tex`: `\authoraction{B01}{what is missing, with both sources and their
  locations}`. It prints as a red tag and disappears after `\showauthoractionsfalse`. In Markdown or Word use
  `FILL IN (B01): ...`. Keep a list of the same IDs in `AUTHOR_ACTIONS.md`. In a draft that co-authors read
  as prose (Word, a shared document, Markdown) the visible marker is always `FILL IN`: one author found
  `AUTHOR ACTION` tags in running text distracting and asked for "FILL IN, not AUTHOR ACTION". The ID stays in
  the marker so each one matches its line in `AUTHOR_ACTIONS.md`.
- Then **close each marker against the source of truth before handing over**: the repository at the branch and
  commit the paper names (fetch it; a local checkout may sit on another branch), the run logs and the recorded
  command lines, the run configuration written at launch, the raw data tables. Most markers close. The ones that
  survive are the real author decisions.
- Where defaults really come from: grep for the configuration file name in the code; if nothing loads it, read the
  signatures. Check the call site, which may pass a value that differs from the function default. Grep names
  built with f-strings by their parts.
- Do not "fix" a label when the fix would imply that dependent values are correct. Flag it instead.
- Never write a sentence the main text and the records do not support. One availability sentence written ahead of
  the records had to be reverted to a bracketed placeholder.
- For a caption or text the author must submit today, they asked for "no actions, find them": close every marker
  you can, and say which ones remain in one list at the top of the report.

`methods_lint.py --final` turns every open marker into an error, for the build that goes to the journal.

## 8. Splicing into the author's file

When the new section replaces part of a long file:

1. Back up the original and record its md5.
2. Draft the section in a scratch file and compile it inside a stub document: the original preamble minus packages
   that are missing locally, stub labels for references into the rest of the paper, and the new section only.
   `pdflatex -interaction=nonstopmode`, then grep the log for errors and `Overfull`. Wrap long file names in
   `\path{}` from the url package. Render the pages and look at them.
3. Before writing, confirm the target's md5 still equals the backup (nobody edited it meanwhile). Rebuild the file
   as the lines before the section, the new section, and the lines after it. Verify that the prefix and the suffix
   are byte-identical to the original.
4. Tell the author what was touched and that nothing else in the file changed.

When the author merges or reorders sections, split the file into heading-keyed blocks with a script and re-emit
them from an explicit ordered list. A hand-run merge once put `\end{document}` in the middle of the file and cut
off everything after it.

## 9. Fanning out a large supplement

For a supplement of many sections, give each section a drafter and a fact auditor, both working from the ground
truth (the old text, the records, the main text) and not from your rationale.

- Fact-check agents are read-only. Their brief says so ("do not modify, move or delete any file; small read-only
  inspection scripts are fine"). They return a table: claim, the text says, the records say, verdict, evidence path.
- Fold their results in as they return and re-confirm the largest corrections yourself.
- For a reviewer-grade audit of the finished supplement (fresh-context lanes, a skeptic per finding, a verdict),
  use the `integrity-audit` skill. Auditing is review: keep findings separate from fixes.

## 10. Revising the author's own text

When the author hands over text they have already worked on, the change is a minimal diff: keep their words and fix
only the facts they point to. The author's words: "keep the wording of the tex file as intact as possible". Show
the plan before any change wider than one sentence, write the revision as a copy unless told to overwrite, and do
not touch other files. When the author asks for the text, put it in the reply in full.

## 11. When the Methods live in a Word file

A co-authored manuscript in Word is edited in place at the XML level, never regenerated. A rebuild through
python-docx or pandoc gave blue headings, visible LaTeX alt-text and a bookmark on every heading. Copy the file,
edit only the text runs, keep styles, fonts and equation objects byte-identical, and write fresh `ZipInfo` entries
(reusing the reader's entries corrupted the checksums). Equations stay in the form the file already uses (in the source, PNGs with LaTeX alt text), byte for byte; never raw LaTeX in the text.
Citations stay as linked reference-manager fields; references to figures and Notes are bold.

- **Replace across run boundaries.** Word often splits one phrase over several `w:t` runs, so a plain search in
  one run misses it. Join the text of a paragraph's runs, replace, write the result into the first run and empty
  the others.
- **Pin heading colors to explicit black.** A heading whose color came from the theme rendered blue after the
  edit; the author asked for "no blue anywhere" except citation links.
- **Links on citations only, one link per citation**, with the hyperlink run style copied from a citation in the
  main text.
- **Check fonts in the XML.** A macOS Quick Look preview (`qlmanage -t`) renders page 1 only and ignores the
  document's default fonts, so it cannot confirm a font. Open the file in Word or read `w:rFonts` and
  `w:docDefaults` in the XML.

## 12. The report

Short enough to read on a phone, in this order:

- the files written, with paths, and what was checked (script results, the build) and what was not;
- the facts that moved and where (results sent to Results, tables moved to Supplementary Tables, identifiers moved
  to the software Note);
- every value changed to match the records, with the record it came from;
- the open author actions, one line each;
- what was not done, and why.

No praise of the text and no list of everything that is fine.
