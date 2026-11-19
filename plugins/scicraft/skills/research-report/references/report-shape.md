# The shape of the report

The form below survived about 22 rebuilds of one report in two days and was then written down as a standing rule.
Each part names the round that set it.

## 1. Who it is for

Write for a reader who knows the field and has not followed the work: a supervisor reading on a phone between
meetings, a co-author who joins the thread late. Before writing, list the internal words of the project (run
names, variant labels, counts such as "the [N] prompts", operations such as "pruning"). Each one either gets a
one-sentence definition where it first appears or leaves the report.

## 2. The opening

Nothing stands between the title and section 1 except the meta line, the answer line, the summary and the TL;DR.

**Meta line.** For whom (the question and its date), the author, the date of this version.

**Answer line: one sentence.** The answer with its number, above the summary (`<p class="answer">`, bold, body
size). It came from "make a one sentence summary of this also on top" on the report that set this form. In the ML
ablation below: "The two-stage schedule explains 1.5 of the 1.8-point gain."

**Summary: three sentences.**

1. What was measured or asked, in words the reader already has.
2. What was done, with its size (runs, seeds, datasets, units).
3. The answer, with its number, and what it means for the decision.

| Field | Summary that was accepted in form |
|---|---|
| ML, ablation | The question was whether the two-stage schedule or the larger batch explains the 1.8-point gain. We retrained both at 3 seeds with one change at a time. The schedule accounts for 1.5 of the 1.8 points, so the paper should credit the schedule. |
| ML, metric question | The question was whether our calibration error favors larger models because it bins by confidence. We recomputed it with 5 binning schemes and on 4 models whose true calibration is known by construction. The ranking of the 6 models is the same under every scheme, and the error tracks the known miscalibration with Spearman 0.98. |
| Biology, cell typing | The question was whether marker-based cell types agree with reference-based ones on the new tissue. We typed 210,000 cells both ways and compared the labels cell by cell. They agree on 87% of cells, the disagreement sits in two immune types, and the marker list needs two more genes. |

The numbers in these rows are illustrations of form, not results.

A summary that was thrown out assumed the reader knew an internal count: what its items were, where they came
from and what the verb of the score meant. The rewrite
named what the score measures, what had been questioned, and the answer.

**TL;DR.** Three to seven numbered items. Each is one bold finding with its number, at most one plain sentence
after it, and a figure reference that links to the section: `(<a href="#s2">Fig. R3</a>)`. The weakness found goes
here too, with its number. A TL;DR item is a claim the figure shows; an item that no figure backs is a sign the
figure is missing.

**No box before section 1.** The Terms box and the Limits box were both added in good faith (one because the
author had asked "define it explicitly, really important!") and both were removed the same day. Definitions go
where the term is first used: in the section's info box, or in the caption.

## 3. Sections

- One section per question the reader would ask, in the order they would ask it. A title that names the question
  (for example "Same prompts, same seeds, same budget") beats a title that names the method.
- The first line is one bold sentence at body size (`<p class="msg">`) that states the section's result. One
  sentence, about 10 to 25 words; `check_report.py` warns above 30 words. Suggested, not yet tested in real work: the author set no number.
- Then two to five plain sentences, a formula box if a quantity is defined, the figure, and its caption.
- Check each bold lead against the data. Over-broad leads were narrowed in review: "all scores" became "of the
  scores tested"; "equals" became "within [tolerance]".

## 4. Sentences

- **A number or a decision in every sentence.** A sentence that holds neither is either a definition (keep it, and
  keep it to one sentence) or filler (cut it). `check_report.py --list-bare` prints the candidates.
- **Direct.** Replace the hedge with the fact: "the paper cites no code", "the package returns an empty result on
  our data", "the run needed about two more hours, so it was stopped".
- **Operational definitions.** For example: "Equal budget: every model is trained for exactly 10^5 steps at
  batch 256; runs that diverged before that are reported as diverged, not dropped."
- **Derived counts explained.** "24 runs" needs its arithmetic in the same sentence: six seeds for each of
  four variants.
- **Settings as run.** Find the value in the run config, the recorded command or the log, and write it once as the
  setting. A function default appears only when it explains someone's failed rerun, and then as a rerun
  instruction.
- **Scope named.** For each summary sentence, name the datasets, conditions and baseline it covers. Write "excess
  over 1" when the fold is of the excess. Write "on the three datasets tested" when a fourth exists.
- **Concessions with numbers.** List the defenses and the concessions side by side and count the numbers in each;
  a list with numbers on one side only reads as advocacy.
- **Full sentences in captions.** "Open circles: no contamination. Band: ..." became "Open circles are cells with no
  added contamination. The shaded band spans ...".
- No em dashes, no semicolons in prose, no "not X but Y". The `humanizer` skill covers the rest.

## 5. Formulas, boxes, appendix

- State each formula once, in a display box, followed by one or two small sentences that name every symbol.
- An info box (`<div class="box">`) holds a definition or a short fact the section depends on, one to three lines.
- The appendix is a set of collapsed `<details>` blocks: variants and controls, settings the source leaves open
  and the values chosen, other metrics from the literature, text corrections, code and data. The print version
  opens all of them.
- The last appendix block is always "Code and data": repository, branch, commit and date of the code behind every
  number, and the report folder.

## 6. Length

Count the main-text words (sections 1 to n, captions excluded) every round and say the count in the delivery
message. One report went from about 2,300 to about 4,100 words because each review round added concessions and
definitions, and the author then cut it hard. Set a cut target with each round of additions. Formulas and tables
the author asked for stay; prose moves to captions and the appendix.

## 7. Integrity

- Choosing what to lead with is presentation. Changing what the records support is misreporting. A weak or mixed
  result goes to the appendix with its number, never out of the report.
- A threshold for what is reported (which runs count as complete, which values are printed) is applied to every
  result alike and stated in the report.
- When the user asks for a claim the records do not support, write the narrower claim that holds and say so in
  the delivery message, with the evidence and the options (rerun, or revert the text).
- When a number in a sent report turns out wrong (one correlation had been computed on 3 of 5 methods), recompute,
  resend, and say it plainly: "The numbers I gave you a moment ago were wrong."
