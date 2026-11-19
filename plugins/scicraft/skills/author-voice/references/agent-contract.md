# The contract for agents that touch an author's prose

Any helper that edits an author's text (a subagent, a fan-out, a script that rewrites, another model) works under
a written contract. Without one, each helper writes in its own voice, and the sum reads as "a bag of words".

## What happened without it

- A first fan-out of four editors over the author's prose was stopped by the author the same morning.
- Twelve restructuring editors produced "a bag of words", then "butchered" chapters.
- Paraphrase agents doubled chapter lengths (one block about 33,000 words against a 40 to 60 page target).
- Word caps added to stop that made agents cut the author's own sentences: one chapter's kept-verbatim share fell
  from 73 % to 46 %.
- Usage limits killed 9 to 12 agents mid-edit four times.
- Auditors argued for printing a borderline statistic and for a sentence the author had banned; the agent kept both
  and "flagged" them. The author: "I told you many many times in the md file."
- Proofreaders checked facts and references through three rounds and passed sentences the author then caught as
  machine-made in minutes.

The record shows two positions over time: fan-outs over the prose banned outright, and later allowed under
contracts and drift gates. The rule here keeps both: ask first; if the author agrees, run it on a named file under
this contract.

## The contract

1. **Baseline.** The author's latest text, copied to a snapshot before any agent starts. Every agent is told the
   snapshot path and that it is the restore point; agents also back up their own input files.
2. **Rules file.** Every never, always and do not from the author's notes, given to every agent as binding. When an
   audit conflicts with a rule, the rule wins and the item is dropped, not kept while asking.
3. **Scope.** One agent per file. The deliverable and the files it may touch are named; everything else is
   read-only.
4. **Edits as a layer.** Each change is an old to new pair that must match exactly once, applied by a script in
   order, logged with its reason and, for a fact, its source quote. Deleting an entry and re-applying restores the
   original.
5. **Drift gate.** At least 80 % of the author's sentences same or near, at most 10 % lost, each lost sentence
   logged with its reason (a repeat within the section, a stage direction):

```bash
python3 scripts/drift_gate.py _snapshots/r5/chapters chapters --min-kept 0.80 --max-lost 0.10 --allow-numbers 0.84,0.86
```

6. **Word caps with a drift floor.** A cap alone forces the cuts into the author's sentences.
7. **Invariants.** The multiset of numeric tokens is unchanged except the updates listed; label and citation sets
   are unchanged in both directions; numbered equations keep their count; there are no duplicate sentences; the
   build has zero undefined references. A trim adds no sentence and no number except a connective of at most 8
   words, logged with its line.
8. **Expected size.** A cut pass removes 15 to 25 % of words with the fact set unchanged. A de-slop pass grows a
   manuscript 3 to 5 %; one measured run went from 35,000 to 36,274 words and surfaced four factual errors. If a
   de-slop pass shrank the text, facts were lost.
9. **Report.** Words before and after, gate result, drift, files touched, log path, and numbered questions for the
   author instead of guesses.

## Audit briefs

An audit finds errors; it does not restyle. The brief that worked after the rejected rebuild:

> This is a final polish. Do NOT propose a rebuild, a new structure, new sections or a new style. Report only
> errors of fact, number, pointer and limit, each as ORIGINAL / REPLACE / WHY, where ORIGINAL occurs exactly once in
> the text.

Give fresh readers disjoint slices, verify that each ORIGINAL occurs exactly once, and apply the accepted
replacements by script. Readers on slices miss sentences about the document itself, so read the whole text once
yourself.

Run voice as its own pass, separate from facts. Sequence audits on a block after its editors finish, so nothing
overwrites anything, and never let auditors run on a text that is still changing (in the rejected rebuild,
auditors reported on versions that had already been replaced).

## Relays

The author keeps typing while agents run; one session had about 25 mid-turn corrections. Relay each one verbatim:

> Addition from the author, verbatim: "...". For your file this means: ...

For a fundamental change, stop the agent and relaunch it with the new contract. Stop reviewers that a restructure
has made stale.

## Recovery

When agents die mid-task (usage limits, a crash), their partial outputs are on disk. Resume each with a message
that says where it stopped ("Continue exactly where you stopped; you were about to ..."), check each file's state
against the snapshot with `drift_gate.py`, and keep a short continuation inventory (task, state, open author
decisions) so a new session can pick up. Smaller waves lose less.
