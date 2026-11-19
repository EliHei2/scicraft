# The design brief and the literature digests

Template: `assets/DESIGN_BRIEF_TEMPLATE.md` and `assets/LITERATURE_DIGEST_TEMPLATE.md`.

## The brief

**Record the lead's questions in their own structure.** The design round in the source work opened its
decisions document with the lead's three questions, "paraphrased only in structure": are we using whatever we
can; do we keep the real borders of the data; what guarantees the model does a good job at that. The decision
record later answered them one by one, in the same order. When the questions are reworded, the round answers
the agent's version of them, and one of the lead's ideas was nearly lost that way (the shared preamble
mis-stated it and six agents confirmed the mis-statement).

**Quote, date and rank the lead's messages.** When the lead writes a governing brief, it overrides earlier
rules. Keep a decisions log against it (D1 to Dn) and never discard earlier work. A spec generated in another
chat is a draft plan: in the tabular side project it was wrong about a baseline's features, about whether
pretrained weights existed (five released checkpoints did), and about a 49-of-51 overlap between two
benchmarks. Save such inputs verbatim, mark which one is the goal, and record the reconciliation.

**Hard constraints are the lead's, and they stay.** Examples of the kind seen: "stay inside this anti-collapse
family", "this baseline component stays", "no k-means anywhere", "the model must not be permutation invariant",
"use gene symbols, not database identifiers". Write them into the brief, have every agent read them, and do not
reintroduce a rejected option. When evidence contradicts one, argue it in one paragraph and wait for the lead.
A standing operator decision is marked "do not re-litigate".

**Separate fixed, free and careful.** A three-column table: what is fixed (the method as published or shipped),
what is a free hyperparameter, and what needs care (a loss change or a large architectural change). The lead's
correction that produced it: every added loss term is an auxiliary regularizer, disclosed with its weight and an
ablation row, never a replacement; size is a free hyperparameter, and size is not a repair.

**Scope is a conjunction.** A method framed on a generic noun collided with a crowded neighboring field and
invited a benchmark the work did not target. The scope that held was the conjunction of properties the method
needs ([property A], [property B], [the deliverable]). For a tabular foundation model the same move is:
heterogeneous columns, many small tables, missing values, in-context prediction as the deliverable. The home dataset is one representative instance.

**Name the deliverable and its forward path.** The decision record in the source round found that the shipped
prediction path returned a normalized leaf output and never called the hierarchical component, so every fix to
that component could not move the deliverable. The brief names the deliverable and the code path that reads it,
so every proposal can be checked against it.

**Surface a semantic change; do not make it.** Audit items that alter training behavior or semantics were left
for the lead with a written trade-off. Two scope choices (a group size and a crop size) were surfaced and not
changed. A reversal of a dependency rule was the lead's informed choice through an explicit options prompt.

## Literature digests of methods known to work

**Anchor every design axis in what working systems do.** The lead's standard: "make sure we're really testing
the newest top techniques in pre-training/foundation models, but from frontier labs and top ML gurus papers not
random. sth that's working". Weight recent releases higher. For each axis (masking, anti-collapse, readout,
positional encoding, scaling, aggregation) find what the top two or three working models do, with citations,
then adopt, adapt or reject with a reason. Precedent is the default and a deviation needs its reason: one design
in the source work was "the outlier", the only one stacking three mechanisms that no working system combined,
and it was the one that failed.

**One topic per digest agent.** Each digest carries:

1. A header naming the agent, the repository and commit, the date, and the primary sources as arXiv IDs.
2. Verbatim quotes extracted from the paper's HTML, with the paper's own section and equation numbers.
3. Probes that import the repository's own functions by file path, so the measurement is of this code.
4. A bottom-line table: what, mechanism, role here, the paper's measured effect with its table or figure.
5. "Corrections to the brief", when the brief got something wrong.
6. The decision, with its exact code shape.
7. "What it should do, so it can be falsified": the before and after on a probe through the deliverable.
8. "Arguing against my own recommendation": the strongest objection. The one that mattered in the source round:
   a mechanism designed to keep a property, applied to a model that never had the property to keep.
9. The runner-up and why it lost.
10. A claim ledger with a tag per claim.

**Tag every external fact.** [V] verified (source opened on a date, link given), [U] unverified, [C] computed
from a downloaded file with the method stated. Helper agents use the same rules and the lead agent spot-checks
their key claims. Citations written from memory are ideas to verify before any manuscript. One research pass
recorded "62/62 citations verified real"; another round found a celebrated citation that did not exist and
removed it after searching the paper and the code.

**Released code over the paper table, and say so.** When a reference implementation differs from its paper,
choose the code, state the parameter count, and record the deviation. A library changed a prior's default in a
change that was absent from its changelog; another produced output that depended on the interpreter's hash seed.
Both were found only by running the installed code. Keep a verified-API notes file: package version and
signature, gotchas found by running the code, measured runtimes, deviations from papers.

**Check what you reimplement against the authors' code.** A knowledge base and a project instruction file both
described a regularizer with the wrong mathematics; the authors' repository had the actual test and its
parameters. Record them in a reference note and correct the knowledge base in place (the knowledge base is
defined in the sibling skill, `project-structure/references/knowledge-base.md`).

**Answer a question by literature only when the literature answers it.** The source decisions document had a
section "answered by the literature reports, not by a build item": a precedent model checked and found not to be
the same kind of model, and a code comment's numeric claim found wrong by a factor of the square root of d minus
one. Those questions closed without spending a run.
