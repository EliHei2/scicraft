---
name: distill-skills
description: Turns a researcher's own history with an AI agent (prompt history, session transcripts, memory notes, repositories, earlier skills) into a tested package of skills others can install. Use it whenever someone wants to capture how they work before moving labs, hand their craft to a group or students, turn a year of Claude Code sessions into skills, mine their chats for lessons learned, or check that every hard skill they built is somewhere in a skill set, even when they only say "make skills from my history". Holds the method that built about forty skills from about 15,000 prompts: secret-redacting digests, slices sized for one agent, the mining brief and findings schema, gap miners, the skill set from candidate sections and tag counts, one build brief per skill, the contract and gate, the author's own look, a coverage audit, tiers and what never ships, and requests that must not become rules. Prefer prompt-writing for one brief, agent-orchestration for fleets, adversarial-audit for review.
---

# distill-skills

How to turn the record of one person's work with an AI agent into a package of skills that an agent who
never saw that work can follow to the same standard. The method was built and used once, on a year of
one scientist's history (about 15,000 prompts across 20 projects, mined by 40 agents into 40 findings
files, built into 46 skill briefs). Every step below was done in that build, except where a section
says it was planned and not yet run. The person whose history is mined is called the author.

> **PRIME DIRECTIVE: every rule in the package traces to something that happened in the author's history,
> and nothing secret, private or dishonest from that history reaches the package.** Evidence goes in with
> its number; names, keys, unpublished results and requests to hide results stay out.

Three failures cost the most. Guard against them from the first command:

1. **A leak.** Old prompt history holds pasted API keys, collaborators' names, unpublished numbers and
   institute paths. In the build this skill came from, a miner found keys in prompts typed months
   earlier. The digest step redacts, the gate scans every file, and the owner is told to rotate
   (sections 1, 6, 12).
2. **A craft that ends in no skill.** The author's requirement was "really make sure that every single
   hard skill and work we've been doing is somewhere within this set". First-wave miners miss work
   that no slice covered. A second wave of gap checks and a coverage audit catch it (sections 4, 10).
3. **Generic skills.** A writer who runs short of evidence fills the gap from general knowledge, and
   the skill reads like every other. The author's standard: "do not hand-wave, do not fixate on a
   specific use case". Each rule carries its number, command or reason, or it is cut (sections 7, 8).

## 0. Before starting

Collect by looking, then ask the rest in one message:

- **The sources**: the prompt history file, the per-project session transcripts, memory notes, the
  author's repositories and any skills they already wrote. Note their sizes; the transcripts of a year
  can be 2 GB.
- **The standing documents of every project**: the index file, the narrative, the guardrails, the
  guidelines and the knowledge base (defined in the sibling skill,
  `project-structure/references/governing-documents.md`; for the knowledge base,
  `project-structure/references/knowledge-base.md`). They live in the repositories, not in chats or
  memory, and they state the rules the author chose to write down. In this package's own build the
  mining of chats and memory missed them, and they were added only when the author asked for them.
- **The audiences**: who will install the package (a new lab, a group, students), and in which field.
  This fixes the tiers (section 6) and the lead example of every skill. In the original build the
  receiving lab was "much much more ai than bio", so every core skill leads with a machine-learning
  example and biology moved to a field plugin.
- **The named requests**: every craft the author asks for by name ("prompt making", "QC", "how to
  organize code and data"). Write them, numbered and in their words, into the state file
  (section 13). Each one must end in a skill or a stated reason.
- **Budget and model**: how many agents at once and on which model. The original build ran at most
  20 agents, all on the strongest model, because the author asked for a fan-out in so many words.
  Without that request, work solo (see `agent-orchestration`).
- **What must stay private**: people, institutes, projects and datasets whose names may not appear.
  These become the forbidden-terms files (section 6).

Work in two folders that never mix:

```
[private workspace]/                 never shipped, never committed to the package
├── digests/        history/, sessions/, INDEX.md          (scripts/extract_sessions.py)
├── findings/       [CODE]_[topic].md, one per miner
├── briefs/         miner prompts, W_[skill].md build briefs, C_[code].md coverage briefs
├── build_notes/    [skill].md, one per writer
├── coverage/       [code].md per auditor, _SUMMARY.md, _additions_[skill].md
├── tools/          copies of this skill's scripts, the skill spec JSON
├── private_terms*.txt               forbidden strings per tier
└── STATE.md                         the lead's state file
[package]/                            what ships: plugins/[plugin]/skills/[skill]/, docs/, tools/
```

## 1. Condense the history into digests, with secrets redacted

Raw transcripts are unreadable for an agent: images as base64, tool output, request blobs. A digest
keeps what carries the working pattern: every prompt typed, the assistant's prose (capped), one line
per tool call, subagent reports, and the compaction summaries, which are the densest record of method.

```bash
python3 scripts/extract_sessions.py --out [private workspace]/digests          # defaults: ~/.claude
python3 scripts/extract_sessions.py --out DIG --projects-dir P --history H --project-filter paper
```

- **Redact at write time, before any agent reads a byte.** Every block passes through one redaction
  function: Anthropic, OpenAI-style, GitHub, Hugging Face, AWS, Slack, Google and W&B keys, private key
  blocks and credentials inside URLs become `[REDACTED:kind]`. The index counts redactions by kind and
  never prints a value.
- **Tell the owner to rotate every redacted key, at once and again at the end.** A digest hides a
  secret; it does not revoke it. The key is still in the original history file.
- **Chunks of 60 KB**, so one chunk fits one read. A year of transcripts went from 2.2 GB to about
  6.7 MB of digests (47 history files, 88 session chunks).
- **Keep the author's typos and profanity in digests.** They mark the strength of a preference; the
  skills later quote sparingly and without profanity.
- **Look at a digest before launching anyone.** The first version filed background-task notifications
  and subagent hand-backs as prompts the author typed; one look at a chunk caught it, the classifier
  was fixed and the digests rebuilt.

What the digest keeps and drops, every cap, the record types and the traps: `references/digests.md`.

## 2. Plan the slices

A slice is what one miner reads fully. Size it so the miner finishes and writes; a miner that runs out
of context loses the synthesis.

| Slice kind | Code | Holds |
|---|---|---|
| prompt history | H | every prompt of one to three projects |
| one long session | S | one session in parts of up to seven chunks |
| memory notes and logs | K | feedback, project and reference notes of one or two projects |
| ground truth | A | repositories, standing documents, existing skills, style files, templates |
| cross-cutting | X, T | one theme across all sources (briefs and agents, a writing system) |

- **At most about 420 KB per slice** (seven 60 KB chunks), the largest slice a miner read fully in the
  original build. `scripts/plan_slices.py DIGESTS --budget-kb 420` packs history and session chunks
  into slices and splits long sessions into parts; it gives 39 slices on the original digests.
  Memory notes, repositories and skills are planned by hand.
- **Give every project's standing documents to a ground-truth miner** (section 0), to read fully.
  A plan built from the digest index alone has no slice for them, because they are not digests.
- **Give each slice a special focus**: the questions its sources answer best (a session of fifteen
  rounds of notes answers "what did the author correct"; a repository answers "what are the exact
  numbers").
- **Weight by audience.** Field-neutral craft first, field craft second, infrastructure last.

## 3. Mine: the brief, the schema, write as you go

One shared contract, `assets/mining_brief.md`, read by every miner, and one short launch prompt per
miner (`assets/miner_launch.md`, four variants). The contract holds the mission, what counts as a
finding, the generalization discipline, the theme tags, the cross-cutting topics, the source formats,
the findings schema and the rules of engagement.

- **The findings schema has ten sections**: sources read, the author's words, rules, procedures,
  failure to fix, assets to ship, vocabulary, candidate skills, sensitive items, contradictions over
  time. Rules carry Why, How, Scope and Strength. Sections 8 to 10 drive everything after mining.
- **Freeze the theme tags before the first miner starts.** The skill set is chosen from tag counts
  across files, and a tag invented by one miner cannot be counted.
- **Write as you go.** Skeleton in the first tool call, an append after every two chunks, a final
  reorganization. A miner that dies keeps what it wrote.
- **Miners are read-only everywhere except their findings file**, report in at most 150 words (the
  path, the five strongest findings, what blocked them), and say exactly what they did not read.
- **Check every miner's file before counting it**: it exists, has all ten sections and has rules.
  `scripts/tally_findings.py FINDINGS` reports a file with zero rules, which is what a dead miner
  leaves.

Slice planning detail, the launch variants and monitoring: `references/mining.md`.

## 4. The second wave: gaps

Added after the first wave, and it paid. Two kinds of gap:

- **Work no first-wave miner covered**: a project found late, a request the author added after mining
  began (in the original build: the newest project's layout, which the author named as the model for
  organizing a project, and a journal revision campaign).
- **Sessions that already produced a skill.** A skill distilled at the time of the work holds what
  seemed important then. A gap miner reads the skill first, then every chunk of the sessions, and
  reports only what is partly there or missing, each with the file and section where it belongs
  (`assets/miner_launch.md`, variant 4).

Second-wave findings reach skills that are already written through a revision: a message to the
writer that still holds context, or a fresh agent with the old build note and the new findings.

## 5. Choose the skill set

Four inputs, in this order of weight:

1. **The author's named requests** (section 0). Each one gets a skill or a named home in one.
2. **Candidate skills named by more than one findings file.** `tally_findings.py` lists them with
   counts; a candidate named by four miners from different sources is a skill.
3. **Tag counts**: a theme with many rules and no candidate is a skill nobody proposed.
4. **Existing skills of the author**: each is merged, ported or retired, never ignored.

Then cut boundaries so that no two skills own the same rule: one skill for the process, another for
the style, a third for the gate. Every brief names all siblings and says which one owns the
neighboring task. Write the set as a spec, one row per skill: plugin, scope in one sentence, what it
must contain, primary findings (read fully), secondary findings (named rules or tags only), existing
material to port, and decisions already made. `assets/skill_spec.example.json` has the shape;
`references/skill-set.md` has the worked reasoning.

## 6. Tiers, and what never ships

| Tier | Who may install it | What it holds |
|---|---|---|
| core | anyone, public | field-neutral craft, led by the main audience's example |
| field plugins | the field's labs, public | domain method (for example ML evaluation, spatial omics) |
| internal | the institution only, never public | cluster queues, storage layout, institute tools |
| personal | nobody | usernames, home paths, keys: read from a local file the user keeps outside the package |

- **Never in any tier**: names of supervisors, collaborators or reviewers; reviewer text and scores;
  results, numbers, claims or method details of unpublished work; usernames, home and cluster paths,
  hosts, group codes, bucket and private repository names, emails, keys; the author's name outside
  the plugin manifest. An incident number from debugging may stay when it teaches the rule and
  identifies nothing.
- **One forbidden-terms file per tier**, kept in the private workspace (the list itself names what
  must not leak). The core list holds people, projects, working names, handles and the institute; the
  field list allows the field's public names; the internal gate runs with `--internal`.
- **Third-party material keeps its license.** Record every borrowed piece in `THIRD_PARTY.md`. A piece
  under a noncommercial license was rewritten independently in the original build; an MIT piece kept
  its notice; pieces whose license could not be verified offline are listed as unverified.

## 7. One build brief per skill

`scripts/make_briefs.py SPEC.json` writes `briefs/W_[skill].md` from `assets/build_brief.md`. The
writer is launched with one line: "Read your full assignment at [brief] and carry it out exactly."

The brief holds, in this order: the mission; what to read first (the contract, then one finished skill
as the model for structure and voice, then the sources); the skill's scope and must-contain list; the
sources; decisions already made; the rules of the job (evidence only, depth, field-neutral, private
strings, integrity, port real code, run what you ship, evals, siblings); the gate command; the build
note; a final message of at most 150 words.

- **Evidence only.** Every rule traces to a finding or to existing material. A writer's own addition
  is allowed only where a gap would stop a user, marked "Suggested, not yet tested in real work".
- **Port real code.** When the author's repository already has a script that does the job, copy it,
  strip the residue, parameterize it and run it. Rewriting working code from memory loses its fixes.
- **Run what you ship**, on a small input the writer makes, never on the real history. If something
  cannot run here, the skill and the build note say so.
- **Put late decisions in the brief before launch.** Evidence that arrives after a brief was written
  goes into its "Decisions already made" line (or a launch note in the state file), never into a
  second conversation.
- **Several agents refining one skill share one written contract**: edits are additive, no existing
  file, macro, style or function is renamed or removed, every snippet an agent touches is compiled or
  run before it returns, and no build file (log, PDF, preview, cache) stays in the skill folder. The
  author's own refinement contract for a figure skill said why: every reference file depended on the
  current names. Leftover build files carry machine paths.
- **Read every sentence a bulk replacement changed, in place, before anything ships.** In this package's own build a
  scripted bulk replacement garbled several sentences before anyone read them.

## 8. The contract and the gate

`assets/authoring_contract.md` is the contract every writer follows: folder layout, description,
body order (opening, prime directive, failures to fear, before starting, numbered sections, check,
thrown-out table, reference list), evidence, generality, privacy, integrity, voice, scripts, evals,
done. Copy it into the package's docs and fill its brackets.

```bash
python3 scripts/check_skill.py [skill folder] --terms [private workspace]/private_terms.txt
python3 scripts/check_skill.py [internal skill] --terms [...]_internal.txt --internal-terms [regexes] --internal
```

The gate checks structure (frontmatter, name, description of 80 to 1,024 characters, at most 500
lines, eval layout), links (every named file exists, every reference file is named), scripts (Python
compiles, `node --check`, `bash -n`), private strings (home paths, emails, keys, the terms file) and
voice (dashes as punctuation, sales words, filler, separators, emoji, staged contrasts). Errors block;
each warning is fixed or justified in the build note. Detail: `references/build-and-review.md`.

- **Check every command a skill prints against the script it calls.** Run `--help` on each script
  named in SKILL.md and the references and compare flag names, defaults and required arguments with
  the documented ones. Repeat after every script change and record it in the build note. A flag the
  script dropped or renamed fails on first paste; one of the author's repositories kept a checklist
  for exactly this ("verify script names and flags against current `scripts/` files") because skill
  text drifted from script behavior.

## 9. The author looks at what renders

A gate cannot see a label sitting on a whisker. For every skill whose output is visual (figures,
schematics, slides, posters, pages), the demo the writer rendered is looked at by the author or the
lead at full size, and the defects go back to the same writer as a numbered list.

- In the original build the writer had already looked at crops at up to 1,500 dpi. The second look
  still found five defects: a label on a whisker, a direction arrow that pointed the wrong way once
  the label was rotated, a checker option that applied a figure width to single panels, a demo whose
  panels did not share top and bottom lines, and British spelling. All five were fixed, re-run and
  looked at again, and the build note records them as revision 2.
- **Send the list to the writer that holds the context** (a message to the running agent), so the fix
  lands in the code, the docs and the look list at once.

## 10. Coverage audit

Added after the writers, to meet the author's "every single hard skill" requirement with a number.

```bash
python3 scripts/coverage.py write --findings F --briefs B --coverage C --package-root PKG/plugins \
    --contract PKG/docs/AUTHORING.md --package [name] --requirement "[the author's words]"
# one fresh auditor per brief, in parallel, each writes C/[code].md
python3 scripts/coverage.py aggregate --coverage C --findings F
```

- **One auditor per findings file.** It lists every rule, procedure and asset, and every failure no
  rule implies, then gives each a status: `COVERED` (cite skill, file, line), `PARTIAL` (say what is
  missing), `MISSING` (name the home) or `EXCLUDED` (project-only, sensitive, superseded, or an
  integrity request). Strict: covered means a user of the skill would be told to do it.
- **The aggregator** counts statuses, computes the covered share of in-scope items (excluded rows
  left out), lists auditors that left no rows and findings never audited, collects the proposed
  additions per skill into `_additions_[skill].md` for one gap-fill agent per skill, and collects
  every auditor's contradictions and leaks into `_CONFLICTS.md` for the reconciler.
- **Audit line by line against the findings, after the package looks finished.** In this package's
  own build the audit found 14 percent of the in-scope items only partly covered or missing, in a
  package every writer had already passed through the gate.
- **Reconcile before repair.** The same audit found about 70 places where two skills disagreed. One
  reconciler read them all and wrote one ruling per contradiction (topic, skills, ruling, owner
  skill, evidence with dates, the exact change per skill, status), settled once for all skills. Only
  then did the gap-fill agents start, each bound by the rulings for its skill. Repairs made skill by
  skill would each settle the disagreement their own way. Newest evidence wins (section 12); a ruling
  that the records cannot settle is applied with a stated default and marked for the author.
- **Apply exact replacements centrally, the rest per skill.** Leak rows and rulings whose change is a
  fixed text replacement go in one pass across the package; rulings that need judgment, the additions
  and the per-skill issues go to that skill's gap-fill agent. Every changed sentence is read
  (section 7).

## 11. Adversarial review, then release

- **One fresh reviewer per skill that has not seen its brief**, reading the skill as a stranger from
  another field would. Reviewers report; the writer (or one gap-fill agent) applies. The finder and
  verifier mechanics belong to `adversarial-audit`.
- **Read the flagship skills yourself.** A sample of SKILL.md files read end to end by the lead
  catches tone and depth problems no checker flags.
- **Check unpublished content once more** before release: method details and benchmark numbers of
  work not yet public.
- **Package**: README, `THIRD_PARTY.md`, an index of skills, an install test in an isolated
  configuration folder, plugin validation. Where it ships (public repository, organization
  marketplace, internal mirror) and who owns it is the author's and the institution's decision; ask
  before publishing. `references/release.md` has the options as of late 2026.
- This step was planned, not yet run, when this skill was written.

## 12. Requests that must not become rules

Research under deadline produces instructions that a skill must never teach. Miners record any they find
plainly in section 10; writers encode only the honest form; the build note lists them. Requests of this kind:

| Request | Encoded as |
|---|---|
| leave out p values above a threshold that nobody asked for | a display threshold is applied to every result alike and stated; full values stay in a table |
| answer reviewers with as little as possible | answer what was asked with true, printed evidence; omitted numbers stay in the paper or appendix |
| word the text so a non-default setting is not noticed | report the value actually run where the result is reported |
| drop the tables where a baseline wins | every table is reported, ties and losses included; a weak result goes to the appendix with its number |

Also not rules: one-off decisions, project facts, preferences a later statement superseded (latest
wins; name the setting where the old one still holds), personal access details, and the author's
appetite of the moment for cost or fan-out size. `references/tiers-and-integrity.md` has the full
handling, including secrets.

## 13. Keep the build alive across context resets

A build of this size outlives the lead's context several times. Keep `STATE.md` (template:
`assets/STATE.md`) current after every launch, finished agent and decision: the package and workspace
paths, the launch line, the model and cap; the user's requests in order; mining done, running and in
the second wave; writers done, running and queued in order, with launch notes; the steps after the
writers; decisions already taken; what to tell the user at the end. After any reset, read it before
anything else. Detail: `references/running-the-build.md`.

## Check before anything is handed over

1. `check_skill.py` on every skill with its tier's terms file: zero errors, each warning justified.
2. `extract_sessions.py` index: every redacted key is on the rotate list for the user.
3. `tally_findings.py`: no findings file with zero rules; `coverage.py aggregate`: no auditor without
   rows, no findings file unaudited.
4. Every named request in `STATE.md` points to a skill or a stated reason.
5. Every script in every skill ran on a small input; every build note says with what. Every command
   a skill prints matches the script's `--help` (section 8).
6. Every contradiction in `_CONFLICTS.md` has a ruling, and every ruling's changes are applied in each
   skill it names. Every sentence a bulk replacement touched was read (section 10).
7. Look at every visual demo at full size (section 9).
8. Say what was not checked: reviews not yet run, licenses not verified, scripts that could not run.

## Scripts

Python 3.9 or later, standard library only. Run each with `--help` first.

| Script | Does |
|---|---|
| `scripts/extract_sessions.py` | transcripts and prompt history into 60 KB digests, secrets redacted, with an index |
| `scripts/plan_slices.py` | digest chunks into slices under a size budget, long sessions split into parts |
| `scripts/tally_findings.py` | rules, procedures, failures, tags, scopes and candidate skills across findings files |
| `scripts/make_briefs.py` | one build brief per skill from a JSON spec and the brief template |
| `scripts/coverage.py` | coverage briefs per findings file, then the aggregate share, additions per skill and the conflicts list |
| `scripts/check_skill.py` | the gate: structure, links, scripts, private strings, voice |

`plan_slices.py` and `tally_findings.py` were written for this skill: suggested, not yet tested in real
work beyond the runs in its build note.

## What was thrown out, and what replaced it

| Thrown out | In the author's words, or what happened | Replaced by |
|---|---|---|
| reading raw transcripts | 2.2 GB of images and tool output | 6.7 MB of digests in 60 KB chunks |
| a digest that filed notifications as prompts | caught by one look at a chunk | a classifier for notifications and hand-backs, digests rebuilt |
| secrets passed to agents | keys found in old prompts | redaction at write time and a rotate list |
| skills written from general knowledge | "do not hand-wave, do not fixate on a specific use case" | evidence only, numbers kept, additions marked |
| first wave taken as complete | "every single hard skill ... is somewhere within this set" | gap miners and a coverage audit |
| mining chats and memory only | the governing documents in the repositories were missed until the author asked | standing documents read as sources (section 0) |
| a finished package taken as complete | the line-by-line audit found 14 percent partly covered or missing | the coverage audit before release (section 10) |
| each skill repaired on its own | about 70 places where two skills disagreed | one reconciler, one ruling per contradiction, then repair |
| a bulk replacement trusted unread | several sentences garbled | every changed sentence read in place |
| code rewritten from memory | working fixes lost | port the author's script, strip, parameterize, run |
| the writer's own look as the last look | five defects found after crops at 1,500 dpi | the author's look, defects back to the writer |
| a skill pointing at files outside itself | a renderer that needed one machine's absolute path | self-contained folders, checked by the gate |
| examples that invented facts | found in a third-party skill being merged | neutral examples written for the skill |
| a request to hide weak results | the kind of request findings section 10 records | the honest form only (section 12) |
| a noncommercial-licensed passage | could not ship in an openly licensed package | an independent rewrite |

## Reference files

- `references/digests.md`: what the digest keeps and drops, caps, record types, redaction patterns, traps.
- `references/mining.md`: slice planning, launch variants, monitoring miners, dead miners, second wave.
- `references/skill-set.md`: from findings to skills: tallies, candidates, boundaries, the spec.
- `references/build-and-review.md`: the build brief, writers, the gate, commands against `--help`, several agents on one skill, bulk replacements, the author's look, the coverage pass (audit, reconcile, repair), revisions.
- `references/tiers-and-integrity.md`: tiers, terms files, secrets, third-party licenses, requests that must not become rules.
- `references/running-the-build.md`: the state file, queue, caps, late findings, the report to the user.
- `references/release.md`: adversarial review, packaging, where to ship, portfolio numbers.
- `references/worked-example.md`: the scale of the original build, step by step.
