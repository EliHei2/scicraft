# Framing and terms

Contents: write around the general data type; claims and novelty; one name per thing; the terminology box;
code names and human names; the reader level.

## Write around the general data type

A method paper for an ML venue is framed as representation learning on an abstract data type. The home
application is one representative instance among peers.

- **Define the data type first** by the conjunction of properties that makes it hard. For point-set work:
  points that are irregular in space, carry labels and are nested at several scales. For a tabular model: heterogeneous columns, no natural order of rows or columns, sizes from
  ten rows to ten million.
- **Then say why current model families fail on it** (fixed scale, no gain from more data or compute,
  a fixed serialization), then the method, and only then the domain example.
- **Domain vocabulary only inside the domain section.** The author asked for the home domain to be toned down
  to one example among peers. In the general sections use point or element, label or feature id, region or
  group. Figures follow the same rule: an architecture figure carries no domain objects.
- **"A representative instance", never "the extreme case"**, for the home domain.
- **Benchmark claims only where results exist.** Domains you did not benchmark are discussed, not claimed.
  When a line of work could become a general paper and an applied paper, decide which claim each owns and
  archive the other draft instead of running two half-papers.
- **Do not straw-man the coarser unit.** Claim that the representation keeps the finest resolution and
  leaves aggregation to the user; never that the abstraction the field uses is wrong. A draft sentence that
  called the field's usual unit the wrong scale was struck by the author. The claim kept was that the
  representation reaches the finest unit available.

The same rule applies to a tabular foundation model: frame on the data type (tables), not on the benchmark
suite or the one domain the authors care about.

## Claims and novelty

- State concrete novelties ("readout at any level of granularity", "linear cost in the number of rows"),
  each tied to the component that provides it.
- When every conjunct of the claim has prior work, claim the conjunction.
- Verify every "first" before the abstract is locked. "first" when it is first: the author rejected "top
  three" for a method that ranked first. Never "first at everything" when it is second somewhere.
- A result that contradicts a claim changes the claim.
- **Theory goes to the appendix unless the main argument needs it.** The main text states the result and
  points to the proof. A separation or optimality result without a complete proof is stated as a conjecture,
  never as a theorem. Every value in a theorem's worked example (a witness pair, a constant) comes from a
  computation that was run: one theorem witness with made-up values was deleted on sight.

## One name per thing

- **The field's established term over an invented one.** Before introducing a term, search the submitted
  text and the literature; ask the author to choose when two are plausible, with the recommendation first
  and its reason ("the submitted paper already uses it"). One coined term ("[a coined term]") was replaced
  by the plain description the field uses, after two rounds.
- **Define once, use everywhere**: prose, captions, table rows, figure labels, replies, the website.
- **A rename reaches every variant.** After a rename, grep every spelling and derived form; a half-converted
  sweep is worse than none. A demoted variant loses its old name everywhere "as if it never existed".
- **Choose the precise term per sentence** when a word is banned; never swap one replacement in everywhere.
- **The coined concept of the paper in italic at its introduction**, in full every time after. The author
  asked for the coined term in full ("not field" alone), set in italic, "we want to establish this name".
- **Use the notation of the latest manuscript** in every derived artifact.

## The terminology box

For readers from ML, define the application's terms once in a box: one bold term, one sentence, at most six
entries, placed before the first use. The box replaces scattered parenthetical glosses. Shape in
`shapes.md`, environment in `assets/ml_addon.tex`.

## Code names and human names

Keep a glossary that maps code identifiers to paper terms, and grep the manuscript for the code side before
any hand-over:

| In code or notes | In the paper |
|---|---|
| `A3`, `A4`, `r2`, `v4` | the model size or a descriptive name ("the 12M model") |
| `w/o_mask` | "−masking" |
| `held_out` | "validation" ("val" in tables for general readers) |
| `seed` tokens | a human name for what they are ("parent tokens") |
| `L_extra` | the plain quantity the term measures |

The code name stays stable in the repository; the paper name is chosen once and applied in the paper. A
conceptually new model is never given a version number.

## The reader level

Decide the reader first. Co-author documents do not recap the concept ("this is to our co-authors, we don't
have to recap everything"). Reviewer-facing and paper text define everything ("don't assume they know
things, define things!").
