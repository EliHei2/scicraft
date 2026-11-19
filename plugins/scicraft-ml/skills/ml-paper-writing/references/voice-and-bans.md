# Voice and bans for a machine-learning paper

What separates a strong ML paper from generated prose is plain sentences that each carry one idea, stated
once, with the result doing the work. The model is the register of I-JEPA (Assran et
al.), GraphSAGE (Hamilton, Ying, Leskovec), Graphormer and the DINO line: declarative, concrete, motivation
first, unshowy. The author asked for it in these words: "write like a human, look up top LeCun or Bengio or
Leskovec papers".

Contents: positive rules; cadence; the ban table; transformations; the preserve contract; verification.

## Positive rules

- **Claim, then mechanism, then at most one reason.** A reason goes only where a reader would be surprised.
- **"We" for decisions, present tense for what the method does, past tense for what was observed.** "We mask
  40% of the cells. The encoder pools rows by attention. The model reached .74 on task A."
- **One idea per sentence.** Break any sentence of three clauses or 60 words.
- **The main verb within the first eight words.** Length trails behind the verb in one of three tails: a
  participial inference (", showing that ..."), a bare appositive (", the highest-ranked published model"), a
  cost tail (", turning a missing value into a false category").
- **Move between sentences by repeating the noun.** Measured over 35,704 words of the author's published
  prose: zero "Moreover", "Furthermore", "Additionally", "Hence", "Notably", "Crucially", "In summary",
  `In order to`; two "However"; four "Finally". At most one "Finally" or "Overall" per section. "therefore"
  only after the verb ("is therefore a separate axis").
- **Parentheses carry provenance, never asides.** "k = 20 neighbors (the 90th percentile of row degree)".
  A parenthesis that carries a whole claim is a sentence trying to get out.
- **Short verbs of operation for inanimate subjects.** determines, assigns, pools, compresses, returns,
  propagates. No sense verbs for models ("sees", "knows", "wants", "understands"): "the encoder receives
  neither column names nor types as input". No "aims to" for what the method does.
- **Bound a claim in the sentence that makes it, and give the bound a cause.** "It ranks first on the four
  classification tasks and remains competitive on regression, whereas models trained on single tables
  typically rank higher on their own task." A caveat without a mechanism is a mood. Never a straw-man hedge ("not a
  universal replacement").
- **A concrete fact in every opening and topic sentence.** Name methods, inputs and operations. "Existing
  methods differ in which evidence decides ..." was rejected as "super not scientific"; write "Gradient-
  boosted trees split on raw feature values and ignore column semantics."
- **Measured relations, never evaluative adjectives.** "ranks first by mean rank", "is rated above X by
  Elo", "the highest-ranked published model". The author: "strong or good or bad are not scientific".
  Do not write "leads"; a sentence the author wrote with it and a named measure stays as written.
- **Define or cite every term, probe, test and statistic at first use.** "when you define new things like
  MLP probe ... every single thing should be clearly introduced, or cited". One audit of a submitted paper
  found 49 undefined, uncited or used-before-definition terms.

## Cadence

Uniform 15 to 22 word sentences read as machine text. The author's measured rhythm is bimodal: a 25 to 45
word specification sentence carries the paragraph, and a 4 to 10 word verdict sits at its edge ("Yet tables
have no single natural order."). Median paragraph of four sentences; the topic sentence is the shortest.
When editing an existing paper, match its measured cadence instead: one audit found added text at a median
of 29 words per sentence and 24% over 45 words, against 17 and 1% in the submitted text, and called cadence
"the loudest giveaway". Measure with the `author-voice` skill.

## The ban table

| Tell | Example | Fix |
|---|---|---|
| em dash `---`, spaced en dash ` -- `, Unicode dashes | `the encoder---a transformer---reads rows` | comma, parentheses or two sentences. Ranges keep `12--18` |
| `not X but Y`, `X, not Y`, `not just X` | `the unit is not a fixed patch grid but a recursive partition` | "the unit is a recursive partition" (the grid was ruled out earlier) |
| `rather than`, `instead of` as a habit | `X rather than Y` where Y was never a candidate | drop Y. A contrast whose Y was a real candidate stays, positive half first |
| triad for rhythm | "attend-locally, pool-globally, read-anywhere" | one plain clause that says what the three share |
| slogan sentence | "Masking is the point.", "Attention is not the villain." | the plain fact it gestures at |
| filler opener | `It is worth noting that, importantly, in order to ensure robustness, we` | "We" |
| over-justification | every choice wrapped in "because ... so that ..." | state the choice; one reason where a reader would ask |
| self-praise | `principled`, `elegant`, `powerful`, `novel`, `carefully`, `rich`, `seamless`, `comprehensive` | cut the adjective |
| vague magnitude | "substantially larger", "high stringency" | the number, version or threshold |
| number-loaded word | "couple four components" | bind, join, integrate ("couple is for 2") |
| inline colon, inline semicolon | "the rule is simple: pool every row" | state it, or two sentences. A colon before a display, table or list stays |
| separators between phrases | `rows · columns · tables`, `A × B × C` taglines | a comma or a sentence |
| daggers and special-case marks | six daggers in an ablation table | uniform settings, or one caption sentence |
| evaluative rank words | `strongest`, `best published`, `wins`, `falls behind`, `dominates` | "ranks first", "is rated above" |
| sense verbs | "the model sees neither" | "the model receives neither ... as input" |
| code words | "w/o", "A3", "lam2", `max_rows`, "held out" for general readers | human names: "−masking", "the 12M model", "val" |
| self-narration | "This section presents", "Below we", "on purpose", "auditable" | delete. One roadmap sentence per paper at most |
| invented count in a title | "One gap, two symptoms", "Three faces of sparsity" | name the things: "Sparsity in the encoder, the loss and the readout" |
| statistics words outside the paper's language | "whiskers", "detectable", "claimed", "q", "Holm" beside BH | "error bars", "significant (adjusted p < .05)", one correction |

The general humanizer patterns (closers, staged run-ups, shallow -ing riders) belong to the `humanizer`
skill. Run it after any pass that removed punctuation: one de-punctuation pass welded clauses together with
`namely`, `rather than`, `so that`, `which is why`.

## Transformations (neutral examples)

Dash aside to parentheses:
- Before: `We evaluate on tabular benchmarks---the hardest case---molecular graphs, and 3D point clouds.`
- After: "We evaluate on tabular benchmarks (the hardest case), molecular graphs and 3D point clouds."

Dash appositive to comma appositive:
- Before: `We give the encoder a summary token---one per column---and learn a column bias.`
- After: "We give the encoder a summary token, one per column, and learn a column bias."

Slogan to claim:
- Before: "Attention is not the villain. Locality is exactly right."
- After: "Attention is the right operator within a row, where interactions are local by construction."

Triad to clause:
- Before: `The three terms are thus attend-at-cell, pool-at-row and calibrate-at-table, not three copies of one feature.`
- After: "Each term reads missingness at a different level, so the three do not encode the same quantity."

Evaluative to measured:
- Before: "Our model is the strongest method and wins on most tasks."
- After: "The model has the best mean rank, 2.1 against 4.6 for the highest-ranked published model, and ranks
  first on 9 of 12 tasks (Table 1)."

Undefined to defined:
- Before: "An MLP probe on frozen features reaches .71."
- After: "A two-layer perceptron trained on frozen features with the encoder fixed (an MLP probe;
  \citealp{key}) reaches .71."

## The preserve contract

Change prose only. Every `\cite`/`\citep`/`\citet`, `\ref`/`\eqref`/`\cref`, numbered equation, macro
(`\method`, `\sg`), defined symbol and number survives byte for byte. Before and after, the multisets of
citation keys, labels, references and numeric tokens are identical, the equation count is unchanged and no
sentence is duplicated. A careful pass in the technical register lengthens the text by 3 to 5 percent (one
measured run went from 35,000 to 36,274 words with every label and citation intact, and surfaced four
factual errors on the way). A shorter result usually means facts were deleted.

Text the author has already humanized is frozen. Change it only to fix an error, a number, a pointer or a
hard limit, or on an explicit order, and list every change with its reason. In submitted text, only
punctuation fixes; rewording belongs to the revision, marked as the `rebuttal` skill describes.

## Verification

```bash
cp main.tex main.before.tex                      # snapshot before the pass
python3 scripts/ml_paper_check.py main.tex       # bans, tables, intro, headings, markers
python3 scripts/preserve_diff.py main.before.tex main.tex   # numbers, keys, labels, equations, length
grep -nE -- '---| -- ' main.tex                  # the dash grep from the original skill, as a cross-check
grep -oE '\\(citep|citet|cite|ref|eqref|cref)\{[^}]*\}' main.tex | sort | uniq -c
grep -E 'Citation .* undefined|Reference .* undefined|^! ' main.log   # after a full build
```

All come back empty, or unchanged for the citation multiset, before the pass is done. Then read the whole
paper once yourself, top to bottom: slice readers miss self-narration almost entirely.
