# {{INDEX}}

{{NAME}}: [one sentence on what this project produces]. The deliverable is [the table, the model, the figure set or the paper]. The standard of work is that every result can be regenerated from tracked code, tracked configs and recorded provenance.

## Read in this order

1. This file.
2. `GOALS.md`: the active short goal, then the long goals and the non-goals.
3. `STATUS.md`: what works, what is blocked, what is next.
4. `GUARDRAILS.md`: what must never happen.
5. The file that owns the question at hand (table in `README.md`): `NARRATIVE.md` before designing or writing for a reader, `GUIDELINES.md` before writing code or prose, `docs/kb/INDEX.md` before any claim about the field.

## Repository contract

```text
{{TREE}}
```

Raw data and run outputs never enter git. Raw stores are read in place through the links in `data/raw/`; anything copied into the project gets a row in `PROVENANCE.md`.

## Pointers

- One row per run: `RUN_MAP.md`
- Every attempt, failures included: `experiments/EXPERIMENTS.md`
- Choices and what they replaced: `DECISIONS.md`
- Every path, set once: `configs/paths.env`
- How a unit of work goes: `guidelines/WORKFLOW.md`
{{EXTRA_POINTERS}}
When two files seem to answer the same question, the owner named in `README.md` wins. `GUARDRAILS.md` wins over every other document.

## Guardrails, by id

Full text, reason and check for each rule: `GUARDRAILS.md`. If this list and that file differ, that file wins.

- **G0** Never write to or delete from a path outside this project's own trees.
- **G1** Code and data never mix.
- **G2** Every path is set once, in `configs/paths.env`.
- **G3** One results root per run profile: config first, manifest last, nothing overwritten.
- **G4** Smoke runs write to `scratch/`.
- **G5** Every copy gets a `PROVENANCE.md` row in the same edit.
- **G6** No number is typed into prose by hand.
- **G7** Failures stay in the log.
- **G8** The laptop writes, the remote computes; `.git` never travels and sync never deletes.
- **G9** [the rule against this method's own failure mode]
- **G10** [the evaluation rule]

## Done checklist

- Every deliverable ticked in `GOALS.md` has the output of its check.
- `RUN_MAP.md` and `PROVENANCE.md` match what is on disk.
- Every run cited anywhere has a `manifest.json`.
- `git status` shows no data, outputs or binaries.
- `STATUS.md` carries today's date.
