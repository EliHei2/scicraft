# GUIDELINES

Owns one question: how work is normally done in {{NAME}}, and what "done" means. These are conventions. Each can be overridden with the reason written where the override happens: a comment in the code, or a row in `DECISIONS.md`. The rules that may never be broken are in `GUARDRAILS.md`.

The bar: [one sentence naming the standard a reviewer would apply, for example that new code reads like the stable modules it sits beside].

## 1. Files and size

- Keep a file under about 200 lines of code. When a file passes that, simplify the design before splitting it.
- One responsibility per file. The tree in the index file is the target; add a file only for a new responsibility.

## 2. Style

- [Type hints on public signatures; configs as dataclasses; no global state.]
- Docstrings give the reason for a choice and say what the choice does not fix.
- [The naming rules of this project: one name per thing, and the names that must not change.]

## 3. What not to write

- No dead code, no speculative flag, no config field that nothing reads. No commented-out code.
- [What is out for now, and the stage that brings it in.]

## 4. Defaults

- [Numerics, seeds and logging: the defaults a new script starts from.] A default with a safe range is documented in `DESIGN.md`.

## 5. Working flow

- How a unit of work goes: `guidelines/WORKFLOW.md`. What every run writes, where the project has the file: `guidelines/RESULTS.md`.
- Shared guidelines are folded in batches, when the lead says "update docs". Until then a ledger row carries `Synced` at `-`.
- A change to `NARRATIVE.md`, `GOALS.md` or `GUARDRAILS.md` is made in the same commit as the decision behind it.
- Commits, branches and reviews: [this project's rules].

## 6. Definition of done

1. [The code compiles and imports with no side effects.]
2. [The fast tests pass.]
3. The run it feeds has a manifest and a `RUN_MAP.md` row.
4. Every guardrail was checked: pass, fail or not applicable, with the evidence.
5. `STATUS.md` carries today's date.
