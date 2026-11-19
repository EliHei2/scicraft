# Check before posting: the proofread loop and the other readers

The standing demand: "when you give me the thing there should be 0 discrepancy or bug or AI pattern, so really make
sure to run the agent again and again until 0 discrepancy is detected, and make the agent really impartial, and a
bit adversarial. do not fixate on AI ... and focus on human psychology and reviewer psychology".

## The zero-discrepancy loop

1. **Snapshot** into a fresh folder `proofN/`: the built PDF, its `pdftotext -layout` text with ruler line numbers,
   the replies, the reviews verbatim, the submitted paper's text, `RULES_AND_FACTS.md`. Record the sha256 of each
   file in the brief. The text must not move under the reader: in the rejected rebuild, auditors kept reporting on
   versions that had already changed.
2. **One fresh agent per round**, on the strongest model available, with `assets/briefs/proofread_brief.md`: checks
   A (every point answered, part by part), B (every number, table, figure, appendix and line range at the cited
   place), C (the paper against itself on revised pages), D (only quotable items a human reviewer would hold against
   the authors), E (slogan sentences, "compared to the other N minus 1" constructions, tangents: three rounds
   without check E let them through). Out of scope: author choices, requests for more disclosure, new experiments, framing and tone.
3. **Fix, rebuild, new agent.** Round 2 is briefed "a second round on a corrected version, so a short report is
   fine"; round 3 "a confirming round ... Do not pad, and do not re-raise the excluded items below."
4. **Gate: zero findings.** About 15 minutes per round, run in the background while packaging. This loop runs until
   a round is clean while the agent writes the text. On the author's polished draft, one focused audit per round with
   the no-rebuild brief (see `references/process.md`). The sibling `qc` skill owns the loop in general.

**The scope includes the neighbors of every change.** Give the reader the unchanged captions and sentences next to
every changed passage along with the marked text. In the source work an untouched caption still claimed rows at two
training lengths after every row had moved to one, and another said "the same checkpoint" for sections that each
had their own. When the paper gives a count two ways, settle it by arithmetic on numbers the paper prints (a total
parameter count divided by the count per unit) before choosing the wording.

What the rounds found in the source work:
- round 1: a citation on the wrong sentence; a "full ranking" promised in the main text and absent from the
  appendix; a count that did not add up; main text and appendix naming different tests; a caption not naming a
  dashed line; a table cited for a number it does not hold; one target with two names; an italic unit;
- round 2: 15 items, mostly bold leads claiming more than their lines showed, and one partial answer found by
  recomputing every rank from the printed table;
- round 3: one grammar slip and six one-word last lines.

**If the author asks for the package mid-loop**, give the current build at once, say it is not final, and put later
fixes in the same folder under the same names.

## Fact check

For a high-stakes text (the note to the chair, a reply with many numbers) add one fact-check agent with
`assets/briefs/factcheck_brief.md`: every statement CONFIRMED, WRONG, IMPRECISE or UNVERIFIABLE, ranks recomputed by
script from the printed table, true replacement wording for each imprecise item. Yields in the source work: 87
statements with 0 wrong and 10 imprecise; 140 statements with 1 wrong; 107 statements with 0 wrong at a later gate.
The confidentiality line goes in every brief: work only from local files, no web search or fetch, nothing sent to
an external service.

## Reader simulations

Before a round is sent, two simulated readers with `assets/briefs/reader_sim_brief.md`:
- the reviewer who rated lowest, with a language model at hand and the wish to keep the score: objections an area
  chair would agree with, a verdict per original point, the rejoinder they could post, what would make them dig in
  (their rating read back to them in public, flat corrections, significance offered where they asked about size);
- the area chair: the 30-second reading of the general response, phrases of the note to the chair that fail when checked, the
  meta-review sentence.

The red-team rejoinder is a test of the draft. The simulations found stale line references and a juxtaposition that
implied a causal claim the paper disclaims.

## The voice pass

Proofreaders check facts and references, not voice. Three rounds passed a sentence comparing each method "with the other N
minus 1", a slogan ("With X, Y and Z fixed, the model matters") and a tangent; the author caught all three. Give voice its own pass:

- run `check_replies.py` and `rev_passages.py` (punctuation and banned terms);
- run the `humanizer` skill on what you composed, then diff that no claim changed;
- read the final text yourself, start to end, as the reviewer reading it.

## Vetting findings

Every finding is checked before it is applied:

- recheck disputed numbers against the records yourself;
- check each suggested edit against `RULES_AND_FACTS.md`; when an audit conflicts with a rule the author repeated,
  the rule wins, and the conflict is reported to the author in one line (an auditor that argued for printing a
  borderline p value the author had banned, and one that judged a sentence on a competitor's lead harmless, were
  both wrong for this author);
- decline a finding that is wrong, with the reason (the unrounded values decide a sort when the caption says so);
- apply accepted fixes by script, as exact replacements that each assert one match, then rebuild and recheck length
  and page budget.

## Saying what was checked

Every send says which checks cover this exact build and which an earlier one: "The adversarial audit ran on an
earlier build; I checked the sentences added since against the paper and the sources myself." Never call a gate
passed while it is still running.
