# Writing a skill for scicraft

Every skill in this package is the distilled practice of real research work: what
was asked for, what was thrown out, and what replaced it. A skill is finished when
an agent that never saw that work can do the task to the standard of the person
who taught it, in a field that person never worked in.

Read this file before writing or changing a skill. `tools/check.py` enforces the
parts of it that a script can check.

## 1. The folder

```
plugins/<plugin>/skills/<skill-name>/
├── SKILL.md          required; frontmatter + instructions, at most 500 lines
├── references/       one topic per file, loaded only when the body points to it
├── scripts/          code the agent runs instead of rewriting it each time
├── assets/           templates and files that end up in the user's output
└── evals/            two or three test cases (section 9)
```

The folder name is the skill name: lowercase, hyphens, at most 40 characters. A
skill must work when its folder is copied alone to another machine, so nothing in
it points outside itself.

## 2. The description

The description is the only part an agent sees before it decides to load the
skill, so it carries the whole decision. Write it in the third person, in under
1,000 characters, in this order:

1. What the skill produces, in one sentence.
2. When to use it, with the words a researcher would type: the plain request
   ("make the ablation figure"), the complaint ("this looks like AI", "the numbers
   don't match"), the deadline ("camera-ready is Friday").
3. What it holds that the agent would otherwise get wrong.
4. Which sibling skill to prefer for the neighboring task.

Agents skip skills more often than they overuse them. State plainly that the skill
should be used whenever the task appears, even when the user does not name it.

## 3. The body

Follow the order of the work. The shape that has held up:

1. **Opening.** Two to four sentences: what the skill is for and what kind of work
   it was distilled from. Refer to the person who shaped it as "the author".
2. **The prime directive.** The one sentence that, if followed, prevents most of
   the failures. Set it apart.
3. **The failures to fear.** The two or three mistakes that cost the most time,
   each with the section that guards against it.
4. **Before starting.** What to collect by reading the project, and what to ask
   the user for in one message.
5. **Numbered sections in working order.** Rules as short bullets that open with
   the rule in bold and give its reason in the same bullet. Tables for mappings
   (claim to picture, symptom to cause, old to new). Exact commands in code
   blocks. Exact numbers with units.
6. **Check before anything is handed over.** An ordered list of gates, scripted
   ones first, then what must be looked at with eyes, then what to say was not
   checked.
7. **What was thrown out, and what replaced it.** A three-column table: the
   rejected thing, the author's words, the replacement. This table teaches taste
   faster than any rule.
8. **Reference files.** One line each: the file and when to read it.

Put detail in `references/`. A reference file over 300 lines opens with a table of
contents.

## 4. Evidence

- Every rule comes from something that happened. If you cannot say what failed
  without the rule, leave the rule out.
- Keep the numbers that were measured or asked for (sizes in pt, px and mm, hex
  colors, thresholds, limits). A rule without its number is advice.
- Never invent a number, a command flag or a behavior. If a script was not run,
  the skill says so.
- When two sources disagree, the newer one wins. If the older rule still matters
  in some setting, name the setting.
- Your own suggestions are allowed only where the source material has a gap that
  would stop a user. Mark each one "Suggested, not yet tested in real work".

## 5. Generality

- State the field-neutral rule first. Then give the instance it came from.
- Use examples from at least two fields where the evidence allows. In the core
  plugin, lead with an example that a machine-learning researcher meets (a
  benchmark table, an ablation, a scaling curve, a model release).
- No project names, internal method names or working titles. Describe the work
  ("a foundation-model paper", "a segmentation benchmark").
- Parameterize everything a user will change: paths, palettes, venue, page limit,
  scheduler. Defaults are the author's; the mechanism is everyone's.

## 6. Privacy

A skill ships to people outside the lab. None of the following may appear in any
file:

- names of supervisors, co-authors, reviewers or collaborators; reviewer text;
  review scores;
- results, benchmark numbers, claims, figure content or method details of
  unpublished work. An incident number from debugging (a loss value, a rank, a
  file size, a timing) may stay when it teaches the rule and identifies no
  dataset, model or paper;
- usernames, home paths, cluster paths, group codes, hostnames, bucket names,
  private repository names, email addresses, keys or tokens;
- the author's name, except in the plugin manifest.

Institute infrastructure belongs only in the internal plugin. Personal access
details belong nowhere: a skill that needs them reads them from a local file the
user keeps outside the package.

Third-party material keeps its license and credit. Record every borrowed piece in
`THIRD_PARTY.md` with its source and license.

## 7. Integrity

The package teaches honest practice. Research under deadline pressure produces
requests to leave things out, and a skill must never turn such a request into a
rule. Where the source material contains one, write the honest form:

- Choosing what to lead with is presentation. Changing what the records support
  is misreporting. A skill may teach the first and must block the second.
- A reporting threshold (which p values are printed, which runs count as
  complete) is applied to every result alike, favorable or not, and is stated in
  the document.
- A result that contradicts a claim changes the claim. A weak or mixed result goes
  to the appendix or backup with its number, never out of the record.
- A setting that differs from the default is reported where the result is
  reported.
- Emphasis by color, order or size is allowed only when the values themselves are
  printed or plotted to scale.

## 8. Voice

Skills are read by agents and audited by people who dislike machine-made prose.
Write the way the best skills here are written:

- Plain declarative sentences. Imperatives for instructions. One idea each.
- No em dashes and no en dashes as punctuation. Use a comma, a colon,
  parentheses or a new sentence. Write ranges with "to".
- No staged contrast ("not X but Y", "X, not Y", "X rather than Y") unless the
  negated half names a mistake that actually happened.
- No triads built for rhythm, no slogan sentences, no closing one-liners.
- No sales words: `powerful`, `robust`, `comprehensive`, `seamless`, `crucial`,
  `novel`, `elegant`, `principled`, `cutting-edge`, `leverage`, `delve`. A word
  such as `robust` stays where it is the technical term.
- No filler openers (`It is worth noting`, `Importantly`, `Note that`) and no
  sentences about the document itself (`This section covers`).
- A list of banned words has to name them. Put each in a code span, as above, so
  the linter skips it.
- No separators between phrases (middle dots, pipes, bullets inside a line), no
  emoji, no bold used as decoration. Bold opens a rule or marks the one phrase
  that must not be missed.
- One name per thing, used everywhere.
- Quote the author when the quote carries the rule. Keep quotes short and free
  of profanity.
- American spelling.

Run `python3 tools/check.py --voice <skill folder>` and fix what it reports.

## 9. Scripts, assets and evals

**Scripts** exist where a step is deterministic or was rewritten more than once.
Each script:

- runs on Python 3.9 or later (or Node 18 or later), prefers the standard
  library, and names every other dependency in its docstring and in SKILL.md;
- takes its inputs as arguments (`argparse`), answers `--help`, and never
  contains an absolute path;
- says what it checked, exits non-zero on failure, and never prints a secret;
- has been run by you on a small real input before you call the skill done.

**Assets** are complete and usable as they are: a preamble that compiles, a style
module that imports, a template with placeholders in [brackets].

**Evals** are two or three realistic requests, each a folder under `evals/`:

```
evals/<case-name>/
├── prompt.md       settings block, then the request as a user would type it
├── case.yaml       schema_version "1.1", name, expected_outcome
├── graders/        NN-few-words.md, one checkable statement each
└── files/          input files, with place-files.sh, only if the case needs them
```

Write requests the way people type them: with context, a deadline, a file name, a
typo. Graders state what the result must contain, in terms a third party can
verify from the files produced.

## 10. Done

A skill is done when all of these hold:

1. `python3 tools/check.py <skill folder>` passes: frontmatter, length, links,
   scripts compile, no private strings, voice.
2. Every script was run and every asset was used once, and the build note says
   with what input.
3. A reader from another field could follow SKILL.md without the references and
   get a correct, if plain, result.
4. No sentence could be deleted without losing an instruction, a number or a
   reason.
5. The build note lists the sources used, what was generalized, what was left
   out and why, third-party material with its license, and what remains
   untested.
