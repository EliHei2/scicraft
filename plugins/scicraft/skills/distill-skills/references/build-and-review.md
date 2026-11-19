# Building each skill: brief, writer, gate, the author's look

## The build brief

`assets/build_brief.md` is the template; `scripts/make_briefs.py` fills it from the spec:

```bash
python3 scripts/make_briefs.py [ws]/tools/skill_spec.json --dry-run      # resolves every findings code
python3 scripts/make_briefs.py [ws]/tools/skill_spec.json                # writes briefs/W_[skill].md
python3 scripts/make_briefs.py [ws]/tools/skill_spec.json --only poster  # rewrite one brief
```

It fails (exit 1) when a findings code matches no file or more than one, or when a placeholder is left
unfilled. The brief is a file; the writer gets one line: "Read your full assignment at [brief] and
carry it out exactly. It names the contract to read first, your sources, the folder to create, the
gate to pass and the build note to write."

Why each part of the brief is there:

| Part | What failed without it |
|---|---|
| read the contract first, then one finished skill as the model | skills in different shapes and voices; the model skill teaches structure faster than the contract |
| primary sources read fully, secondary by rule or tag | writers reading 40 files and running out of context, or skimming the one that mattered |
| existing material to port | working scripts rewritten from memory, losing their fixes |
| decisions already made | writers re-deciding what the lead had settled, differently each time |
| evidence only, additions marked | generic rules that no finding supports |
| run what you ship, on a small input you make | scripts that compile and fail on first use; real history passed through a test |
| sibling list | two skills teaching the same rule two ways |
| the gate command with the tier's terms file | private strings found only at release |
| the build note | no record of what was run, left out or not tested |
| a final message of at most 150 words | long reports the lead must read for three numbers |

## The writer's loop

1. Read the contract, the model skill, the sources (primary fully).
2. Port the existing material: copy, strip names and paths, parameterize, add `--help`.
3. Write SKILL.md in working order; detail into references, one topic per file.
4. Run every script on a small input the writer makes; compile every template if the tool exists.
5. Write two or three eval cases (request as a user would type it, graders a third party can check).
6. Run the gate until it reports zero errors; fix or justify each warning.
7. Write the build note (`assets/build_note.md`).
8. Final message: files, gate result, what is untested, questions for the author.

## The gate

`scripts/check_skill.py` is a copy of the original package's gate with the institute patterns moved
into a file. What it enforces:

| Check | Error | Warning |
|---|---|---|
| structure | no frontmatter; name differs from folder or breaks the pattern; description outside 80 to 1,024 characters or with angle brackets; eval case without settings block, `case.yaml`, schema version "1.1", matching name, expected outcome or graders | SKILL.md over 500 lines; body under 150 words; no eval cases |
| links | SKILL.md names a file under references/, scripts/ or assets/ that does not exist | a reference file SKILL.md never names; a reference over 300 lines without a table of contents |
| scripts | Python that does not compile; JavaScript failing `node --check`; shell failing `bash -n` | |
| private | home paths, emails (example domains excepted), API keys, private key headers, any term of `--terms`, any regex of `--internal-terms` without `--internal` | |
| voice | em or en dash as punctuation; slop words; separators between phrases; emoji | en dash in a range; sales words unless technical; filler openers; more than 30 staged contrasts per 10,000 words |

Ban lists inside a skill go in code spans, which the voice check skips. Eval folders are skipped by the
voice check and scanned by the private check, so a test fixture with a planted key must build the key
at run time (see `evals/digest-own-history/files/make_fixture.py`).

## Commands against scripts

The gate checks that a script compiles. It does not check that the command the skill prints still
works. For each script named in SKILL.md or a reference file:

1. Run `python3 scripts/[name].py --help` (or the subcommand's `--help`).
2. Compare every printed command with it: flag names, defaults, required arguments, subcommands.
3. Fix the text, or the script, until they agree. Repeat after every script change.
4. Record the check in the build note ("commands checked against `--help`, [date]").

Evidence: one of the author's repositories kept a skill-maintenance checklist whose first line was
"Verify script names and flags against current `scripts/` files", because skill text drifted from
script behavior; a renamed or dropped flag fails on first paste.

## Several agents on one skill

When agents refine one skill in parallel, write their contract once and give it to each:

- **Edits are additive.** No existing file, macro, style, color or function is renamed or removed; a
  value may be re-tuned or a new name added. The author's refinement contract for a figure skill
  stated the reason: every reference file depended on the current names, so a rename breaks what
  another agent is editing.
- **Every snippet an agent adds or touches is compiled or run before it returns.** The same contract
  made this binding on every implementer.
- **No build file stays in the skill folder** (log, aux, PDF, PNG preview, cache). Leftover build files
  carry machine paths, and the contract itself was later found to hold one.

## Bulk replacements

A scripted replacement across many files (a spelling pass, a renamed term, a leak row) matches
strings and cannot tell whether the sentence around them still reads. In this package's own build one such replacement garbled several sentences
before anyone read them. After every bulk replacement, list each changed line with its file
(`git diff --word-diff` or the script's own log) and read the whole sentence around it. Quotes stay
verbatim; a replacement never edits inside quote marks.

## The author's look at rendered demos

For skills whose output is visual, the writer's own look is not the last look.

- The writer renders the demo and looks at crops. The lead or the author then opens the demo at full
  size and lists every defect, numbered, each with where it is and what is wrong.
- The list goes to the same writer as a message (the agent keeps its context, so the fix reaches the
  code, the documentation and the skill's own look list at once). A fresh agent gets the build note
  plus the list.
- The writer fixes, re-runs, looks again at the crops that showed each defect, re-runs the gate and
  appends a "Revision N" section to the build note: each defect, the fix, the file, the re-run.
- In the original build one round found five defects in a figure skill's demo after the writer's own
  look at up to 1,500 dpi: a label on a whisker, a direction arrow wrong after rotation, a checker
  option misapplied to panels, panels misaligned with a dead margin, and British spelling. One defect
  (the arrow) was also in the shipped template, which the demo alone would not have shown.

## Revisions from late evidence

A revision is a brief of its own: the skill folder, the build note, the new findings file and the
named items to add. The writer keeps everything that holds, adds the new evidence where it belongs,
re-runs what it touched and records "Revision N" in the build note. Revisions in the original build
came from second-wave findings (a project layout, slide session gaps, a journal campaign, new ML
evaluation evidence) and from the author's look.

## The coverage pass: audit, reconcile, repair

In this package's own build, after every writer had passed the gate:

1. **Audit.** One auditor per findings file, line by line (`scripts/coverage.py`). It found 14 percent
   of the in-scope items only partly covered or missing, and about 70 places where two skills
   disagreed.
2. **Reconcile, once.** One reconciler read every disagreement in `_CONFLICTS.md` and wrote one ruling
   per contradiction: topic, the skills it touches, the ruling, the owner skill, the evidence with
   dates, the exact change per skill, and a status (settled, or applied with a stated default for the
   author to confirm). A skill that is not the owner states the rule in one line and points to the
   owner by skill folder and file.
3. **Apply exact changes centrally.** Leak rows and rulings whose change is a fixed text replacement
   go in one pass across the package, and every changed sentence is read (section above).
4. **Repair per skill.** One gap-fill agent per skill gets its rulings, its `_additions_[skill].md` and
   its issues. It adds each addition or declines it with a reason (already present, overruled by a
   ruling, too tied to one project, private, or a request honest reporting does not allow), runs the
   gate and appends "Revision: coverage pass" to its build note.

Repairing skill by skill before the reconciliation would let each agent settle a shared disagreement
its own way.

## Reading build notes

Read each build note before accepting the skill: what was left out and why, what is untested, and the
questions for the author. Collect the questions into the final report; do not answer them for the
author.
