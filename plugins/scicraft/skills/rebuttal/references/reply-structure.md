# Reply structure

The template is `assets/reply_template.md`: one block per comment, the header line `<<<<< key | title | readers >>>>>`,
read by every script in `scripts/`.

## The general response

Readers: the area chair first, then every reviewer. It is read in about 30 seconds and decides how the replies
below it are read. The senior author's rules: "they will need a clear summary in 2 to 3 sentences. A longer
exposition with details can follow"; "General reply: 1p max"; "Use K.I.S.S"; "Have full ablation tables in
individual replies (and sort from important to less important)".

The shape that was accepted, after a long version with tables and a terse version with code words were both thrown
out:

1. Thanks, then what the reviewers valued and what they doubted, in their words. "We agree that ..." for the shared
   concern.
2. "The revision makes two main changes." Two numbered items, each a bold label of a few words and one sentence.
3. "The main results are summarized below." Three to six bullets: a bold topic name, one sentence in the field's
   standard terms, the tag of the reviewer who asked (color-coded tags were used on one platform:
   `$\color{red}{\textsf{R1}}$`). One italic key sentence per topic at most.
4. One closing line: the point-by-point replies give the details; changes are highlighted in blue in the revised
   paper.

About 280 to 400 words. No tables, no line numbers, no method details, no p values, no figure pointers. In any
summary use ranks and plain heads (what changed, what we added, results, scope), never test statistics; a summary
"full of Elo, intervals and Z" was "non-sensical numbers". Shared details that several reviewers need go
below the summary inside the same comment or into each reply. Never a second general comment.

## The reply to each reviewer

One comment per reviewer, each under the platform limit. Structure:

```
We thank the reviewer for [the strengths they named, in their words].

> *W1. "[the reviewer's sentence, verbatim]"*

**[One bold sentence stating exactly what the cited lines show.]** [One small table copied from the paper, or two
to three evidence sentences, each with the comparison named and line numbers.]

> *Q1. "[...]"*

**Yes.** [...]

We thank the reviewer for these requests, which [what they produced], and would appreciate a reassessment.
```

Rules that shaped it:

- **The bold lead claims no more than the cited lines show.** Round 2 of a proofread found 15 items, mostly bold
  leads that went further than their lines.
- **Answer part by part.** A point with three questions gets three answers.
- **Lead with the answer and one piece of evidence.** "Make their life easy ... give the main things in the
  response" (a colleague's advice the author made binding). "If you were the reviewer right now, would you read?"
- **Short tables, in the text.** Copy rows from the paper's table; do not refer to figures (a figure on most
  platforms can only be a link).
- **Every parenthesis in a table reads on its own.** A cell of the form "| x (1st, training-fold mean y) |" meant
  nothing to the author a day later; "| x (1st of N, now above the training-fold mean of y) |" did. Name what a
  control is and which way it compares.
- **Cite related work by author and year where a method is first named.**
- **Define what you introduce.** "every single thing should be clearly introduced, or cited": a probe, a test, a
  statistic, at first use.
- **One name per thing, the paper's name**, and the field's existing term. Internal code names never reach the
  reader (a loss written as `L_x`, an internal module name, a run label).
- **Mention what is still running only if it is running**, with when it lands, and what the reply will say for
  either outcome.

## One spine for the whole reply set

Choose the order of evidence once and keep it in the general response, in every reply and in the revised paper.
Lead with the aggregate the reviewers asked about, then the per-task placings, then the paired results; any
second summary comes after them. When one round led with mean rank, the author moved it back: "It's not about mean
rank, they raised this." Present ablations as two kinds: single components removed from the full model, and the
whole block replaced by other architectures.

The revised abstract keeps the arc of the submitted one at the same length or shorter, "as clean as the first
version, but stronger". A new shape asks the reviewers to read a new paper.

## A summary for expert co-authors

Co-authors who know the method want the technical deltas only (losses, notation, parameters). Open "What changed" with
about half a page of math that defines every symbol the change table uses. Then the table, with a submitted column
and a revised column and no "why" column, then one short plain paragraph on why. Read the differences from the two
runs' manifests (the submitted configuration against the final one), so the question "did anything else change?"
is answered from data. In the source work the summary led with one line naming the component that stayed fixed and
the two that changed.

## Tone

| Reader | Register | What worked |
|---|---|---|
| a reviewer, in public | very polite, factual, confronting only with their own words | thanks, their praise quoted, the gap between text and rating stated once, one question they can answer by moving one step |
| a reviewer who kept a low score | the same, plus a calm close | "We know of no point of the original review that we left unanswered", the unchanged rating, a question |
| the area chair or editor, in private | firm, brief, evidence first | `references/chair-note.md` |

- "There is absolutely nothing to gain from being blunt" (a senior co-author's advice).
- Blunt lines go to the private note or nowhere. A sentence on how the paper could have been framed
  differently was dropped from a public reply.
- Leave the reviewer an exit, but do not write a weak sentence to build it. "Several of the comparisons above were
  spread over the appendices, and we hope that seeing them side by side helps" was rejected as weak. The close that
  held: "With respect, we cannot reconcile this rating with the reviewer's own assessment. A paper described in
  these words is not a clear rejection, and we kindly ask the reviewer to reassess the rating."
- Do not repeat the reviewer's attack phrases. Use neutral topic labels and quote the reviewer where they concede.
  Never quote a reviewer phrase that concedes your side (a "several" in "addresses [several] of my concerns"
  concedes that the rest are open).
- Give a competitor no points. Frame the comparison at the level of the paper's claim: what the cited test pools,
  the result at the scale the paper claims, with line numbers. "ranks lower", never "is worse".
- **When a reviewer cites a test in which a competitor is not separated from your method**, answer in three parts,
  each with line numbers: what that test pools, the result at the scale or setting the paper claims, and how the
  competitor's rank moves across scales where the paper prints it. Do not volunteer a sentence that the competitor
  leads at some scale. Its row stays in the paper's table, complete, and a reviewer who asks gets the number.
- **Strike concessions nobody asked for.** "On par with", "essentially" and a limiting "only" ("only on two tasks")
  hand the reviewer a weaker reading of a result the table already states. Delete the word and keep the number. A
  concession stays only where the reviewer asked about exactly that point, stated once, plainly, beside what holds
  (`references/triage.md`, unasked concessions).
- No aggressive comparatives: a sentence that counted how little the other methods achieved was "a bit aggressive
  ... strength is in subtlety".
- Polite phrases can concede: "we left them for future work" conceded the point. "they belong in a [other field]
  journal, which [the venue] is not" kept it.
- "We would like to kindly draw your attention to ..." is the author's phrase for pointing at evidence.

## Voice of reply prose

From the author's own polished replies and the rules struck into them:

- Full declarative sentences, one idea each. No fragments ("Two more probes.").
- No inline colon, semicolon or dash in our sentences (headings and tables exempt). `check_replies.py` enforces it.
- No staged contrast ("not X but Y", "X, not Y"). No tricolons, slogans or filler openers.
- No indirect-question topic sentences ("we tested whether ...", "your questions were whether ..."): state the finding.
- No hedges ("approximately", "remains a diagnostic"), no evaluative words ("strongest", "leads", "wins", "best
  published"): state the measured relation with both numbers ("[x] against [y] for the next method").
- **List the bare short sentences before each send.** Slogans pass fact-checking proofreaders because they hold no
  fact to check; three rounds passed "With X, Y and Z fixed, the model matters". List every short sentence of ours
  with no number, no line pointer and no citation, and read each one. It is a heading in disguise or a slogan: cut
  it, or rewrite it as the finding with its number.
- Concrete verbs: we compared, removed, encoded, trained, tested.
- "Replace existing paragraphs rather than expanding them."
- Run the `humanizer` skill on composed text, then diff the claims: a humanizer pass that changes a claim is
  reverted.

## Journal point-by-point responses

A journal letter keeps this discipline and adds a five-part block per comment (the comment verbatim in full,
Response, Revisions implemented, Location in revised manuscript, the checklist evidence), a three-paragraph opening to
Editor and Reviewers, and no length limit. `references/journal-revision.md` has the block, the opening, and the
patterns for disagreeing, declining an experiment and a comparator that could not be run; the template is
`assets/journal/04_RESPONSE_LETTER.md`.
