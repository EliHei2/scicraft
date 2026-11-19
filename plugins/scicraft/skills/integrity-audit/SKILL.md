---
name: integrity-audit
description: Checks that what a manuscript, figure, report or release says matches the code, the run records and the data, and delivers a claim ledger, author actions and, when asked, a plain integrity-defense report. Use it whenever a number must be traced or defended, even unnamed: before submission or camera-ready, when someone says "the numbers don't match", "I can't reproduce Table 2", "is this the code that made the figures", "check the Methods against the code", "verify the data links" or "check all references", and when reproducing published results. Holds what agents get wrong: tracing to the released commit, real defaults and call sites; recomputing with the exact pipeline; tolerance and mismatch classes; recovering lost code from bytecode; byte-exact data checks over HTTP ranges; a reference audit; a fresh-context audit protocol. Prefer paper-code-parity to keep a release in step with a paper, adversarial-audit to attack an argument, stats-reporting for how to report a test.
---

# integrity-audit

How to check that every number and factual claim in a document is what the code, the run records and the data
say, and how to report the result so the author can act on it. Distilled from a year of one researcher's work on a
benchmark paper and a book: a Methods fact-check against code that had moved on, the recovery of a benchmark
metric that survived only as compiled bytecode, a byte-exact data-availability check, a 278-entry reference
audit, and the defense of a benchmark metric against questions. The author's
standard for that defense was "no faking, no over-claiming. see if it's actually true".

> **PRIME DIRECTIVE: check every claim against the artefact that produced it (the released code at a named
> commit, the run's own command line and log, the data file opened and read), and when two sources disagree, put
> the disagreement in front of the author with both quotes and locations. Never pick one silently.**

Three failures cost the most time. Guard against them from the first minute:

1. **Trusting a stand-in for the record.** A config example the code never loads, the project's own notes, a
   folder called `full/`, a log that says "All done!", a function default the caller overrides, a collaborator's
   draft. Each one let a false claim or a false data point through; the config example alone kept two false
   author actions alive for several audit passes (section 2).
2. **Reimplementing instead of re-running.** A rewrite of a metric "from the description" differs in one
   definition (the filter's field, the gene or feature universe) and moves the value far enough to fake a
   mismatch, or hide one (section 3).
3. **Choosing the wording for the author.** Calling a run setting a "discrepancy" made honest work read as
   misconduct; writing the text "as if default" when the records show otherwise is misreporting. Both are fixed
   the same way: state the value actually run, where the result is reported, and flag what disagrees (section 9).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The document and its version**: the exact file that will be submitted or was questioned (TeX, docx, Markdown,
  HTML), plus the main text if the target is a supplement. Record its md5; audits of a moving file go wrong.
- **The released code**: repository, branch and commit that produced the numbers. The local checkout is often an
  integration branch. Fetch the release: `git fetch origin <branch> --depth=1`, then `git ls-remote origin` before
  stating any head.
- **The run records**: launch scripts, recorded command lines, scheduler logs, the results table every figure
  reads (the master table), run maps, per-figure provenance notes.
- **The data**: local bundles, public accessions, reference objects.
- **The question**: which claim was challenged, by whom, in what words. Copy the challenge document into a scratch
  folder and convert it without executing anything (`pandoc -t markdown --wrap=none in.docx -o in.md
  --extract-media=media`).
- **The mandate**: report only, or edit the document? Edits to co-authored files go through the author.

Work in a folder of its own beside the project, never in the paper's repository:

```
audit_<topic>/
├── numbers.tsv          every number with its sentence (scripts/extract_numbers.py)
├── CLAIM_LEDGER.tsv     one row per claim: quote, location, records, class, verdict (assets/claim_ledger.tsv)
├── AUTHOR_ACTIONS.md    every disagreement the author must settle, with IDs B01, B02, ...
├── EXACTNESS.md         per figure or table: exact, printed precision, differs (and why), not reproducible
├── repro/               the wrapper that calls the original functions, and its outputs
└── report/              only if a report was asked for (section 11)
```

## 1. Inventory the claims

- **Extract every number with its sentence before reading for meaning.** `extract_numbers.py paper.tex supp.tex >
  numbers.tsv` gives file, line, kind (value, percent, reference, year), token, value, unit and the sentence. Add
  `--words` to catch "five seeds" and "twice as fast". Human reading skips numbers that look familiar.
- **Add the factual claims that carry no number**: what initializes the model, which reference trained what,
  which version of a competitor ran, what an algorithm is called, what a dataset is.
- **One row per claim in the ledger**, with the verbatim quote and its location. A claim without both cannot be
  re-checked by anyone, so it is not an audit finding.
- **Map the supplement as the authority on procedure.** Main-text Methods are often a condensed copy of it. In
  the author's words: "From the supplementary, it should be reproducible. That's the point."

## 2. Trace each number to the code and run that produced it

The procedure, with commands, is in `references/tracing.md`. The rules:

- **Read the released code, never the project notes about it.** A manuscript claimed a component was
  pretrained; the project's own top-level notes carried the same claim; the code trained it from random weights. The author's reaction: "serious red flag".
- **Find where defaults really come from.** Grep for the config file's name in the code. If nothing loads it, it is
  an example, and the defaults are in the signatures (one CLI built them by parsing class signatures). Trusting the
  example kept two false author actions alive through several passes.
- **Read the call site, not the function default.** A caller passing `max_iter=250` to a function whose default
  is 100 runs 250. The value run is the value the caller passed.
- **Grep f-string names by their parts.** A literal grep for `col_scores` misses `f"{col}_scores"`.
- **Confirm the command from the logs.** The run's recorded command line, or the harness record, says what ran;
  then check it against the scored output.
- **A metric's name means the computation that produced the published figures.** Not the function default, not
  the branch tip. "Whatever went into the paper figures is" that metric.
- **Name branch, commit and date in every claim about code.** "Wait new GitHub or old GitHub? Which one?" came
  when the public code changed on the day of the audit. Use a table with one column per state (old head, new head,
  side branch) and rows for function identity, CLI defaults and date made public.
- **Per-dataset settings in a Methods section are the likeliest stale items.** Check each against the figure's own
  provenance note and its run ID.
- **"Which of two numbers is correct?" is answered from the code, with file:line.** When both values exist in the
  code for different panels (a legend said one radius, the text another, and each panel used one), give a table
  (value, used by, file:line) and ask one question: which panel is meant. Once answered, reply in one line. When a
  caption's parameter is in doubt, recompute the plotted quantity at both candidate values; the one that
  reproduces the plot is the one used (the two radii gave counts about twofold apart, so the plot settled it).

## 3. Recompute with the exact pipeline

- **Wrap the original functions; never reimplement them.** One `repro_metrics.py` imports the code at the run's
  commit and writes the definition beside it (floor, feature universe, label source). A filter applied to the full
  field instead of the method's own subset inflated recall, worst for low-coverage methods. A wrong reference set
  moved a metric from the middle of its range to near its ceiling.
- **The first output of any new evaluation script is a known number.** Reproduce the published baseline exactly
  before the script decides anything.
- **Probe definitions until the digits match, then record which one matched.** A floor of one value reproduced a
  heatmap "to every digit"; the other value reproduced an older aggregate. A figure with no code was rebuilt by
  probing per-unit mean against pooled, label source and floor, to three or four decimals. When nothing matches,
  write "not reproducible" in the exactness ledger.
- **A run counts only if it covered the full input.** Prove it from the output's extent, never from the folder
  name, a log line or a coverage figure: a `full/` run that logged "All done!" was a crop. For spatial data, more
  than 20% empty tissue bins on a 100 µm grid marks a subset. For a model, count the evaluation rows actually
  scored against the split size. A subset run is "not run".
- **Never publish a statistic on partial data without saying so.** A correlation reported from 3 of 5 methods
  changed once all 5 were in; the correction was announced plainly. Scripts refuse incomplete inputs unless a flag
  writes to a prototype folder.
- **Check plausibility before showing a value.** Identical values across methods, proportions that do not sum to
  1, a score outside its range, mirrored patterns: a bug until shown otherwise.
- **A join key is defined once, before any filter, and asserted exactly.** A row index assigned after filtering on
  one side and before it on the other joined 0.065% of rows correctly and raised no error; a guard that accepted
  0.9 of the expected count let a 0.25% offset through. Assert an exact invariant (rows pointing at discarded
  records = 0), and give test data interleaved rows that a filter removes.
- **When a result flips between versions, stop and reconcile.** Diff the two pipelines and name the change that
  flipped it before using either.

## 4. Tolerance and mismatch classes

| Class | Test | What to write |
|---|---|---|
| exact | relative error ≤ 1e-12 (note bit-exact separately) | "reproduced" |
| printed precision | equal at the digits printed | "reproduced to the printed precision" |
| setting | same code and data, a run setting the text does not state | the setting as run, and the sentence to add |
| code | the numbers came from other code than the text or release describes | recover the code (section 5), then rewrite the text |
| data | other input than stated (a filter, a version, a subset) | the input as run; a rerun is the author's call |
| not reproducible | no definition matches | "not reproducible", with what was tried |

Keep the exactness ledger per figure. A residual gap of a fraction of a percent after the mechanism is understood
is listed and left: the author was "frustrated by over-iteration" on a 0.4% typing difference. Ship with the open
items named.

## 5. Recover lost code, and release exactly that code

When the published numbers came from code that has since changed, recover the original before describing or
rerunning anything (`references/tracing.md` has the commands).

- **Bytecode is a record.** A benchmark's real metric code survived only as a cached `.pyc` behind a 20-line shim.
  Copy it first: importing the live package under the matching Python recompiles the shim and overwrites the only
  copy. Load the copy with `importlib.machinery.SourcelessFileLoader`, find the source in git history, strip later
  additions, and verify zero differences in `co_code`, constants and line tables for every code object.
- **Release byte for byte, nothing new.** "exact metric, no new stuff". Gate: zero bytecode differences, tests
  pass, the remote tip unchanged since the fetch, fast-forward only, then download the file back and verify again.
  Anything more (porting a loader the CLI needs) is a separate decision for the author.
- **Run the public entry point end to end.** Function identity alone was certified once; a reviewer agent found
  the branch's data loader could not run the CLI. Disclose the rerun recipe.

## 6. Provenance by opening the artifact

- **Open the file; never match names.** A caption credited two public atlases for a reference; its gene count gave
  away the real source. Species follows from symbol case (all uppercase is human). For a model: open the
  checkpoint's stored config and the dataset's hash, not the run folder's name.
- **Get to the primary source before naming or citing an algorithm.** Compare constants line by line with the
  original code, read every version's changelog (a "similar" note applied to one version only), check what the
  library name means (a library's `concave_hull` is a different algorithm from the one the text named), and write
  "adapted from" when constants differ.
- **Reimplementations are labeled as such.** "our implementation of the recipe in paper X" and "the authors'
  package, run as coded" are two names, in the definition, every caption and every row label. Never "exact" when
  the paper leaves settings open; list the settings chosen.
- **Quote from the downloaded text, never from memory.** `python3 scripts/kwic.py "<phrase>" paper.txt` prints
  each hit with 80 characters either side, file and offset; copy the quote from that output. One word of a
  first-draft quote was wrong. For a docx, `python3 -I scripts/docx_paras.py copy.docx > paras.tsv` gives one row
  per paragraph and per comment (reviewer comments name the claim as often as the text does).
- **Check a dataset descriptor that stands out against the provider's own page** (a density, an area or a count
  far from its siblings) before it goes into a table. Record the URL beside the value; a descriptor that cannot be
  verified is marked so, never estimated.

`references/provenance-and-data.md` has both procedures.

## 7. Data availability and references

- **Match bytes, never tissue, technology or task names.** Fetch one small member of the multi-GB public ZIP with
  HTTP range requests and diff it against the local bundle:
  `python3 scripts/remote_zip.py <url> <member> --compare <local file>` (exit 1 on any difference or missing
  member). It catches mislabeled samples, dead links, release folders whose files were never uploaded, and
  references cited under the wrong source.
- **curl every link live** and give plain URLs. Object stores are case-sensitive; a capital letter gave a 404.
- **Reference audit, one verdict per entry and per citing sentence.** Entry: OK, FIX (bib only), REPLACE_IN_TEXT,
  QUERY. Citation context: FIT, WEAK, WRONG, SELF. Pre-compare every DOI with Crossref; read the full text when a
  number is cited. One audit corrected 137 of 278 entries, including "up to 40%" that the paper gives as an average
  of 39% (4% to 84%). Unpublished own work is never cited as evidence.

## 8. Manuscript against data

`references/manuscript-checks.md` has the checks and scripts. The rules:

- **One authority per number.** The master results table is canonical; every figure reads from it. A number in
  two places is identical in both. Keep a retired-numbers list and grep for it at each intake.
- **Never type a corpus number by hand.** Generate it into the text and fail the build when the block is stale;
  mark anything not generated `[VERIFY]`. Hand-copied counts drifted twice in two days.
- **Every method by dataset cell is filled or explained** (done, OOM, timeout, subset = not run, missing). If a
  value is unrecoverable for one method, drop that dataset for every method.
- **Check what the plotted quantity is.** A figure said "% cells" and plotted % transcripts. Every caption names
  the exact statistic and n; Kendall's τ was once reported for a Spearman computation.
- **The text alone must regenerate the numbers.** Give an agent that has not seen the code only the supplement's
  sentences, have it implement, and diff against the published values. Each gap becomes a sentence to add.
- **Narrow each claim to what was tested.** For every summary sentence name the datasets, conditions and baseline
  it covers. Classify each claim the author wants as TRUE, NARROWER (give the wording) or FALSE (drop it).
- **After any rewrite, diff the numbers.** `extract_numbers.py --diff old.tex new.tex` lists every numeric token
  lost or gained (exit 1 on a loss); also diff `\label`, `\cite` and the equation count. This caught two facts
  that lived only in dropped text.

## 9. Flag disagreements as author actions

- **Write the disagreement where it stands and in the log.** `\authoraction{B07}{text says X (line); launch log
  says Y (file)}` from `assets/authoraction.tex` prints a red tag in drafts and nothing after
  `\showauthoractionsfalse`. In Markdown or docx use `FILL IN (B07): ...`. Every ID has a row in
  `AUTHOR_ACTIONS.md`.
- **A figure and the text that disagree: neither side wins by default.** Recompute the value from the records; the
  value the records support goes in, the mismatch is logged for the paper, and the choice is listed in
  `AUTHOR_ACTIONS.md` (or the project's `AUTHOR_DECISIONS.md`) so it is never made silently. In one book a
  heatmap and its text disagreed on a count; the text's value was kept and the author was asked.
- **Close a flag against the record when you can.** A flag that the records answer is a fix, not a question.
- **Do not fix a label in a way that implies the numbers built on it are fine.** A dataset's wrong species was
  flagged, not relabeled, because the analyses typed it against the wrong reference.
- **State the value actually run where the result is reported.** Write "every metric used at least N records per
  unit", from the run config, once. Never "N vs M": the author rejected that framing because it read as a
  discrepancy and made sound work look bad. Never omit the value either: a setting that differs from the default is reported with the result.
- **Wording may simplify; the records must still support it.** When an instruction asks for text the records
  contradict (a run described as default when it was not, a procedure described differently from what the
  logs show), do not write it. Say so first, with the evidence (job ID, config line), and offer the two
  honest options: rerun as described, or describe what ran.
- **Do not write sentences the main text does not support.** An auditor once drafted a data-availability sentence
  of its own; it was reverted to bracketed placeholders, then real accessions were found.

## 10. The audit protocol

For a large document or a high-stakes claim. `references/audit-protocol.md` has the splits, the kinds of finding,
the hand-back format and the briefs.

- **Fresh-context auditors get only the ground truth**: the document, the code at the run's commit, the records,
  the version before any rewrite. Never notes on why the text says what it says.
- **Split by what the document needs**: by area, by lane (self-consistency, agreement with the main text, code
  grounding, duplicates; about 15 agents for one supplement), by lens, by persona, by chunk.
- **Auditors propose; one writer edits.** "You audit and propose. You do NOT edit any [project] file."
- **A finding is a quote plus a location.** Without both it is dropped.
- **Each finding is marked `check` or `judgment`.** Check when a grep hit, value diff or count anchors it; judgment when
  it is a judgment.
- **A skeptic tries to knock down each finding** that would change a number, claim or citation. Four findings read
  from the wrong code tree fell this way.
- **Verdict words**: the author's `TRUE`, `NARROWER`, `FALSE` per claim, `OK`, `FIX`, `DECIDE` per figure and the
  reference verdicts of section 7; this package adds `blocker`, `fix`, `polish` per finding and, on the next
  round, `resolved` or `unresolved` per earlier finding, with new findings listed apart.
- **Edits travel as old and new text**, each old string unique in a pinned version (md5), checked by script.
- **Check every agent finding before applying it.** List the rejected ones with the reason.

## 11. The integrity-defense report

When someone questions a metric or a result and the author must answer. `references/defence-report.md` has the
analyses and the form.

- **Answer the exact question asked**, restated at the top, with "no reported value changes" where true.
- **Test on known ground truth.** Inject known error into real data at graded doses (0.5% to 30%), build
  fully synthetic cases that are clean by construction, and compare removing the true errors against removing
  random units at the same count. Report the weakness the test finds.
- **Rankings on the real outputs**, with and without the contested threshold, across datasets and alternative
  metrics. Never as rank changes under synthetic perturbation.
- **Plain wording.** Keep every number and every concession; drop loaded verbs (`inflated`, `overstated`,
  `misreported`, `misspecified`, `conflated`, `hacky`). Corrections read "state more clearly". A draft that led
  with "what's wrong" read as "seems like I did a hacking".
- **Every concession carries its number**, as every defense does. A cold reader called one draft "a defence brief"
  because only the defenses had numbers.
- **Do not claim more than holds.** "don't push it. If they're actually very good, show that they're good."
- **Audit the implementation before the defense ships.** One fresh, read-only agent gets the scoring code at the
  run's commit and checks label mappings, reference mappings and joins. One such audit found a real mapping bug;
  it was fixed, the metric rescored and the change disclosed in the report.

## 12. Check before anything is handed over

In this order:

1. `extract_numbers.py` on the final file: every row of the output has a source and a verdict in the ledger, or
   is a reference, year or citation key.
2. `extract_numbers.py --diff` between the version received and the version returned: zero tokens lost that the
   ledger does not explain.
3. `remote_zip.py --compare` for every public bundle named: exit 0, md5 recorded in `DATA_AVAILABILITY.md`.
4. TeX builds with zero undefined references or citations (`pdflatex`, `bibtex`, `pdflatex`, `pdflatex`), with
   author actions shown, then hidden.
5. Grep the deliverable for the loaded verbs of section 11 and for retired numbers, as whole words.
6. Re-verify every quote and number against the source files before anything goes to a third party. One summary
   said "all datasets" where only some had been checked.
7. Read every rendered page you changed.
8. Say what was not checked: claims with no record, links behind logins, code that could not be run here.

## 13. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| the project's notes and a config example as ground truth | "serious red flag" | the released commit, signatures, call sites, logs |
| porting "the latest" code with new functions | "exact metric, no new stuff" | the bytecode-identical file, nothing else |
| "N vs M" discrepancy framing | "as if it's [a] discrepancy" | the value run, stated once |
| a TL;DR that led with what was wrong, loaded verbs | "seems like I did a hacking" | verdict first, "state more clearly", numbers kept |
| "our metric is the best" | "no faking, no over-claiming" | the measured wins and the measured weakness |
| rank changes under injected contamination | "rather on the real data" | ranks on the untouched outputs |
| a plotted estimate or a subset run | "I want accurate data on this" | not run, and a fetch list for the missing value |
| a hollow glyph for a missing value | "don't make it weird" | the gap stated in text (a value that cannot exist takes the one hatched missing glyph) |
| "could not be used, so we built our own" | "use direct on-point stuff" | the reason: "the paper cites no code" |
| a glossary and limits box at the top | "total AI slop" | terms defined where first used |
| a dataset link to a similar dataset | "not sth just similar tissue type and tech" | a byte-exact match |
| an algorithm called by a library's name | "get to the bottom of this" | the original code, "adapted from" |

## Reference files

- `references/tracing.md`: tracing commands, the repro wrapper, the exactness ledger, bytecode recovery and the
  exact release.
- `references/provenance-and-data.md`: opening artifacts, checking dataset descriptors, algorithm attribution,
  byte-exact data availability with `remote_zip.py`, the reference audit, paywalled sources and quoting with
  `kwic.py`.
- `references/manuscript-checks.md`: number control, completeness tables, the text-only reimplementation, claim
  scope, the rewrite safety net, author actions and the in-place splice.
- `references/audit-protocol.md`: fresh-context auditors, how to split the work, kinds of finding, the skeptic,
  verdict words, the hand-back format, brief templates.
- `references/defence-report.md`: the analyses that defend a metric and the form of the report.
- `scripts/extract_numbers.py`: every number in TeX or Markdown with its sentence; `--diff` for the safety net.
- `scripts/remote_zip.py`: one member of a remote ZIP over HTTP ranges, compared byte for byte.
- `scripts/kwic.py`: keyword-in-context search over downloaded paper text, for quoting; `--self-test`.
- `scripts/docx_paras.py`: paragraphs, comments and image references of a docx to TSV, nothing executed;
  `--self-test`.
- `assets/authoraction.tex`: the author-action macro. `assets/claim_ledger.tsv`: the ledger header.
- `assets/reproducibility_bundle/README.md`, `assets/reproducibility_bundle/RUN_MAP.md`,
  `assets/reproducibility_bundle/METRIC_MAP.md`, `assets/reproducibility_bundle/inputs.tsv`: the bundle to build
  beside a paper when none exists (`references/tracing.md` section 1).
- `THIRD_PARTY.md`: what is borrowed (nothing from third parties) and what the protocol shares with common practice.
