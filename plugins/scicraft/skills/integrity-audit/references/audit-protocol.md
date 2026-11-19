# The audit protocol

How the author ran audits by fresh-context agents, written from their own rounds: a Methods supplement checked
against code by about 15 agents in lanes, a merged supplement reviewed through five lenses, a manuscript section
fact-checked by four read-only agents, a defense report reviewed by five personas, a 278-entry bibliography split
across five agents, and a 55-figure book audit. Use it when one reader cannot hold the whole document, or when the
stakes justify a second opinion on every finding.

## 1. Rules of the round

1. **Auditors see the ground truth and the document, and nothing else.** No notes on why the text says what it
   says. An auditor who has read the rationale defends it; one who has only the sources rechecks every fact.
2. **Auditors propose; one writer edits.** The reference-audit brief said it: "You audit and propose. You do NOT
   edit any [project] file. Your verdicts will be double-checked." Read-only fact-checkers were told: "do not modify,
   move or delete any file; do not run heavy compute".
3. **A finding is a quote plus a location.** The quote is copied from the file; the location is file and line (or
   section). If neither can be found again, the finding is dropped.
4. **Every finding says what anchors it: `check` or `judgment`.** A check finding rests on a grep hit, a value
   diff or a count anyone can rerun. A judgment finding rests on a reader's reading. The author weighs them
   differently, so they stay apart in the report.
5. **A skeptic tries to knock down each finding before it reaches the author** (section 5).
6. **The author's mandate goes into the brief**: report faithfully, including results bad for the authors.
7. **If the sources cannot settle a fact, the finding stays open and becomes an author action.** Nobody fills the
   gap with a plausible value.

## 2. What counts as ground truth

| Question | Source |
|---|---|
| is the text true | the code at the commit that ran, the run's command line, logs and configs, the master results table |
| did a rewrite keep every fact | the version before the rewrite (backed up before the pass) |
| does a supplement agree with the paper | the latest main text |
| is the document consistent | the document itself |
| is a citation right | the cited work's full text, its DOI record |

Name the commit in every brief. In one round, four findings were rejected because the auditor had read a
development branch instead of the code that produced the numbers.

## 3. Splitting the work

Choose the split by what the document needs. The splits the author used:

- **By area, read-only** (a Methods section against code): one agent per subsection's run records, one per
  group of figures' analyses, one for package versions, one for benchmark design and comparator settings.
- **By lane** (a long supplement against code): self-consistency, agreement with the main text, grounding in the
  code, duplicates. About 15 agents; some lanes were lost to spend limits and their numeric suspects were recovered
  by grep.
- **By lens** (a merged supplement): facts kept against the backup, the Methods register, cross-references and
  LaTeX, machine-made prose, scientific consistency.
- **By persona** (a report for a decision-maker): a PI cold read, a line editor, a hostile fact-checker posing as
  a competitor or as a reader reproducing from the text alone, a terminology and versions auditor, an outsider who
  reads the report before the brief. The cold reader caught that only the defenses carried numbers; the
  terminology auditor caught one word with three meanings; the fact-checker caught a false caption.
- **By chunk** (a bibliography): about 56 entries per agent, plus one agent for style and the binding rules.
- **By item** (figures reused from other papers): each figure against its source figure and legend.

## 4. What auditors look for

Kinds of finding the author's audits produced, each with an instance:

| Kind | Instance from the records |
|---|---|
| text contradicts the code | estimators described from another branch; a split described as Mahalanobis 70/30 that the code made at the median distance |
| run setting missing from the text | the floor the benchmark passed, which the text did not state |
| a claim about the method the code does not do | "pretrained on X" where the code started from random weights |
| other input than stated | a dataset labeled with the wrong condition or species |
| one quantity, two values | a figure value that came from a different run than the master table |
| plotted quantity differs from the label | "% cells" on a plot of % transcripts |
| statistic misnamed | Kendall's τ reported for a Spearman computation |
| claim wider than the evidence | "all units, all datasets" where some datasets were checked |
| fact lost in a rewrite | two facts that lived only in dropped text |
| version or resource claim wrong | a comparator version stated as a release that was a later commit; a stated uniform time limit that one run exceeded |
| attribution wrong | an algorithm named after a library function it does not use; a reference credited to the wrong atlas |
| citation does not support the clause | a documentation page cited for a claim it never makes |
| term or label undefined for a cold reader | "the N pairs" with no sentence saying which pairs |
| build hygiene | undefined references, a label removed while another file still points at it |
| machine-made prose | the patterns `humanizer` and `nature-methods-writing` list |

The list is a starting point. An auditor names a new kind when a finding fits none.

## 5. The skeptic

Each finding that would change a number, a claim or a citation goes to a separate agent told to refute it:

- Is the quote in the file, at that location, in the pinned version?
- Are the two values the same quantity, measured the same way?
- Is the point already handled elsewhere in the document?
- Was the code read at the commit that ran?

Findings that survive go to the author. Findings knocked down are listed in a short appendix with the reason, so
the next round does not raise them again. Polish findings skip the skeptic.

Then the main session checks each surviving finding itself with a one-line test (a grep, a recomputed number)
before applying it. "I'll verify each against the evidence rather than accept or dismiss it wholesale." This caught
auditor errors, and confirmed real problems, including one auditor's finding that the main session's own code
release could not run end to end.

## 6. Verdict words

Use the words the author's audits used:

- **Per claim**: `TRUE`; `NARROWER` (with the wording that holds); `FALSE` (dropped). For numbers, the mismatch
  classes of SKILL.md section 4.
- **Per fact-check row**: the table `claim | text says | records say | verdict | evidence path`, plus a list of open
  questions.
- **Per figure**: `OK`, `FIX`, `DECIDE` (the author must choose).
- **Per reference entry**: `OK`, `FIX` (bibliography only), `REPLACE_IN_TEXT`, `QUERY`. **Per citing sentence**:
  `FIT`, `WEAK`, `WRONG`, `SELF`.
- **Per finding, how much it matters**: `blocker` (a reader would be misled or could not reproduce), `fix` (a real
  error that does not change a conclusion), `polish` (wording or layout).
- **The round as a whole**: `ready`, `ready after fixes`, `not ready`, with the blockers listed.
- **On the next round**, each earlier finding is `resolved` or `unresolved`; new findings are listed apart.

The last three sets were chosen for this package; the author's records grade findings and rounds without fixed
words for them.

## 7. What auditors hand back

One file per auditor, in a format the main session can check by script:

```tsv
id	kind	quote	location	text_says	records_say	evidence	origin	weight	proposed_old	proposed_new	reason
A01	run setting missing	"<verbatim>"	supp.tex:412	<value>	<value>	<path:line at commit>	check	blocker	"<exact old text>"	"<new text>"	<one sentence>
```

- `origin` is `check` or `judgment`; `weight` is `blocker`, `fix` or `polish`.
- `proposed_old` must occur exactly once in the pinned version of the file. Auditors record the file's md5
  because the file changed under them in practice; ship a check script that confirms each old string is unique and
  the edits apply in order.
- Freeze one version per round, or require the check script.
- Edits that rewrite prose keep every number: compare the numeric tokens of old and new text, and of the whole file
  before and after (`scripts/extract_numbers.py --diff`).
- The main session writes the round's summary: what was found, what was knocked down, what was applied, what waits
  for the author (in `AUTHOR_ACTIONS.md`), and the round's verdict.

## 8. Brief templates

Read-only fact-checker:

```
You are an auditor. READ-ONLY: do not modify, move or delete any file; do not run heavy compute; small
read-only inspection scripts are fine (use <python>). Ground truth: <code at commit>, <run records>, <data>.
Document: <path> (md5 <md5>), lines <a> to <b>. Return the table claim | text says | records say | verdict |
evidence path, and a list of open questions. Every finding quotes the text and gives file and line.
```

Adversarial computation fork:

```
You are Fork <X>: <TOPIC>. Adversarial mandate: try to show <claim> is an artefact of <named mechanisms>;
report faithfully, including results bad for the authors. Work dir: <scratch>/<X>/ (create). Peak memory
< <N> GB, disk < <M> MB; check free memory and disk before big steps and wait if low. Do not push or commit.
Inputs: <paths>. Import <shared engine>; do not edit it. Write: <names>.tsv and key_numbers.md. Mock data goes
in a separate folder behind a flag, never at a real output path.
```

Skeptic:

```
You are a skeptic. For each finding below, try to show it is wrong, using only the sources: find the quote at
its location in <file> (md5 <md5>); check the two values are the same quantity; check the point is not handled
elsewhere; check the code was read at <commit>. Return per finding: stands or falls, its weight, one sentence why.
```

When several agents compute, write one shared engine yourself and have them import it. Earlier forks that each
wrote their own estimator produced floor and run inconsistencies. When the engine changes, message every agent
with the change and the rerun instruction.

## 9. Re-audit

After fixes are applied, run a fresh round on the new version with the previous findings attached, so each one is
marked `resolved` or `unresolved`, with new findings listed apart. Fresh agents again: the auditors of the last round have seen the
fixes argued.
