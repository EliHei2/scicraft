---
name: paper-code-parity
description: Keeps a paper and its code in agreement while both change, and produces a paper-to-code map, tests that assert the paper's constants, a generated macros file and tables for every reported number with a preflight that fails when one is stale, a hash-checked contract file between repositories, and a parity status record when a project reproduces someone else's paper. Use it whenever code implements a written method or numbers move from results into a paper, even unnamed: "make sure the code matches the paper", "implement eq. 3 exactly as in the methods", "the numbers in the text are stale", "the table doesn't match the results", "camera-ready is Friday, regenerate everything", "we reimplemented the baseline, what differs from their paper". Holds what agents get wrong: following the paper and flagging typos instead of coding them, tests that bite, numbers never typed by hand, pending instead of estimated. Prefer integrity-audit to audit finished claims, research-code for general code structure.
---

# paper-code-parity

How to keep a method paper and its code saying the same thing while both are still changing: the paper is the
specification, every equation and constant is tied to code and a test, and every number in the text, the captions
and the tables is generated from the result records, so none can go stale. Distilled from a year of one
researcher's work on method papers, a benchmark and a reproduction study. The author's standard: "If it can't regenerate from raw data with one
command, it's an assertion, not a finding."

> **PRIME DIRECTIVE: no number, constant or equation exists in only one place by hand.** Each paper statement
> has a row in the paper map that names its code and its test; each number in the text is a macro or an assert
> generated from a record, and the build fails when any of them disagree.

Three failures cost the most time. Guard against them from the first minute:

1. **Silent drift between the equation and the code.** A loss term averaged over views where the paper's
   equation summed them changed the training dynamics; it surfaced weeks later, from trained models that
   scored worse than expected. Every convention an equation hides
   gets written into the map and a test (sections 1 and 3).
2. **Numbers typed by hand.** Hand-copied counts drifted twice in two days; in a rebuttal, stale ranks and scores
   from old drafts came back round after round until a build-time check caught them (section 5).
3. **Fixing the wrong side.** Coding a paper's typo to look consistent, or quietly rewording the paper to match a
   bug, hides the disagreement from the authors. The protocol in section 2 keeps the code on the intended method
   and puts every disagreement in front of them.

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The specification**: the paper's TeX source (a PDF if nothing else), with its version and date. For a
  reproduction, the reproduced papers and their released code, with commits and licenses.
- **The code and what it actually runs**: the config files and their loader, the entry points, the test suite,
  the released commit if one exists.
- **The records**: where result files land, which are frozen, which job produced each one.
- **What exists already**: a paper map, a provenance log, a vocabulary module, generated tables, a build script.
  Extend them; do not start a second system beside them.
- **Who owns what**: which side is the specification for each part (your own methods text, or someone else's
  released code), which repository is upstream of which, and who decides the paper's wording.

Ask the user only: which document version is the specification, whether the code may be changed or only audited,
and the deadline. Then say in one line what you will produce (map, tests, macros, tables, contract check, status
record) and start with the map.

## 1. The paper is the specification: build the paper map

`docs/PAPER_MAP.md`, from `assets/PAPER_MAP.md`. Detail and the full procedure: `references/paper-map.md`.

- **One row per statement of the methods**, in the paper's section order: equation (in its own symbols, with its
  number), constant, stated rule, stated procedure. Columns: paper, code (`module.function`), setting (config key
  and value), test. A row without a test is an open item.
- **Find the code by running it, not by reading names.** Open the call site and read the value the caller passes;
  a function default the caller overrides is not the value in force. Where prose and the YAML disagree, the YAML and
  the source win (the mask ratio once appeared as four numbers in the docs and one in the code); record each case
  in the corrections table.
- **Write down the conventions an equation hides**: summed or averaged, over which axis, per device or global,
  in which precision. The worst bug in the source project lived in that gap.
- **List the choices the paper leaves open** separately (graph direction, widths outside the table, init,
  schedules), each with what the code does and why.
- **List the ablation hooks**: every config switch the experiments section uses. Each loads and trains one step in
  CI (section 3).
- **Keep it current "when either side moves"**: an equation, constant or default change updates the map in the
  same commit, with a dated row and the receipt file that measured the effect.

## 2. When the paper and the code disagree

Decide which side is the specification and write it at the top of the map. For your own paper it is the methods
text. For someone else's paper with released code, see section 8.

| What you find | Do |
|---|---|
| the code does not do what the paper states, and the paper is right | **Follow the paper**: fix the code, add a dated map row with the receipt, add the test that would have caught it and see it fail on the old code |
| the paper has a typo or contradicts itself | **Keep the code on the intended method and report the typo.** Never code the typo, never silently reword the paper. Write a numbered paper edit (location, what the code does, proposed sentence) and tell the authors |
| the code moved ahead of the paper on purpose | Mark the row **paper edit: [what the text must say]** and list it; the paper is updated before submission, or the change is reverted |
| the paper is silent | A row under "choices the paper leaves open" |
| a paper constant looks wrong | Measure the quantity the argument rests on before moving it; change defaults only through the plan of record plus a test |

- **The wording of the paper is the authors' decision.** The author put it plainly: the code follows the method,
  and "I can adjust text if you come up with things that are a tad different from text". Propose sentences; do
  not edit the paper's text unless asked.
- **A finding that weakens a claim stays on the record** as a dated open revision item with its numbers, and
  changes the claim. It is never dropped because it is inconvenient.
- **Before submission, audit the methods text against the code** line by line, report what is wrong before
  editing, and when one fact is wrong audit the whole document (`references/paper-map.md`, last section; the full
  audit is the `integrity-audit` skill).

## 3. Tests that assert what the paper states

Detail: `references/paper-tests.md`. Template: `assets/example/test_paper_constants.py`.

- **Every constant of the hyperparameter table is asserted** on the config the code actually loads, in one dict
  that cites the table and the map row.
- **Derived rules are recomputed in the test** from their inputs, never copied as a second literal.
- **Test the shipped expression, never a copy of it.** "If a test has to freeze the thing that varies in
  production, it is testing a different program."
- **A test counts only after it was seen failing**: change the constant or revert the fix, watch it go red,
  restore. Two tests added in one tidy-up passed either way. "A test that does not bite is worse than none."
- **Every ablation config loads, builds and trains one real step in CI**: "a config that cannot train cannot be
  merged". Five arm configs that differed only in comments built the identical network until this ran.
- **Name tests as claims** (`test_per_view_backward_equals_the_joint_objective`), and rename a test when its claim
  is overturned.
- **New mechanisms are switches whose default is the current behavior**, with an equivalence test that the default
  path is bit-identical, so a published row stays reproducible.
- **A reproduced published number is a self-test** at the printed precision.

## 4. One source of truth for vocabulary and settings

Detail: `references/contracts-and-vocabulary.md`.

- **Every id, display label, direction, sweep grid and threshold comes from one module** (`vocab.py` or a JSON the
  code loads). Runners import it; human-readable maps (`METHOD_MAP.md`) are generated views of it.
- **Display names are a dict applied by the renderer.** Internal ids, run names and hardware words never print.
- **The manuscript's terminology wins** (manuscript, then main figures, then tables, then supplement). Never coin a
  term or a symbol the paper does not use.
- **Settings live only in the config**, with the resolved config and the code commit echoed into every run log and
  result record. The paper map, README and methods point to the config; they never restate a value as the
  authority.

## 5. Numbers in prose come from the records

Detail: `references/generated-numbers.md`. Scripts are standard-library Python 3.9 or later.

- **Every number in the text is a macro** in `tables/macros.tex`, generated by `scripts/gen_macros.py` from a JSON
  spec that names the record file and key path for each macro. The text reads `\AccOurs{} over \NSeeds{} seeds`.
- **Numbers stated in words are asserts**: "ranks first", "in 5 of 7 tasks", a rank in a list. Each goes in
  `claims.json` with its record path, value, tolerance and location. Every number added to the text gets a macro
  or an assert in the same edit.
- **The preflight fails the build** when the macros file is stale against the records, edited by hand, or missing
  a macro the text uses, and when a claim is outside its tolerance. It warns on `pending` macros, `[VERIFY]` tags
  and hand-typed decimals or percentages in the prose.
- **A missing record prints `pending`**, visibly, and fills in on the next build with no code change. If a number
  exists nowhere, write `[PENDING: what]`. Never estimate one. `--strict` fails instead, for the final build.
- **When the records move, the text follows.** Never edit a record or a rounding to keep a sentence true; a result
  that contradicts a claim changes the claim.

```bash
S=<skill>/scripts
python3 $S/gen_macros.py --spec macros_spec.json --out tables/macros.tex
python3 $S/check_numbers.py --spec macros_spec.json --macros tables/macros.tex \
    --claims claims.json --tex paper.tex sections/*.tex          # exit 1 on any stale or wrong number
```

House number format, shared by macros and tables: fixed digits, leading zero dropped below 1 (`.812`, `--lead0`
keeps it), true minus `$-$`, signed deltas `$+$.011`, a percentage as its own macro with `"scale": 100`.

## 6. Tables are generated, and captions read generated values

- **Every results table is a fragment written by `scripts/gen_table.py`** from the records, plus a sidecar JSON for
  other renderings (docx, website). No cell is typed.
- **Fragments are self-terminating**: the fragment holds the body rows and ends with `\bottomrule`; the main file
  holds `\toprule`, the heads, `\midrule` and the `\input`. Otherwise TeX Live 2025 stops with "Misplaced
  \noalign" (reproduced while building this skill, pdfTeX 1.40.27).
- **Emphasis follows one rule per column** (`"best": "max"`), applied to every method alike, with the values
  printed.
- **A missing cell reads `pending`.** A comparator's published cell is frozen as published and re-read from its
  record, never re-scored or retyped.
- **Captions are prose**: every number in them is a macro, and they state the interval type, the number of seeds
  or folds, every filter or subset applied, and every non-default setting. Panel scripts assert the invariants of
  what they draw, so a figure cannot disagree with its caption.
- **Figure render parity has its own harness.** This skill covers number parity; a refactor of figure code is
  checked output by output with the render-parity harness of the sibling skill `figure-development`
  (`figure-development/scripts/parity/`).
- **One command rebuilds everything** from the frozen records, re-scoring nothing: figures, macros, tables,
  preflight, LaTeX twice, then a grep of the log for `undefined`, `Misplaced`, `multiply`. A gate reads the log;
  a build once exited 0 with a bibliography-less PDF. `assets/example/build.sh` runs this on toy records.

```bash
python3 $S/gen_table.py --spec table_main.json --out tables/tab_main.tex   # prints the head line for the main file
```

## 7. A contract file between repositories, checked by hash

When results come from one repository and the paper or figures from another:

- **Each repository has one deliverable and one write target.** The upstream deliverable is one long-format table
  (method, dataset, metric, value, interval, with labels and direction), copied byte-identical downstream. The
  source project's contract was one row per method, dataset and metric.
- **A frozen reference copy is tracked**, and every regeneration is checked against it: header, vocabulary, the
  complete grid with no duplicates, and the hash.
- **A legitimate change is recorded, then propagated**: refresh the reference, log the new hash and date in the
  provenance file, refresh the downstream copy deliberately. "Visible drift, never silent."

```bash
python3 $S/verify_contract.py --actual results/aggregate/scoreboard.tsv \
    --reference reference/scoreboard.tsv --vocab vocab.json        # OK / OK_SCHEMA_ONLY / exit 1
```

## 8. Reproducing someone else's paper: the parity record

When the project re-implements published methods, keep `PARITY_STATUS.md` from `assets/PARITY_STATUS.md`. Detail:
`references/reproduction-status.md`.

- **Mark every component R, A or E**: exact reproduction (same procedure, checked against a number the authors
  published or released), approximate reproduction (same idea, documented differences), new extension (in no
  reproduced paper). Infrastructure gets "none".
- **Number the deviations per reproduced paper**: what the paper or its code does, what you do, why, and the
  measured size. A protocol flaw you fixed (a bootstrap before the split that leaks duplicates into the test set),
  a released architecture that differs from the paper's table, a library default changed silently between
  versions, a wrong claim in your own plan: each is a numbered line.
- **Released code over the paper's table** when they differ, because the code made the published numbers; state
  it as a deviation. Without released code, the paper is the specification.
- **Verify before porting**: re-check every asserted fact about the baseline by running the installed code, and
  keep verified API signatures with their versions in the same file.

## 9. Check before anything is handed over

In this order:

1. `check_numbers.py` with `--spec`, `--claims` and `--tex` on every source file: zero failures. Before
   submission add `--fail-on-pending --fail-on-literal`, and `gen_macros.py --strict`.
2. `verify_contract.py` on every contract file: `OK`, or `OK_SCHEMA_ONLY` with the provenance log updated.
3. The test suite, including the paper-constant tests and the one-step run of every ablation config. For each new
   test, the note of when you saw it fail.
4. The full build from a clean folder, and the LaTeX log grep.
5. Read the paper map against the paper once more, section by section: every statement has a row, every row has
   code and a test or is listed as open.
6. Look at the compiled PDF where numbers changed: a `pending` in the abstract, a caption that no longer matches its
   panel, a bolded value that is no longer the best.
7. Report: what was checked and how; every paper edit and typo found, with location and proposed sentence; every
   number that changed between builds and the sentence it sits in; every claim that no longer holds; what was not
   checked (for example, a literal scan run only as warnings, or tests not run because the environment lacks a GPU).

## 10. What was thrown out, and what replaced it

| Thrown out | In the author's words, or their repositories' rules | Replaced by |
|---|---|---|
| numbers copied by hand into prose | "they don't match man", "hand-copied counts drifted twice in two days" | generated blocks and a preflight that fails when stale |
| a figure or table that cannot be rebuilt | "it's an assertion, not a finding" | one command from the frozen records |
| the same metric computed in two places | "these values are not matching at all what we see in figure 2" | one module, one master table, everything reads it |
| a test that froze the varying part | "a test that does not bite is worse than none" | tests on the shipped expression, seen failing first |
| an invented symbol or term | "if we don't have it leave it as is" | the manuscript's terms only |
| a step recomputed instead of read from its record | "do it once and move on" | a registry of canonical runs and records the text reads |
| silent drift of a hand-off file | "visible drift, never silent" | a frozen reference and a hash check |
| trusting the docs over the config | "four different numbers in the docs, one in the code" | the YAML and the source win, with a corrections table |
| an estimate drawn or printed as a value | "never invent or estimate one" | `pending`, filled by the next build |

## Reference files

- `references/paper-map.md`: building the map, the disagreement protocol, paper edits, authority between sources,
  the methods-against-code audit.
- `references/paper-tests.md`: what to assert, how to make a test bite, configuration as one source of truth.
- `references/generated-numbers.md`: records, macros, claims, the preflight, tables, captions, pending values, the
  build order, renames.
- `references/contracts-and-vocabulary.md`: the vocabulary module, display names, the contract file and its
  provenance log, data identity.
- `references/reproduction-status.md`: the R/A/E parity record and the deviations list for reproduced papers.
- `assets/PAPER_MAP.md`, `assets/PARITY_STATUS.md`: templates.
- `assets/example/`: toy records, macro and table specs, claims, a TeX snippet, a contract and its vocabulary, a
  paper-constants test and `build.sh`. Run `S=../../scripts bash build.sh` inside a copy of the folder.
