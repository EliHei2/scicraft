---
name: research-kickoff
description: Turns an idea, a research brief or a chat-written specification into a verified research plan within days, above all in a field new to the author. Produces a frozen specification with the author's words verbatim and a claim-by-claim verdict table, tagged literature and interface notes with version pins and traps, numbered research questions tied to analyses, a reproduce-first plan and a status file marking each component as exact reproduction, approximation or extension. Use it whenever someone starts a project or enters a new field, even when unnamed: "I generated this plan with ChatGPT, check it", "new project on X, where do I start", "reimplement this paper", "is my port faithful", "what should the first experiment be", "hackathon tomorrow". Holds what agents get wrong: trusting the brief, following the paper over the released code, building before the baseline reproduces, citing an algorithm by the wrong name. Folder layout belongs to project-structure, design critique to research-design-review.
---

# research-kickoff

How to start a research project, above all in a field the author has not worked in, so that the first week builds
on facts. Distilled from a one-day project that entered a new machine-learning subfield from a chat-written plan
and a research brief, from months of self-supervised model work where redesigns were measured against what had
worked, and from manuscript sessions that settled what an algorithm really was. The author is demanding about
evidence: "I don't know if these are facts you say or delusions, do you have proof or just anecdotes?"

> **PRIME DIRECTIVE: nothing in the plan rests on a claim that has not been checked against the primary source,
> and nothing new is built before the published baseline reproduces.** A brief is a list of hypotheses. The
> released code outranks the paper, the paper outranks a summary, and every statement says how it was verified.

Three failures cost the most time. Guard against them from the first minute:

1. **Building on the brief.** A plan written by an online chat said that no pretrained weights existed (five
   checkpoints did), misdescribed a published baseline's features, named the wrong corpora and gave a library
   default that had changed two releases earlier. Each would have shaped the design. The claim table catches them
   before any code (section 2).
2. **Following the paper where the code differs.** A paper gave one architecture and output size; the released
   weights came from another. Only the code's version reproduced the authors' outputs (sections 2 and 4).
3. **Comparing against an unproven reimplementation, or losing the version that worked.** A port is trusted after
   it matches the authors' own outputs, and every redesign is compared with the last good commit (section 4).

## 0. Before starting

Collect by reading, then ask only what is missing, in one message:

- **The inputs**: the idea, the brief, any chat-written plan, follow-up messages, links the author pasted.
- **The papers and code** named in them, and the authors' released artifacts: weights, intermediate outputs,
  result files, logs.
- **The environment**: machine, accelerator, hosted runtime, Python version, what may be installed where.
- **Compute limits and standing rules** (this author: no model training on the CPU; hosted GPU work kept light).
- **Deadline and deliverable**: a one-day sprint ships a picture in 30 minutes; a month-long project ships a plan.
- **What only the author can decide**: license acceptance for gated weights, scope, which part of the inputs is
  the goal.

**Write or check `GOALS.md` with the user before anything is built**: the long goal with a test an outsider can
apply, the one active short goal with its due date, and the non-goals. The file and its parts are defined in the
sibling skill, `project-structure/references/governing-documents.md`; this skill only makes sure the file exists
and that the user has agreed it. The author asked for the governing documents to be "stated exactly what they
are", and a plan without a dated short goal has nothing to be judged against. `scripts/check_kickoff.py` warns
when a project folder has no `GOALS.md`.

Folder layout, the ignore file and the results contract belong to `project-structure`. This skill fills five
documents, from templates in `assets/`:

| Document | Template | Holds |
|---|---|---|
| `SPEC.md` | `assets/SPEC.md` | the inputs verbatim, which part is the goal, the claim-verdict table |
| `research/LITERATURE.md` | `assets/LITERATURE.md` | papers and methods: identity, exact definitions, paper versus code, pitfalls, open uncertainties |
| `research/INTERFACES.md` | `assets/INTERFACES.md` | libraries: version pins, signatures, defaults, determinism, invariances, traps, timings |
| `QUESTIONS.md` | `assets/QUESTIONS.md` | research questions, each tied to an analysis, an output and a reference |
| `STATUS.md` | `assets/STATUS.md` | each component as R, A or E with its evidence; the last good commit |

`assets/EXEMPLARS.md` records an exemplar study (section 6).

## 1. Keep the author's words

- **Paste every input into `SPEC.md` unedited, typos kept, as labeled parts.** Later agents need the exact words;
  a paraphrase drops the constraint hidden in a subordinate clause.
- **Say which part is the goal.** In the source project the header labeled the chat-generated build prompt as
  a draft plan whose every fact is re-verified, and said of the research brief: "Part B is the goal." Where parts
  conflict, record the choice and its reason under "Key decisions" in `NOTES.md`.
- **The author's own words outrank a chat-written part on constraints.** The chat plan said "CPU only"; the
  author's follow-up allowed the local GPU and forbade CPU training. The follow-up won.
- **Later instructions are appended, dated and quoted**, never merged into earlier text.

## 2. Check the specification claim by claim, before any code

`references/verify-spec.md` has the procedure, the claim kinds and the cases.

- **One row per factual claim**: what a method computes, which data a paper used, that something does or does not
  exist, a default, a size, an overlap, a version, a URL. Each gets a verdict (`true`, `partly wrong`, `wrong`,
  `overstated`, `changed in <version>`, `unverified`) and tagged evidence: [RUN] ran it, [DOC] read it with the
  exact source, [U] not yet.
- **Order of authority**: released code at a pinned commit, then released weights and result files, then the
  paper, then documentation and changelogs (a changelog omitted a breaking default change), then notes and agent
  summaries. A project knowledge base (defined in the sibling skill,
  `project-structure/references/knowledge-base.md`) once described a regularizer with the wrong mathematics.
- **Where paper and released code disagree, follow the code that produced the published numbers or weights, and
  record the deviation** in a table of item, paper, code, followed. The paper of a set encoder gave 45,424
  parameters and 64 output dimensions; the released weights had 75,072 and 32.
- **Check license, gating and availability** for every model and code base before choosing it: code with no
  license is ported from its definitions and never copied; non-commercial weights are downloaded at run time and
  never redistributed; a host that no longer resolves takes the candidate out.
- **Look for the strongest and newest version**, not the convenient one. The author asked "why didn't you use ...
  one? ultrathink" when a stronger checkpoint existed, and "why didn't you inlucde these?" about a recent paper.
- **De-duplicate benchmark suites before counting.** 49 of one suite's 51 datasets were inside another: about 144
  unique datasets, not about 190 [DOC], read from the published lists. Match normalized names first, confirm each
  match by identical row and column counts (names alone caught 40 of 49 in a rerun), check the rest by eye, and
  keep the mapping in a file.
- **Spot-check what helper agents report** and list what was re-checked. Audit a shared agent preamble against the
  raw outputs before fanning it out: one wrong preamble was confirmed by six agents.

## 3. Literature notes and interface notes

`references/notes.md` has both formats and the trap catalog.

- **Tag every statement** [RUN], [DOC] or [U], date the file, and keep an "Open uncertainties" list that holds
  every [U] with what would settle it.
- **Write exact definitions from the code** for what the project computes or compares against, with constants and
  file:line.
- **Re-analyze the authors' released result files** and recompute their headline before relying on it. One
  re-analysis found 82,176 configurations at 4 levels per parameter where the paper said 6 levels and "more than
  86k".
- **Never guess an interface.** "Never guess an API. Inspect the installed package first." Record version and
  signature from the installed source, diff defaults against the published recipe and the previous release, and
  log every surprise with its fix. Run `scripts/env_pins.py` for the environment block.
- **Measure what the analysis relies on**: determinism within and across processes, invariances with their
  tolerances, precision and device effects. Mixed precision on one accelerator drifted by 2e-3; switched off,
  CPU and GPU agreed to 1e-6.
- **Cite only files inside the repository.** Notes that pointed to a session scratch folder lost their evidence
  at the next reboot.

```bash
python3 scripts/env_pins.py numpy torch scikit-learn --repo .            # paste into INTERFACES.md
python3 scripts/env_pins.py torch --pin torch==2.5.0                     # exit 1 if the pin does not hold
```

## 4. Reproduce the published baseline first

`references/reproduce-first.md` has the protocol.

- **Order: exact baseline, trivial floor, approximation, extension.** The exact replication of the published
  baseline is "the baseline every other view is read against". A floor (averaging plus PCA, a constant, a
  random-initialization twin) shows what needs no learning.
- **Prove a reimplementation against the authors' own outputs**: reproduce their protocol including the unstated
  parts, then report the minimum per-dimension Pearson r and the Spearman correlation of pairwise distances. An
  accepted port reached 1.0000 on both over 63 datasets. Re-run from the documented snippet, not the scratch file.
- **Set the tolerance from a noise floor**: run the reference against itself. A numpy copy matched a library's
  own functions to 4.8e-7; the test tolerance was 1e-4.
- **Mark every component R (exact reproduction), A (approximation) or E (extension)** in `STATUS.md` with
  `file.function` and its evidence. **A substitute never carries the original's name.**
- **Anchor design choices on methods from groups known to work**, recent and cited, adopted, adapted or rejected
  with a reason: "sth that's working", "not random".
- **Keep the last good commit as the reference.** "keep the og versions (cuz they wroked)." Carry it as a named
  baseline, and on any regression diff against it first.
- **Prove determinism across processes.** A seeded generator changed between processes because it iterated over
  a set of strings; `sorted(...)` fixed it for hash seeds 0, 1, 2 and 5.

```bash
python3 scripts/parity.py authors_outputs.csv my_outputs.csv --id dataset --minmax --report research/parity.md
python3 scripts/hashseed_check.py -- python3 make_item.py --seed 11
python3 scripts/hashseed_check.py --expect-different -- python3 make_item.py --seed 11 :: python3 make_item.py --seed 12
```

## 5. Questions, then a minimal first step with a picture

`references/questions-and-first-step.md` has the details and the one-day timeline.

- **Name the object of study in one sentence**: the units and the space they live in.
- **Number the research questions and tie each to an analysis, an output and a reference or null.** A question
  without an analysis is not yet a research question.
- **Test hypotheses; do not presuppose them.** "Do NOT assume correlation ... We want to test that." State the
  detectable effect first: 51 units detect |r| of about 0.38, about 144 detect about 0.23. A null is reported as a
  null, scoped to the setting tested.
- **Read every number against a reference**: chance, a same-size within-group baseline, the published value, the
  floor.
- **Make the first step minimal and visual.** "give me sth very cool in 30 mins": cheap statistics per item and a
  map of all items within 30 minutes, then layering one family at a time. For a new model, a minimal sibling of
  the design with one visual headline, quantitative evaluation added once the picture works.
- **Save pictures to disk early**: "do it in a way that I have some pngs to look at even if you now run out of
  token limit". A metric does not overrule an obvious picture.
- **Gate expensive work on the cheapest measurement that could stop it**, and report that number first.

Experiment ladders and ablation design belong to `ml-experiment-design`; adversarial review of the design to
`research-design-review`.

## 6. Exemplars and attribution

`references/exemplars-and-attribution.md` has the procedures.

- **Study 5 to 10 exemplars of the field's best work from the files, never from a summary**, against fixed
  dimensions, quoting verbatim, marking each move confirmed or disputed, and recording which moves to adopt in
  `EXEMPLARS.md`. Four of eight rejected book openings came from working off a summary.
- **Use the field's vocabulary**: "really name these stuff liek the field does". Mine it with counts (the full
  procedure is in `author-voice`).
- **Establish an algorithm's true origin and name before citing it**: every copy of the implementation, its
  constants by line number, the original code, the comparator across tagged versions, what the competing name
  means in standard libraries. Where constants differ, write "adapted from". When an earlier claim of yours was
  overstated, say so plainly.
- **Check every citation.** A reference that does not exist and a fabricated citation behind a design choice were
  both caught this way. A missing reference is a placeholder that fails the build, never an invented key.

## 7. Check before the plan is handed over

1. `scripts/check_kickoff.py <project> --strict`: zero errors. It checks the claim table (verdicts, tagged
   evidence, [U] consistency), tags on every literature and interface statement, versions in library headings,
   an analysis, output and reference for every question, R/A/E types with evidence for every R, a named last good
   commit, dates, and no citations into temporary folders.
2. `scripts/env_pins.py` with the project's pins: every pin holds.
3. `scripts/parity.py` for every component marked R that is a reimplementation; its report is the R row's evidence.
4. `scripts/hashseed_check.py` on every generator whose outputs are compared.
5. Read the claim table against the inputs with your own eyes: every factual sentence of the brief has a row.
6. Open the source of each [DOC] row that a design decision rests on and confirm it says what the row says.
7. Look at the first picture before reporting that the first step works.
8. Say what was not checked: every [U], every claim resting on a helper agent's report alone, and anything that
   could not be run here (gated weights, hardware not present).

Report in this order: the corrections to the brief, the questions with their analyses, the first step and its
picture, the status table, what is unverified, and what only the author can decide.

## 8. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| building directly on a chat-written plan | "look I generated this with online chat, please do your own research" | the inputs verbatim plus a claim-verdict table before code |
| facts stated without proof | "do you have proof or just anecdotes?" | a tag and a source on every statement |
| guessing a library's interface | "Never guess an API. Inspect the installed package first" | interface notes read from installed source, with version pins |
| the convenient public model | "why didn't you use ... one? ultrathink" | a search for the strongest available version, with its path as a parameter |
| a missed recent paper | "how about the features from this one? why didn't you inlucde these?" | a literature sweep that includes the last months' preprints |
| a fallback under the original's name | "DO NOT call the fallback" by that name | R, A or E on every component, and a new name for every substitute |
| untested or random methods | "sth that's working", "not random" | design axes anchored on recent methods from groups known to work |
| redesigns that lost what worked | "keep the og versions (cuz they wroked)" | the last good commit as a named baseline in every comparison |
| staying on the theory side | "use our results here to really guid the decisions don't stay on the thoery side" | a minimal first step with a picture, then layering |
| a large plan with nothing to see | "give me sth very cool in 30 mins" | a visual result within 30 minutes |
| an assumed effect | "Do NOT assume correlation ... We want to test that" | hypotheses as tests with a stated detectable effect; nulls reported |
| a summary of exemplars | (four of eight book openings rejected) | the exemplar files opened and quoted |
| an algorithm named after a tool it only resembles | "is it really simiarl ...?" | the primary source, matched constant by constant; "adapted from" |
| notes citing a scratch folder | (evidence lost at a reboot) | scripts copied into `research/scripts/` and cited there |

## Reference files

- `references/verify-spec.md`: saving the inputs, claim kinds, verdicts and evidence, paper versus code, licenses,
  survey agents, benchmark corpora.
- `references/notes.md`: tags, the literature-note blocks, interface notes and the trap catalog, installing
  safely, resuming from notes.
- `references/reproduce-first.md`: the order of work, the parity protocol, R/A/E naming, anchoring, the last good
  commit, determinism.
- `references/questions-and-first-step.md`: object of study, research questions, design tables, the minimal visual
  first step, the one-day timeline, the hand-over.
- `references/exemplars-and-attribution.md`: exemplar study, the field's vocabulary, an algorithm's true origin,
  citations.

Scripts (Python 3.9 or later; `parity.py` needs numpy, the others only the standard library):
`scripts/check_kickoff.py`, `scripts/env_pins.py`, `scripts/parity.py`, `scripts/hashseed_check.py`.
