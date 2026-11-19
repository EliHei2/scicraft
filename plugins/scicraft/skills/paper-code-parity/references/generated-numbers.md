# Numbers that cannot go stale

Every number in the prose, in a caption and in a table is generated from the result records, or asserted against
them, at build time. Hand-copied counts "drifted twice in two days" in the source projects; in a rebuttal, stale
ranks and scores came back from old drafts again and again until a build-time
check caught them. The scripts in `scripts/` are ported from those builds.

## Contents

1. The records
2. Macros for prose and captions (`gen_macros.py`)
3. Claims stated in words (`check_numbers.py --claims`)
4. The preflight (`check_numbers.py`)
5. Tables (`gen_table.py`)
6. Captions
7. Pending values and missing records
8. The build
9. Renames, retirements and cross-document agreement

## 1. The records

- One frozen folder of JSON records per paper (`data/` or `records/`), written by the analysis code, never by
  hand. Each record carries what produced it: the code commit, the resolved config, the seed list, the scoring
  protocol stamp. A table builder refuses records with mixed protocol stamps.
- Read a result only after its job finished cleanly (the source project read a result only after its job's
  "ends rc 0" line; interim records passed every validity check and were wrong).
- Each metric is computed once, in one module, into one master table. Every figure, table and sentence reads that
  table. "Numbers must match 1:1 across figures, tables, captions and text": a value shown in two places that
  differs in the last digit (91.40 beside 91.45) "reads as an error", so pull the master's canonical row, never a
  sweep run a local analysis happened to use.
- When the records change, the text follows. Never edit a record, or round in the favorable direction, to keep a
  sentence true. A result that contradicts a claim changes the claim.

## 2. Macros for prose and captions

`scripts/gen_macros.py` writes `tables/macros.tex`, one `\newcommand` per quoted number, from a JSON spec that
names the record file and the key path for each macro:

```bash
python3 scripts/gen_macros.py --spec macros_spec.json --out tables/macros.tex
```

The text then reads `a top-1 accuracy of \AccOurs{} over \NSeeds{} seeds`. Conventions carried over:

- Macro names are letters only (TeX control words): `AccOurs`, `DeltaMixup`, `NSeeds`. Spell digits out in names
  (`ZTenK`, `TwinThree`).
- House number format: fixed digits per macro, leading zero dropped below 1 (`.812`), true minus `$-$`, a signed
  delta as `$+$.011`. `--lead0` keeps the zero where the venue wants it. The format lives in one function (`num`)
  shared with the table script, so text and tables print a value identically.
- A percentage is its own macro with `"scale": 100`, never a second number typed beside the first.
- A non-numeric fact (the name of the strongest baseline) is a macro too (`"text": true`), so a change in the
  records changes the sentence.
- The macros file is generated whole and sorted, with a header line saying not to edit it. Nothing else writes it.

## 3. Claims stated in words

Some numbers are not printed as digits but are still claims: "ranks first", "in 5 of 7 tasks", "the gap is
within seed noise", a rank in a list. Put each in `claims.json` with the record path, the stated value, a
tolerance where the value is continuous, and where it appears:

```json
{"file": "records/main.json", "path": "methods.ours.rank", "want": 1, "where": "sec. 5: 'ranks first'"}
```

This is the generalized form of the rebuttal's `check_text.py`, whose purpose line was "the numbers the prose
states, checked against the records, so a refit cannot leave a stale sentence behind". Every number added to the
text gets either a macro or an assert, in the same edit.

## 4. The preflight

`scripts/check_numbers.py` runs inside the build, before LaTeX, and exits 1 on any problem:

```bash
python3 scripts/check_numbers.py --spec macros_spec.json --macros tables/macros.tex \
    --claims claims.json --tex paper.tex sections/*.tex
```

| Check | Fails when |
|---|---|
| stale macros | a record moved since the macros were generated, a macro was added to or removed from the spec, or the macros file was edited by hand |
| claims | a claim's record is missing, or its value is outside the tolerance |
| TeX scan | the text uses a results macro that the macros file does not define (names from the spec, or `--expect-prefix`) |
| TeX scan, warning | a macro still reads `pending`; a literal decimal or percentage stands in the prose (`--fail-on-pending`, `--fail-on-literal` make these failures) |

The literal-number scan is a heuristic. It skips comments, inline math and equation and table environments, and
reports the rest with file and line. Before submission, run it with `--fail-on-literal` and either convert each hit
into a macro or list it as a fixed fact (a year, a dataset size quoted from its source) with `--allow-literal`.
(The literal scan is suggested, not yet tested in real work; the stale and claims checks are ported from builds
that ran for weeks.)

A number that cannot be generated yet (it lives in a co-author's spreadsheet, it comes from a paper you cite)
carries `[VERIFY]` in the source until it has a record or a cited source; the preflight lists every `[VERIFY]`.

## 5. Tables

`scripts/gen_table.py` writes each results table from the records as a LaTeX fragment and a sidecar JSON:

```bash
python3 scripts/gen_table.py --spec table_main.json --out tables/tab_main.tex
```

- **Fragments are self-terminating.** The fragment holds the body rows and ends with `\bottomrule`; the main
  file holds `\begin{tabular}`, `\toprule`, the column heads, `\midrule`, `\input{...}` and `\end{tabular}`. TeX
  Live 2025 raises "Misplaced \noalign" when `\bottomrule` follows an `\input`-ed row in the main file, and the
  same error comes from a fragment that opens with `\toprule` or `\rowcolor` (both reproduced while building this
  skill, pdfTeX 1.40.27).
- **Bold or shading for the best value follows one rule for every column** (`"best": "max"` or `"min"`), and the
  values stay printed. Emphasis never depends on which method wins.
- **A missing cell reads `pending`**, never a blank that looks like zero and never an estimate. A comparator's
  published cell is frozen as published and never re-scored; the table builder re-reads it from its record.
- **One table definition, several renderings**: the sidecar JSON feeds a docx or a website from the same values.
- Tables for one claim come from one script per table (`tab_<name>.py` or one spec per table), and the build runs
  all of them.

## 6. Captions

A caption is prose and follows section 2: every number in it is a macro. The rebuttal book's rule was "captions
read every number from `tables/macros.tex`, which is regenerated from the frozen data". A caption also states what
the reader needs to read the values: the interval type (IQR or CI), the number of seeds or folds, every filter or
subset the analysis applied, and every setting that differs from the default. Panel scripts assert the invariants
of what they draw (`assert row["label"].startswith("necessity")`, `assert lo * hi > 0` for an interval said to
exclude zero), so a figure cannot silently disagree with its caption.

## 7. Pending values and missing records

- A macro whose record does not exist yet prints `pending` in the PDF and appears in the preflight's warnings.
  When the record lands, the next build fills it with no code change. If a number exists nowhere, write
  `[PENDING: what]`. Never invent or estimate one.
- `gen_macros.py --strict` fails instead, for the final build.
- Results that run against the narrative stay in the document, labeled, with their numbers. A reporting rule
  (which runs count, which p values print) applies to every result alike and is stated in the text.

## 8. The build

One command rebuilds every number, table, figure and the PDF from the frozen records, re-scoring nothing. Order:

1. (optional, explicit flag) refit or re-aggregate the records;
2. figure panels, then composed figures;
3. `gen_macros.py`, every `gen_table.py`;
4. `check_numbers.py` (fails the build);
5. `pdflatex` twice (three times with `bibtex`);
6. grep the LaTeX log for `undefined`, `Misplaced` and `multiply` and fail on a hit, because a gate reads the
   log, never only the exit code (a build once exited 0 with a bibliography-less PDF);
7. other renderings (docx, website) from the same sidecar JSON;
8. print the page count.

`assets/example/build.sh` is a runnable version on the toy records. A `SKIP_FIGS=1` switch that rebuilds text and
tables only keeps the loop fast while editing prose.

## 9. Renames, retirements and cross-document agreement

- **A rename is a pure label change, verified by a numeric diff**: after renaming a metric or a method across
  every figure, table and sentence, diff the values before and after; nothing may move.
- **Retired forms and numbers are written down with the reason**, so no agent brings them back.
- **Before delivery, diff every number in captions and manuscript against the master table.** Treat any mismatch
  as a bug and find where it comes from.
- **When a result changes direction between versions, stop and reconcile**: diff the two pipelines (normalization,
  filters, test) and name the change that flipped the sign before using either result.
- **Source-data files** for the journal are rebuilt by a script from the inputs the published figure read, and
  checked against the counts the figure itself wrote.
