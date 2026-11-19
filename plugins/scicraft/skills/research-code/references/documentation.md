# Documentation of research software

## 1. Per-command user docs

One file per command in `docs/`, numbered in the order a new user needs them, from the template
`assets/command_doc.md`. The owner's requests that shaped it:

- "make a docs dir ... inputs, outputs, what exactly is being computed"
- "-idea -steps -output"
- "step by step guides and starting from the most important stuff then go down to specific details"
- "explain ... how best to set params and what is the effect of each param"
- "also include time and memory"
- "what is the minimal info in a data that could be runnable?"

Rules:

- **Most important first.** The main command, its required inputs and its default output come before options.
- **Each parameter with the effect of raising and of lowering it**, and the situation in which to change it.
- **Guidance drawn from benchmarks, never benchmark results.** "don't explicitly mention any result (other than
  expected time/vram) from benchmarks. only deduce guidelines from it." Give real thresholds where they exist;
  do not label values as good or bad without one.
- **Measured time and memory**, with input size and hardware. Never extrapolated without saying so.
- **Exact definitions** of every computed number (the formula or the rule), and where an approximation is used
  (an ellipse fit in one place, a convex hull in another), say which.
- **`None`, never `none`**, every identifier in backticks.
- **Common errors with their fix**, one row per message.

## 2. README

- The minimal runnable input and one command that runs on it, then a pointer to the docs folder ("add minimal
  needed info also to the README and that people can get guides from that docs folder").
- A few lines in the repository's existing style for any addition. An edit that added generic prose was
  rejected: "you added so much ai fluff, unnecessary and slop."
- Careful compatibility claims ("compatible with X's spec").

**A sprint repository others will run** (a hackathon, a one-day team repository). A long first README came back
with "the readme you made is extremely long, please make super on point 1-2-3 main points". The form that
replaced it:

- Two or three sentences on why, then the 1-2-3 main points.
- One hero figure on top, after the brief explanation: at most four panels, one shared legend, no panel letters.
- The gallery of further figures lower down, or left out ("instead of dumping "all figures" there, just put the
  points and the AUC").
- How to run the minimal entry function and `vis.py` (`git-and-prs.md` section 8).

## 3. Docstrings and comments

- Terse, in the target repository's docstring style ("adjust all code style, docstrings and all that compatible
  to [the upstream] lab").
- The rationale and an honest hedge, never a restatement of the code.
- Shape comments on tensor lines.
- A comment beside a non-obvious fix that records why it exists (a build path, a workaround).

**The paper-to-code map.** For a method paper, keep one table in `docs/`: each equation, loss term or claim of
the paper, the function that computes it, and the test that checks it. Check the newest methods text before
changing what a function computes. A map plus a test replaced prose descriptions after a knowledge-base entry
described a regularizer with the wrong math; the authors' code settled it.

## 4. When docs are updated

- **Docs that describe a decision** go in the same commit as the decision.
- **Shared indexes, skills and the project's guidelines** (`GUIDELINES.md` and the other governing documents
  are defined in the sibling skill, `project-structure/references/governing-documents.md`) are updated in batches on a trigger phrase ("update docs", "sync
  docs"): per-item work marks a ledger row as unsynced, and the sweep folds them in as one named change. "I don't
  want to update every single time ... when I'm done with big changes I'd like to say update docs."
- **What was learned in a session** (a cause found in a regression hunt, a measured memory profile) goes into the
  project's docs or lab notebook at the end of the session, appended and never contradicting what is there.
  When it is generalized into a skill, project specifics are stripped.

## 5. Agent context files

A short index (200 to 500 words) with pointers, kept local in shared repositories. `project-structure` owns the
layout and the template.

## 6. Methods text

A methods section or supplementary note states the exact math with no code identifiers and no results.
`nature-methods-writing` and `paper-writing` own that register.
