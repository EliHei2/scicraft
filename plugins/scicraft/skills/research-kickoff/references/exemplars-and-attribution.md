# Exemplars, vocabulary, and the true origin of an algorithm

## 1. Studying exemplars

When the project attempts a new kind of output (a method paper for a venue, a book chapter, an architecture
figure, a benchmark table), study the field's best instances first and record which moves to adopt.
`assets/EXEMPLARS.md` is the record.

- **Collect 5 to 10 exemplars as files on disk and open them.** Four of eight rejected opening paragraphs of one
  book came from working off a summary of the exemplars instead of the exemplars.
- **Fix the dimensions before reading**, the same for every exemplar: headings, contributions, depth of method
  detail, where the mathematics sits, how limits are conceded, the opening, share of background, figures.
- **Quote verbatim.** Mark a finding "confirmed" when further exemplars agree; state disagreements without
  averaging; state gaps ("where a study found nothing, that is stated rather than filled").
- **Measure twice where judgment enters.** One book was measured in two passes; "their disagreement is itself a
  measurement ... treat plus or minus 10 points as noise".
- **Uniform polish is a machine signal.** Good books ship typos; what makes them read human is specificity and
  local commitment.
- **Turn each adopted or banned move into a numbered rule with evidence and a check.** One book project kept its
  standing no-go rules from its exemplars in this form, each with its own search line. Each rule carries six
  parts:

  | Part | What it holds |
  |---|---|
  | Number and rule | one sentence, stable id (`R1`, `R2`) so findings can cite it |
  | Why | what goes wrong without it |
  | Evidence | the verbatim quote from an exemplar, with file and page or line |
  | Search line | one `grep -nE` (or `rg`) pattern that finds violations |
  | Allowed in | the places where the pattern is legitimate (a quotation, a code listing, a glossary) |
  | Detector gap | what the search cannot see, so a reader checks it by eye |

- **Run the sweep and report two tables.** Instances: file, line, rule, quote. Verification: rule, hits, where,
  judgment, with every false positive named.

  ```bash
  # one rule, one line; the pattern and the file glob are parameters
  grep -nE '\b(crucial|seamless)\b' chapters/*.tex
  ```
- **For a figure, copy one named exemplar exactly**, often a panel the author made or a figure from a
  specific paper. Weeks of schematic iteration converged only once one exemplar was fixed and every panel copied
  its theme. Figure work itself belongs to `figure-development` and its siblings.
- **For a paper, calibrate density and length to recent papers at the target venue** and fetch the venue's
  official style. The author asked to look at the most cited papers of the venue from the last three years and
  adjust the level of detail to them.

## 2. The field's vocabulary

Use the field's word for shared objects and your own word only for objects you built. The author rejected an
invented term: "'instrument' no one calls it like that, look up [the vendors'] websites, and other papers, really
name these stuff liek the field does."

How the terminology table of one project was mined (the full procedure belongs to `author-voice`):

1. A corpus of the author's published texts, kept apart from machine-drafted wrappers (2 dashes in 225 lines of
   the author's own text against 135 in 738 lines of a wrapper).
2. For each imported term in a draft: hits in the draft (`grep -roiw -- "TERM" *.tex | wc -l`), files, hits in the
   corpus, the corpus term that replaces it, and a quote that licenses it.
3. A verb table with counts: "assign" 409 times in the author's corpus, "allocate" 0.
4. Every row wired into a check, so the replacement is enforced; a table that no check reads changes nothing.

## 3. The true origin and name of an algorithm

Before a manuscript or a note names or cites an algorithm, find the primary source and compare it line by line.
A manuscript can name a method after a tool it only resembles; the check can show that the constants match an
older algorithm instead, and that the name used means something else in standard libraries.

The procedure:

1. **Find every copy of the implementation.** Grep all installed versions and repositories for the class name and
   the original author's name. Read the implementation and write down the line number of every threshold and
   constant. List every copy; copies can carry wrong docstrings naming other algorithms.
2. **Find what the text says.** Extract the manuscript's paragraphs (for a .docx, a small `zipfile` plus
   ElementTree script, run with `python3 -I`), grep for the candidate names, including in the comments part, and
   map figures to the paragraphs that describe them.
3. **Read the comparator's source across its tagged versions** and its changelog, and diff the versions. A
   changelog sentence can apply to one release only.
4. **Find the original reference and its original code.** Search, download the original implementation, and match
   constants line by line. Where any constant differs, the honest phrase is "adapted from". Get the DOI
   metadata from Crossref or Semantic Scholar when the paper is paywalled.
5. **Check what the competing name actually means** in the standard libraries of the field; the same name can
   denote a different published method there.
6. **Trace which outputs feed each reported number.** Recompute one figure statistic from the prepared data and
   check that each value measures what its label says.
7. **Deliver the bottom line first**, then what the code does in numbered steps with file:line, the differences,
   replacement sentences for each location in the manuscript, and the source links. Edit the manuscript only if
   asked.
8. **Say plainly when your own earlier claim was overstated.** Asked "is it really simiarl ...?", the right answer
   was a plain no, an admission that the earlier answer overstated the likeness, and one concrete input on which
   the two methods give different outputs.

## 4. Citations

- **Every citation is checked against the paper, and claims are checked against what the paper actually did.** A
  research log recorded a reference that does not exist (corrected to the real paper with a different author
  list), and a claim attributed to a study that never measured the quantity. A fabricated citation was once used to
  justify a design choice; it was removed after searching the paper and the code.
- **A missing reference is a placeholder that fails the build**, such as `\citep{NEEDS_CITATION_shortdesc}`,
  never an invented key: "a fabricated key does not fail anything". Prefer omission to a hedge, and a hedge to a
  fabrication.
- **Cite the origin**, adjacent to the named method, one source per claim. Verify by DOI against Crossref, and
  record what could not be verified.
