# Triage, regression checks and the next round

## Surgical or semantic

The question that decides it: does the change alter what the artifact does or claims? If yes, it is semantic and
the author decides, however obviously right it looks. In the code audits, items that "alter training
behavior/semantics" were "left for author decision"; parameter choices were "surfaced to user, NOT unilaterally
changed"; an override of a guardrail was "awaiting go-ahead". A guardrail is a rule in the project's
`GUARDRAILS.md` (defined in the sibling skill, `project-structure/references/governing-documents.md`); overriding
one is always semantic.

| Surgical (apply) | Semantic (author) |
|---|---|
| crash with an unambiguous fix | a change to the loss, the sampling, the schedule or any default |
| misspelled key, dead guard made live | a change to the evaluation protocol or the metric of record |
| typo, broken reference, wrong label | rewording that changes a claim's strength or scope |
| number in the text differing from its table (fix the text to the table) | which of two conflicting sources is right |
| house-ban violation in text the coordinator wrote | style in the author's own sentences |
| missing citation for a fact, with the source verified | a credit not confirmed by the author |
| | deleting the author's content, models or figures |

The author's decisions override audits that recommend deleting things that work: an audit suggested deleting a set
of earlier models, and the author kept them ("they were good models, don't lose them").

## The author's rules beat auditor advice

Vet each finding against `RULES.md` before triage. A finding that asks for something the author has ruled out is
declined, with the rule as the reason, and is not "flagged" back to the author as an open question. In the rejected
rebuild, the coordinator kept two auditor-backed items the author had excluded and flagged them; the author's
strategy was lost under auditor preferences.

Where a rule is applied literally beyond its intent (a license rule that deleted a software license statement),
surface it as "one call for you".

## Honest triage

Findings about honesty are not open to taste. A claim stronger than the records, a number that differs from its
source, an absolute word with a counterexample in the document itself (a text that said "no overlap" while its
appendix listed two shared items, an illustrative case), a weak result that undercuts the headline: each goes to the author with
the evidence and the defensible replacement. The author chooses the wording; the audit never proposes hiding a
result. A table copied into a book was re-sliced so that the tasks where the method won disappeared; the fix was
the paper's single table and the paper's own wording everywhere. `integrity-audit` covers this in full.

## The decisions file

`assets/author_decisions.md`: one section per kind (credits to confirm, number mismatches between figure and text,
license permissions, semantic changes, places where the author's final text undoes an audit fix). Each item gives
the location, the finding, the evidence, the options and the cost of each. Offer the minimal neutral wording as an
option, never as applied text.

## Regression checks

### Code

1. `py_compile` and import of every touched module.
2. A synthetic end-to-end canary on real framework code: forward and backward, the EMA or optimizer step, every
   architecture builds, byte-exact equivalence tests for refactors.
3. Guard tests that each fire on a failing input. For each new test, revert its fix and confirm the test goes red;
   two tests were decoration until this check.
4. Canary numbers kept in the audit record across rounds (for example an architecture gap, a loss before and after,
   a guard delta of zero), so a regression shows as a changed number.
5. A one-job smoke on the target hardware before the expensive sweep, when the audit touched anything that cannot
   be tested locally.

### Documents

1. Build with zero errors, zero undefined references and citations, zero overfull boxes, zero "float too large",
   page count explained, all fonts embedded (`latex-typesetting` has the gates).
2. Render the changed pages and look at them. Visual checks caught text printing over a caption and figures
   drifting to the end of a chapter.
3. Run the mechanical checks (banned patterns, bundled citations, undefined keys) on the old and the new version
   and diff the outputs; pre-existing flags are fine, new ones are regressions.
4. Audit merged text against the previous verified version. A merge weakened "not evaluated" to "no advantage
   established", reversed a prediction direction and lost caveats; only an auditor of the merged text caught it.
5. Check the length against the round's target; audit rounds add words.

### Figures

Re-render, then one final verifier for regressions after the batch of fixes. Keep-as-is guards list the deliberate
choices the next loop must not undo.

## The next round

1. Read the record: lenses run, counts, refuted list, keep-as-is guards, the completeness critic's gap list.
2. Pick lenses for what was not covered. A second code audit aimed "at what the prior two audits did NOT cover:
   efficiency, minimality, and comparison to WORKING foundation models". In the de-slop of a paper, three readers
   with different lenses found what two earlier passes missed.
3. Fresh agents, fresh snapshot, the refuted list attached as "do not re-raise".
4. For a final deliverable, loop one fresh agent per round until a round finds nothing. If the user asks for the
   files mid-loop, hand over the current build marked "not final", and put later fixes in the same folder under the
   same names.
5. Stop at a clean round, at the budget, or (suggested, not yet tested in real work) after two rounds that find
   only minor items. Write the stop reason in the record.
