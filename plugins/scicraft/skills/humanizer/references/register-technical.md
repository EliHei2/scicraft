# The technical register

Contents
- When this module applies
- T1 to T17: the sentence-level patterns
- Density thresholds per 10,000 words
- Searches that a script or a shell can run
- What the module must never do

## When this module applies

Papers, methods sections, appendices, books, technical reports, model cards, documentation of research code
and replies to reviewers. Run it after the general catalog (`references/patterns-general.md`), and **always
after a de-punctuation or restructuring pass**. Removing semicolons and colons is the biggest single generator
of the tells below: the clauses the semicolon separated get welded back together with `namely`, `rather than`
and `so that`. On one methods chapter a de-semicolon pass left 69 `namely`, 25 `rather than` and 15 `so that`.

A de-slopped draft can still read as machine-made: correct, dense, without repetition, and built entirely of
long multi-clause sentences with nominalized subjects. This module fixes that. Read the text top to bottom
once, because several of these tells (T8 above all) are invisible inside a 200-line window.

The examples below are invented and neutral. Keep every number, citation, label and equation of the real text.

## T1. One clause per sentence

The dominant tell in technical prose. A model writes the whole thought as one sentence with three subordinate
clauses; a person writes two or three sentences.

- Before: "We fine-tune every layer with a cosine schedule that decays the learning rate from 1e-4 to zero over
  30 epochs, which was chosen because shorter schedules underfit on the two smallest datasets, and evaluate
  after each epoch."
- After: "We fine-tune every layer for 30 epochs with a cosine schedule from 1e-4 to zero. Shorter schedules
  underfit on the two smallest datasets. We evaluate after each epoch."

A parenthesis carrying a real number is usually a sentence trying to escape: promote it with "which was" or give
it its own sentence. Parentheses are for provenance (a source, a threshold's origin, a count), not for asides.

The rule targets stacked subordinate clauses first, and length has one limit (below). One author's measured
papers have a median sentence of 28 to 29 words, with a short topic sentence and 4- to 10-word verdicts at
paragraph edges; long sentences get their length from an appositive or a participial tail after an early main
verb. Uniform 15- to 22-word sentences read as machine text too. With a voice sample, match its rhythm (see
`author-voice`).

- **Split a sentence over 45 words into two declarative sentences**, unless the writer's sample shows long
  specification sentences as a signature. `frame_density.py` lists every sentence over 45 words and prints the
  share for the text and, with `--sample`, for the sample; the sibling `author-voice` skill's
  `voice_fingerprint.py` reports the same share. The limit comes from a book de-slop pass whose house list
  ended "sentences over 45 words split"; a reply audit measured 1 percent of sentences over 45 words in the
  submitted paper against 24 percent in the added text. An en dash inside a compound or a range
  of the writer's text (`input–output`, `12–18`, in TeX `12--18`) is not punctuation and stays.

## T2. The announcing sentence

A sentence whose only job is to say what the next sentence says.

- Before: "Several statistics accompany the main comparison. The table reports wall-clock time, peak memory and
  accuracy for each model."
- After: "The comparison also reports wall-clock time, peak memory and accuracy for each model."

Same family: "Three steps produce it.", "Two controls were measured.", "The following operations recur." If the
list follows at once, the announcement goes.

## T3. Nominalizations back to verbs

- "performs an aggregation of" becomes "aggregates"
- "carries out the normalization of the inputs" becomes "normalizes the inputs"
- "rows carry a stable integer index" becomes "each row has a stable integer index"

## T4. A trailing gloss becomes a sentence

- Before: "The calibration error is (eq. 3), equal to zero when confidence matches accuracy in every bin."
- After: "The calibration error is given by eq. 3. It is zero when confidence matches accuracy in every bin."

## T5. First person for a choice, passive for a procedure

A methods section that never says "we" reads as generated. Use "we" where a person decided something and the
passive for what was done to the data. Use the present tense for what the method does and the past tense for
what was observed. A publisher may require the first person singular for acts of judgement.

- Before: "A temperature of 0.07 is used and the logits are scaled."
- After: "We set the temperature to 0.07 and scale the logits by its inverse."

## T6. Figure and pipeline jargon out of prose

`strip`, `panel`, `tile`, `arm`, `read-out`, `block` are fine in a caption and wrong in a sentence about a
computation. "A per-model strip reports latency" becomes "The comparison reports latency". A short figure label
is not a definition: do not use it as one in the text.

## T7. Stock connective frames

Count them (`scripts/frame_density.py`). More than about 15 per 10,000 words of any one frame means a pass
welded clauses instead of splitting them. `rather than` is measured against the writer's own rate when a sample
is given (`--sample`), because one author's published corpus uses it 24.1 times per 10,000 words.

| Frame | Replace with |
|---|---|
| `X rather than Y`, `instead of` | keep it when the rejected option is real; cut it when Y was never a candidate, or when two sit back to back |
| `so that ...` | a new sentence, or `to` plus the infinitive |
| `namely, ...` | an apposition with a comma, or a new sentence |
| `which is why ...` | `so ...`, or a new sentence |
| `because ... whereas ...` in one sentence | two sentences |
| `not only X but Y` | `X and Y`, or two sentences |
| `in the sense that` | drop it, or say the sense |

An older version of this table offered "X, not Y" as the fix for "rather than". That form is the same staged
contrast and is banned with it (see the contrast rule in SKILL.md). `X rather than Y` stays when the rejected
option is real, with the positive half first: "the threshold is chosen per dataset rather than fixed during
training". Cut it when Y was never a candidate. An earlier cap of one per section is stale: a later ledger
entry recorded the form as the author's signature (121 uses in one supplement).

## T8. The document narrating itself

The tell that survives every other filter, because each sentence is well formed. Any sentence about how the
document is organized, what a section will do, where a fact lives or why the document is designed as it is.

- "This appendix is the complete account of the training setup."
- "It is the single source for all hyperparameters."
- "The protocol below covers only what Section 3 does not state."

Keep at most one roadmap sentence ("Section 2 defines the task, Section 3 the model and Section 4 the
benchmark") or an orientation paragraph of at most five sentences. Delete the rest. Readers working on slices
miss this pattern almost entirely, so read the whole document yourself for it.

## T9. Furniture verbs for abstractions

`sits`, `sits at`, `lives in`, `holds`, `carries`, "where it lives". Prose about data and models uses `is`,
`contains`, `is given in`, `is listed in`. "The ablation lives in Appendix C" becomes "Appendix C gives the
ablation". "The score sits at nearly the same value" becomes "The score is nearly unchanged".

## T10. Narrating your own rigor

Announcing rigor instead of showing it: "Two controls were measured rather than asserted.", "The prior is
stated as one.", "so the reported choice is auditable", "chosen on purpose", "by design". State the control,
state the prior, and let the reader judge the rigor. An AI-use disclosure states which tools were used for what;
it does not explain its own policy.

## T11. Essay vocabulary

Words that read as a model reaching for emphasis in a text that should have none. Hunt them by name:

`load-bearing`, `the decisive measurement`, `the sharpest form of`, `is a stress test`, `pure noise`,
`headline` (as an adjective), `the wrong instrument`, `is exactly the adjustment`, `gains nothing`,
`essentially every`, `the one place`, `at the heart of`, `underscores`, `speaks to`, `the analog of X rather
than a departure from it`.

Self-praise on the contribution: `principled`, `elegant`, `powerful`, `novel`, `seamless`, `comprehensive`,
`carefully designed`, `rich`, and `robust` unless it is the technical term or is quantified.

Imported register (words absent from one author's whole published corpus that drafts kept adding): `symptom`,
`rung`, `knot`, `gatekeeper` (an author's own framing line may keep it once), `honest`, `currency`, `earns`, `buys`, `pays for`, `state-of-the-art` as filler,
`crucial`, `various`. A word that is the field's own term stays.

## T12. Verbs that give a model senses or intentions

A model does not see, know, want or aim. "The encoder sees neither the labels nor the coordinates" becomes "The
encoder receives neither the labels nor the coordinates as input". Avoid `aims to` and `seeks to` for what a
method does; say what it does. Give inanimate subjects short verbs of operation: determines, assigns, pools,
compresses, returns, propagates. Watch the opposite tic too: de-slop passes have produced chains of agency verbs
on inanimate subjects ("the loss insists", "the benchmark demands") and inanimate possessives.

## T13. Evaluative words where a measured relation exists

`strongest`, `leads`, `wins`, `beats`, `falls behind`, `best published`, `dominates`, `betters` become the relation the
records support: "ranks first on 9 of 12 tasks", "is rated above X by Elo", "the highest-ranked published
model", "ranks below". Contest vocabulary (`winner`, `runner-up`, `arm`, `competing method`) does not belong in a
comparison of two methods. "First" stays when the method is first; it is never inflated to "first on every
task" when it is second somewhere, and a lead of .004 is not a win. The rewrite never changes the rank, the
comparator or the number. A sentence the writer wrote with `leads` and a named measure stays as written; the
vocabulary rules are owned by the sibling skill, `stats-reporting/references/vocabulary.md`.

## T14. Vague magnitudes and number-loaded words

"high stringency", "substantially larger", "a small floor" become the number when the source has it ("QV of at
least 20", "2.3 times larger"). If the source does not have it, leave the phrase or mark it
`[AUTHOR ACTION: value?]`; never supply a number yourself. "Couple" means two: "couple four components" becomes
"bind four components".

## T15. Slogans and over-justification

Slogan sentences: "X is the design.", "That is the point.", "This is exactly right.", "Attention is not the
villain." Delete them, or replace them with the plain fact they gesture at. Over-justification wraps every
choice in "because ... so that ...": state the choice and give one reason only where a reader would be surprised.

## T16. Inline semicolons and mid-sentence colons (a house rule)

The author's own measured corpus used both freely (80.7 semicolons and 38.9 colons per 10,000 words), and the author
later named them as machine patterns in new and edited prose. The latest rule: no inline semicolon and no mid-sentence colon, apart from one or two per chapter that carry the sentence. A colon that ends a line before a display, a table or a list stays, and a semicolon
between list items that contain commas stays. In this register a dash becomes a comma, parentheses or a new
sentence. A voice sample that uses semicolons overrides this rule, and so does a venue or co-author style.

## T17. Discourse markers

Move between sentences by repeating the noun. In 35,704 words of one author's published prose none of these
appeared: `Moreover`, `Furthermore`, `Additionally`, `In contrast`, `Hence`, `Notably`, `Crucially`,
`Interestingly`, `In summary`, `In other words`, `This means`, `Note that`, `In order to`. "However" appeared
twice and "Finally" four times. Do not turn this into a ban on real connectives: a de-slop pass once removed every
"however" from a book, while the reference texts used it 732 times per million words. Measure against a
corpus of real writing in the same register (`frame_density.py --reference`) before banning a word.

Three related rules from other skills apply here and are not repeated: one name per thing (pattern 27 and
`author-voice`), no code-font internal identifiers in Methods (`nature-methods-writing`), and one statistics
vocabulary (`stats-reporting`).

## Density thresholds per 10,000 words

| Count | Limit | Source of the limit |
|---|---|---|
| dashes used as punctuation (em dash, spaced en dash, TeX `---` and ` -- `) | 0, or the rate of the writer's sample | the author's rule; upstream pattern 8 |
| any one stock frame of T7 | about 15 | a 25,000-word methods chapter after a de-semicolon pass |
| essay vocabulary (T11) | none: each hit is read | hunted by name |
| a word against a reference corpus | flagged at 3 times the reference rate with at least 5 uses | a book checked against exemplar books |
| a word absent from every reference text and from the whitelist (facts file, bibliography) | listed as imported register, each read | the same book check |
| a word in 6 or more reference texts at over 40 per million | listed as under-used below a quarter of that rate | the same book check, after a pass had removed every "however" |
| sentences over 45 words | each listed for splitting, unless the sample runs long | a book de-slop house list |
| word count after a pass | about 3 to 5 percent longer | 35,000 to 36,274 words on one measured run |

Run the counts before and after the pass and report both. If a pattern's count did not change, the pass did not
reach it.

```bash
python3 <skill>/scripts/frame_density.py draft.tex                          # counts, line numbers, exit 1 over limit
python3 <skill>/scripts/frame_density.py draft.tex --sample own_paper.tex    # 'rather than' at the writer's rate
python3 <skill>/scripts/frame_density.py draft.tex --reference ref/*.txt --whitelist facts.md refs.bib
                                                    # one text per reference file; whitelist = domain terms
```

## Searches that a script or a shell can run

These are BSD-grep safe (macOS) and come from a book gate. Drop whole-line `%` comments first, and inspect
every hit by hand: an epigraph, a quotation or a defined term can legitimately match.

```
em dash            grep -rnE -e '---| -- |—'
not X but Y        grep -rnEi '\bnot\b[^.]{0,120}\bbut\b|\bnot (just|only|merely)\b|, not\b'
filler openers     grep -rnEi '(^|[.!?] )(it is worth noting|importantly|crucially|notably|interestingly|note that)'
in order to        grep -rnEi 'in order to'
self-praise        grep -rnEi '\b(principled|elegant|powerful|seamless|robustly|carefully (designed|chosen|constructed))\b'
slogans            grep -rnEi 'is the (point|design|whole idea)\.|is exactly right\.'
inline semicolon   grep -rnE ';[]})]*[[:blank:]]+[a-z]'
mid-sentence colon grep -rnE ':[]})]*[[:blank:]]+[a-z]' | grep -vE '\\(in|mathbb|mathcal|left|right|sum|prod|mid|colon)\b'
self-narration     grep -rnEi 'this (chapter|section|appendix|file) (is|covers|describes|gives)|below we|is organi[sz]ed as'
future pointers    grep -rnEi 'will (be )?(discuss|describ|present|cover|introduc|explain|show|examin)'
markers            grep -rnE '\[AUTHOR ACTION|TODO|FIXME'
```

To judge whether a pass made things worse, run the same searches on the old and the new file and diff the two
outputs; hits that existed before are not new problems.

## What the module must never do

- **Change a claim's strength.** A caveat with a physical or named cause stays ("accuracy on held-out folds
  only, since all folds come from one hospital"). A bare caveat ("may not generalize") is flagged
  `[AUTHOR ACTION: cause?]`, never deleted and never given an invented cause. Stacked qualifiers are cut only
  where the source does not support the doubt (upstream pattern 9).
- **Change a result.** A weak or mixed result keeps its number and its place. Softening an evaluative word never
  turns a loss into a tie or a tie into a win.
- **Restyle submitted or frozen text.** In a text already submitted, fix punctuation only; rewording belongs in a
  marked revision.
