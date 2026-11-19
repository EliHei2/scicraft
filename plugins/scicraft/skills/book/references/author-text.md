# The author's text: what may be touched

The author's sentences carry the argument the way the author makes it. Every wholesale rewrite in the source
work was reverted, most of them the same day. This file holds the rules and procedures that replaced rewriting.

## The table

| May | May not |
|---|---|
| change a number, a status, an attribution or a retired result inside the author's sentence, listed old to new with the paper's quote | restructure, re-title, merge or split the author's chapters |
| fix a factual error, a typo or a conversion slip ("cellsd", "mayroduce") | replace the author's wording with the agent's, however "human" it reads |
| remove the agreed house bans (dashes, inline semicolons) in single-word or single-sentence brushes | run an editor or "humanizing" fan-out over the author's prose without a request that names the file |
| move a whole procedural paragraph verbatim to an appendix | compress sentences to save space |
| flag a style breach in the author's text as a decision ("it's your text") | silently fix a style choice in text the author just pasted |
| propose a restructure as a plan at the narrative level, then stop | carry out a restructure; it is the author's decision |
| report defects found in the author's current chapters | rewrite a heading the author wrote |

"Update against the new version" means surgical fact updates. "Rewrite like a human" plus "update against new
manuscripts" was once read as a license to restructure: twelve new chapter files, new headings, a fan-out of
editors. It was rejected whole ("you really butchered my beautiful text, the titles were so nice and human") and
restored byte for byte from the snapshot. When a request's breadth is ambiguous, take the narrowest reading and
show the plan.

Spans the author wrote personally (the Summary, the opening section, the aims) get error fixes only, and every
agent brief says so. An audit's three edits to an aims paragraph were rejected. Making the Summary "more formal"
changed the register only: same content, same order, mirrored in the translated summary.

## Snapshots

- **Snapshot before every fan-out, restructure or integration**, and give the path in the first report:
  `mkdir -p _snapshots/rN_<label>_<date> && cp -R chapters front back style tools _snapshots/rN_<label>_<date>/`.
  Usage limits killed 9 to 12 running agents four times in one session; the snapshots were the only restore point
  because the working tree was untracked.
- **Back up a file before every edit batch** (`cp file $SCRATCH/<name>_before_<change>.tex`).
- **After a revert, diff the tree against the pre-change commit.** A parking step once swept narrative files into
  an attic folder and the revert did not bring them back (`git checkout <commit> -- <dir>`).

## The drift gate

`scripts/chapter_drift.py SNAPSHOT_DIR CURRENT_DIR --show-lost` classes every baseline sentence as same, near, edited
or lost. The gate used in the agent contracts: same + near at least 80 %, lost at most 10 %, each lost sentence
logged with its reason (a repeat inside the section, a stage direction, a retired fact). Example outcomes after a
contract with this gate: one chapter's lost share went from 40 % to 1 %, the Discussion's from 90 % to 8 %.

Add `--structure` after a heading pass, an appendix move or a writer agent's draft. It compares the `\label` keys,
the `\includegraphics` targets and the citation keys of each pair and fails on a label or figure file that is gone
or changed, unless it is listed in `--intended FILE`. A removed label that nothing references passes the LaTeX
build silently, so only this check catches it.

## Overlap with the source papers

Use the papers' terms, never their sentences, unless the author orders a verbatim version. A similarity check at
delivery flags long verbatim runs from published papers even when they are the author's own.

```bash
pdftotext -layout papers/paper1.pdf sources/paper1.txt        # textutil -convert txt for a .docx
python3 scripts/overlap.py chapters/*.tex --sources sources/ --minspan 12 --max-share 0.7 --out overlap.json
```

The script lowercases and strips LaTeX (comments, math, tables, citation and reference commands), splits each
chapter and each source into word 8-grams, reports per chapter the share found in each source, and lists every
shared run of 12 or more words with its file and line. Targets that held in the source book: body chapters under
3 % and a methods appendix under 8 % in the early rounds, at most 0.7 % per chapter in the final round, no shared
run of 12 or more words, and no run over about 8 words from a published legend. Run it after every paraphrase pass
and before the similarity-check upload. A run over the limit goes to the author, who rewrites it or quotes and
cites it. Unpublished text never goes to an external checker.

## Fact-check surgeries

One procedure, used for every round of factual updates (one round in the source work made 47 surgeries, each
anchored to a paper quote):

1. Read each paper. Grep the framing sentences that most often go wrong (`right unit`, `wrong`, `natural unit`,
   `canonical`, `first`, `only`, `best`).
2. Write each correction as an entry with old, new, the paper's quote and its location (`audit/surgeries.json`).
3. Trace every number in each chapter to the paper's full text. `extract_numbers.py chapter.tex` from the sibling
   skill `integrity-audit` gives one row per number with its sentence.
4. Apply in the main thread, group the surgeries by theme in a log (`SURGERIES.md`), and re-read each changed
   paragraph in context.

## Integrating a revision the author supplies (used about ten times)

The author rewrites a chapter elsewhere and hands it over: "simply fact-check and if it's correct replace the old
text with it, if not massage it a bit", "make sure nothing is lost".

1. Split the revision into per-file parts (by `% START:/END:` markers or by section boundaries). Check that the
   parts concatenate back to the original exactly.
2. Find the base version the author edited from. Diff against the committed file, never against an older draft.
3. Compare per file: citation keys, `\ref`/`\cref` targets and every number between the current and the revised
   version. Dropped keys and changed numbers are the high-risk set.
4. Diff sentences. When a revision is mostly already-merged text (one was 95 to 99 %), review only the new blocks.
5. Fact-check every new claim against the papers, the supplementary methods, the appendix and the code. Restore
   dropped facts, citations, credits and earlier decisions the revision silently undid (chosen terms, the
   epigraph, float barriers). Keep a chapter's established term over a new synonym when later chapters use it.
6. Remove house bans. Flag style breaches in the author's text instead of fixing them silently: 19 mid-sentence
   colons in one pasted Introduction were left and listed.
7. Build, gate, look.
8. Report: what went in, every deliberate change with its reason, which earlier decisions were kept, what the
   revision reverted (a pasted Summary silently dropped a dozen of the author's own earlier edits; it went in as
   given and the dropped edits were listed), and the verbatim share (for example 467 of 612 sentences verbatim plus
   49 lightly edited).

Tools for steps 3 and 4: `preserve_diff.py CURRENT REVISED` from the sibling skill `humanizer` lists numbers,
citation keys, labels and references that one side has and the other lacks (dropped keys and changed numbers
first). `python3 scripts/chapter_drift.py CURRENT REVISED --show-lost` gives the sentence classes; run it the other way
round (`chapter_drift.py REVISED CURRENT`) for the evidence table, since every revised sentence then counts as same,
near or lost.

**Keep a list of the author's recurring factual slips** for the project and grep each new revision for them at
intake. One draft carried the same wrong description of a data structure twice (an adaptive structure where the
code builds a fixed grid); the fix went into the list, and the next revision was checked against it.

For a small revision (the author edited 15 to 20 paragraphs of the committed file) swap only the changed
paragraphs, after checking each maps to its true counterpart and was not already moved to the appendix.

**A chapter-scale revision goes through part files** (8 to 11 agents in the source work):

1. Split it at section boundaries into `rev/parts/`, keep the originals in `rev/base/`, and give each part one
   surgeon. The surgeon brief names the sources of truth in order (supplementary methods, latest manuscript,
   appendix, code, run configurations), the credit and citation-status rules and the banned words.
2. The surgeon logs each edit by category (method, fact, credit, citation status, banned word, LaTeX) and confirms
   labels, `\cref`s, environments, braces and `$` balance against the base part.
3. Then one de-AI editor per part, with a hard deadline (8 minutes in the source work): sentence edits only, never
   a paragraph rewrite, a backup before the pass, and the preservation check before and after (`preserve_diff.py`:
   numbers, keys in order, labels, equations, table bodies, word count).
4. Assemble the parts into the chapter files once, build, look at the figure pages, commit. Later edits go into the
   chapter files directly.

**Do not re-run an assembler after later edits.** A script that rebuilt chapters from parts would have
overwritten the appendix moves, the bold cleanup and the table fixed after it ran.

## Integrating a chapter draft from a writer agent

The agent returns an assembler script that copies untouched paragraphs line for line from the current file and
applies only its listed edits. Verified wording, equations, tables, boxes and labels then stay byte-identical (83
labels kept in one chapter). Before installing, compare style counts old against new
(`book_checks.py` on both, diff the outputs), grep every new number against the source manuscript, and trace
every new credit claim to a contribution statement: one timing credit traced only to a caption draft and was
removed. Then `chapter_drift.py --structure` against the current file.

**Audit merged text against the previous verified version, not only against style rules.** One merge weakened
claims silently ("not evaluated" became "no advantage established"), reversed a prediction direction and dropped
caveats; an adversarial auditor of the merged text caught them.

## Evidence that a revision was integrated

When the author asks "are you sure you integrated it?", answer with a measurement. Take the sentences that exist
only in the revised file, search the current book for each (allowing for sentences a later pass split in two),
and report a table: new sentences, present, changed on purpose (for example 178 / 170 / 8), the overall verbatim
share, and the reason for each deliberate change.

## A verbatim assembly, when the author orders one

A copy-paste version assembled from the papers' own sentences worked once, as a separate tree. Keep it in its own
folder and never merge it into the author's chapters; report defects found in the author's chapters instead of
fixing them there.

1. Freeze a sentence corpus with a stable id per source sentence (`MS.0001`) and a checksum file; the builder
   refuses to overwrite it without `--force`. Fix errors in place without renumbering, and list never-copy units
   (editor notes, placeholder paragraphs) and source conflicts in an errata file. Build with
   `scripts/verbatim_corpus.py build`, apply the errata file with `scripts/verbatim_corpus.py errata`.
2. Every assembled sentence carries its id in a comment (`% MS.0001`), new connectors carry `% [NEW]`, and
   third-party sentences sit in a macro that prints them flagged. `scripts/verbatim_corpus.py check` reads these
   comments.
3. A provenance check labels each sentence verbatim, edited or new (the tree that worked reached about 91 %
   verbatim plus edited). Run `scripts/verbatim_corpus.py check`; it verifies the corpus checksum first and exits
   1 on an untagged sentence, an unknown id or a never-copy id.
4. Then reword toward the overlap target with flow first; a number diff must report identical.

**Allocate by the author's contribution, never by the paper's section order.** That order buried the contribution,
and its connectors read as machine-made. In the cleaning round use the author's sentence shapes: a section opens
with the object and the number, one fact per sentence, no connector that only announces.

## The last polish

The de-slop polish is the last text pass. It runs after every fact, citation and heading pass has landed, so no
later pass undoes it or brings patterns back. It changes single words and punctuation only: an em dash becomes a
comma or a new sentence, an inline semicolon becomes a full stop, a repeated "Together," or a second "rather than"
in a row is cut. A phrase that matches the papers' terminology stays even when it looks like a pattern. One final
pass of this kind made about a dozen single-word cuts, mostly the filler "particularly". The pattern lists are in
the sibling skill `humanizer`.

## A pasted text with author-year citations

1. Inventory the chapter's labels and the external `\cref`s that point into it.
2. Resolve each "Author et al., Year" to a bib key by first-author surname and year; search for the rest; fetch
   missing ones by DOI from Crossref.
3. Assemble into the chapter template, keeping the figure blocks; place figures at first mention; convert
   "(Chapter 2)" to `\cref`.
4. Build, look at a contact sheet, commit.

## Personal documents

When editing the author's email or form text, remove what the author would not send (auxiliary contacts,
department tags), fix typos, return it, and go back to the book.

## Learning the author's style

When the author rewrites a passage, diff the two versions, classify each change (cut, word swap, reorder,
register) and record the rule with a before/after pair in the edit ledger the `author-voice` skill keeps. Text the
author approved is never touched again ("I told you to keep fixed, but you changed it").
