# Claims, limitations and the facts file

## Bounding a claim

- **Bound the claim in the sentence that makes it.** State the claim, then "whereas" or "while" plus
  the measured counter-fact. A template of the shape: "[Method] ranks first on [condition A]
  and within noise of the best model on [condition B], whereas [comparator class] ranks first only
  on [condition C]."
- **Every caveat has a named physical or methodological cause.** Template: "[The
  measure] establishes [what it shows] rather than [what it does not show], since [named physical
  or methodological cause]." A caveat with no mechanism
  is a mood. Never a bare "may not generalize".
- **Uncertainty is a number, an interval or a missing control, never an adverb.** Hedges attach to
  the number ("roughly halving memory"), not to the sentence. Never stack hedges ("may potentially
  suggest").
- **No straw-man hedges.** "Not a universal replacement" concedes something nobody claimed; state
  the paper's actual result instead.
- **No straw man of the coarser approach.** Claim that your representation keeps the finest
  measured unit and leaves aggregation to the user; do not claim the field's standard unit is
  "wrong".
- **Declare every asymmetry in a comparison, whichever way it cuts, and print the number that
  beats you.** One exemplar paper states "we intentionally made the comparison quite unfair for our
  pipeline"; another opens its results with the competitor's winning scores. An independent
  benchmark that ranks a competitor above you is reported in the results, with its own caveats
  quoted, without claiming the caveats overturn the ranking.
- **Name what a null controls.** "Abundance-controlled", not "degree-controlled", when the degree
  sequence was not controlled. A selected example is "illustrative", never "representative".
- **Claim hygiene for representation-learning results**, from the author's own brief: frozen-encoder
  probing is not zero-shot; name the precedent that already used your objective before writing
  "first"; state the split's true disjointness (sample-disjoint or source-disjoint); no
  pretraining-benefit claim without a matched untrained encoder; untested differences are labeled
  "descriptive"; a mean rank is restricted to "these N tasks and M representations".
- **Verify every "first" before locking the abstract.** List prior work for each part of the claim;
  when every part is occupied, claim the combination only.
- **Name an algorithm by what the code implements.** A method named after a published algorithm
  whose state variables the code lacks was corrected to "resembles X". Paper-versus-code mismatches
  follow the code and are flagged to the author.

## Limitations

Four shapes, all with a cause, each stated once in the paragraph that defines the thing:

| Shape | Example form |
|---|---|
| Bare declarative | "What remains unsolved is the absence of row-level ground truth." |
| Positive first, then the alternative | "recorded rather than imputed" |
| Concede and defend, naming the cost as chosen | "This is a deliberate trade: ..., at the cost of ..." |
| Caveat beside the definition | "an independent validation axis, imperfect on sparse datasets and not treated as ground truth" |

A limitations section opens with one plain sentence ("[Method] is a first step toward [concept], and
several limitations remain."), gives a short concrete list with one cause each, then concrete next
steps. Never apologize, never excuse, never repeat a caveat in another section (once measured: the
same caveats restated three to five times across chapters, which an outside audit flagged as a
machine fingerprint). Delete "honest" and "honestly" always: candor is shown with a mechanism, not
asserted. Limitations come from the paper's own discussion and the author's records, never invented
("for limitations do not come up with new stuff").

## Integrity

Choosing what to lead with is presentation; changing what the records support is misreporting.

- A result that contradicts a claim changes the claim.
- A weak, mixed or negative result goes to the appendix with its number and its diagnosis, never out
  of the record. "A negative result with a clean diagnosis is publishable evidence and it is stronger
  than a specification." Printing the weakest run while a stronger controlled run sits in the logs
  "understates what was achieved and it will look like selective reporting"; report the strongest
  available evidence and the negative result together.
- A reporting threshold (which p values are printed, which runs count as complete) applies to every
  result alike and is stated in the document. Never print one p value and hide its sibling.
- A setting that differs from the default is reported where the result is reported.
- Deleting a number that carries the argument is an honesty defect, not a style choice (one draft
  dropped a negative scaling result while arguing for pretraining).
- A panel or table that does not separate the methods is moved to the caption or appendix with its
  number; its script stays as the source.

When a request asks to leave a result out, write the honest form above and tell the user which rule
applies.

## The facts file

**One file holds every number the document may state.** It is the ledger of allowed values in the
project's `GUARDRAILS.md` (defined in the sibling skill,
`project-structure/references/governing-documents.md`). Template for its sections:
`assets/FACTS_TEMPLATE.md`.

- It names the single source of truth and its date, and an authority order between sources: the
  latest manuscript wins on numbers, the supplement wins on procedure. Where a source carries a
  placeholder, nothing from that passage may be quoted. Conflicts across the author's own sources:
  "Do not average them and do not pick one silently. Use the manuscript value where one exists,
  otherwise mark it."
- **"Numbers that appear nowhere are not hedged; they are deleted."**
- Every entry carries value, unit, comparator, source location and status tag.
- **The Retired list** holds every superseded value and every renamed or removed name, "delete on
  sight". `prose_qa.py --facts GUARDRAILS.md` fails on any of them. One book kept shipping a scoreboard
  from an earlier scoring run until the retired values were grepped.
- Attribution is copied verbatim from the published contribution statement: "described, never
  claimed". A misattributed contribution in one guardrail file was caught only by that verbatim
  copy.
- Superseded clauses stay as record, marked "not in force".
- Hard constraints live in this file, apart from style. "If you must break a guardrail to make
  progress, stop and flag it. Do not break one silently."
- Read the code before describing the method: a "learned tree" in one draft was a fixed one.
- When a published number and the text disagree, settle it from the analysis code, report the
  code-derived value, and flag the discrepancy.
- Match every number in a results section against its source before hand-over.
- **A diagnostic is not a result.** A number from a sanity check, a development run or a probe of the
  pipeline is tagged `diagnostic` in the facts file, never quoted as evidence for a claim, and a
  figure that shows one says so in its caption ("Diagnostic: ...").
- **Keep the raw text of every source beside the facts file** (`writing/sources/`): one numbered
  brief per source or topic, text conversions of the manuscripts, the bibliography key list. Mine
  talk decks for argument order: a formulation repeated on three consecutive slides is how the author
  fixed it. A narrative the author dictated is stored verbatim and treated as "binding content, not
  binding wording"; record every departure from it with its reason.

### A new version of the manuscript

1. Convert it to text and store it beside the facts file.
2. Write a delta note: source file and timestamp, "read in full" with the date, old value to new
   value ("use X"), removed items ("GONE. Do not use them."), placeholder paragraphs ("NOTHING FROM
   THAT PARAGRAPH MAY BE QUOTED").
3. Update the scoreboard and extend the Retired list the same day.
4. Apply old to new inside the existing sentences, one sentence at a time, logged per file
   (`references/intake-and-revision.md`). Verify with `drift.py new --max-new-numbers N`, where N is
   the count of values meant to change.

## Citations

- Cite every claim at the claim. A method or platform citation comes right after its name, not at
  the end of the sentence.
- One fundamental source per claim, the origin rather than a review citing it; never a review as the
  source of a fact. Two sources for one claim means one is decoration. No clumps
  (`prose_qa.py` warns on three or more keys in one command).
- **No invented citation.** A missing key is written `\citep{NEEDS_CITATION_shortdesc}`, which fails
  the gate; "a fabricated key does not fail anything". "Prefer omission to a hedge, and a hedge to a
  fabrication." Anything only the author can resolve is `[AUTHOR ACTION: ...]`.
- Resolve keys by title and author, never by key name: an absent key is as likely to be a work
  already cited under another key as a new one (nine of 28 absent keys in one package were
  duplicates).
- Verify entries against Crossref or the publisher by DOI. Signatures of scraped citations: a free
  superseded edition, a claim that outruns the source, a key year that contradicts the entry, a
  preprint title on a published record, truncated author lists, placeholder pages, wrong first names.
  Record what could not be verified rather than filling it.
- **Read a quoted sentence in the paper it is attributed to before repeating it.** One sentence that
  circulated in search summaries, attributed to a benchmark paper, was not in that paper. Record the
  absence in the facts file ("not in [source], checked [date]") so the next pass does not add it
  back.
- Never cite your own unpublished work as evidence. State its status in words ("under review at
  [venue]"); cite public own work only for the work itself, a figure source or a release.
- Content comes only from the author's papers, records and written brief. An external benchmark
  that leaked in from an older draft was read by the author as invented.
