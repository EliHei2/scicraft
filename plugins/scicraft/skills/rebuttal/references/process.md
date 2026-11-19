# Process: polish, do not rebuild

## The rejected rebuild

The most instructive incident of the source work. On the morning the second-round reply was due, the author asked
the agent to understand the strategy in their chat log, add a few points, and run narrative and strategy agents, "but
at the end don't fixate". The author added: "essentially rerun my commands in the md file".

What was done instead, over about three and a half hours: four research agents, three adversarial agents and a
final gate, then five to eight more agents at once (reviewer simulation, chair cold read, clarity, fact check,
rules and voice, closure audit, another fact check, another gate); web research on base rates of score changes; a
red-label reply format borrowed from a public template the author had linked for the preview page only; drafts v1 to
v13; an unrequested comment to a third reviewer; a folder of analysis reports; a 24 KB preview builder. The text
kept moving while the auditors ran, so they reported on stale versions.

The answer, in full: "you made it sooo weird... really bad, the responses I made with chat were so much better, you
did such a bad job, really killed my whole points, make these human, drop the crazy style... just try to polish the
edges ... what you did is super overwhelming and is not even covering the most important points ... don't drift off
from that answer, because that answer was way better than what you made after like 3-4 hours of work." Then: "you
didn't follow the MD ... pick the one that is the most convincing ... You just have to put the best combination
together ... Don't do actually too much."

What went wrong:
1. The author's last chat versions were treated as material for a new text. They were the base text.
2. Auditors were optimized for facts and closure and outranked the author's strategic rules; two items the author had banned were
   kept and "flagged".
3. A style was borrowed from a link given for another purpose.
4. Scope crept to a reply nobody asked for.
5. The author's points were buried, and the result was overwhelming: three new tables, four labeled sections, a complex
   preview.

The fix took ten minutes: both texts rebuilt as light polishes of the author's last version, in their plain style. From then on
each turn integrated one or two of the author's points into the accepted text, and one audit ran per round, briefed: "This is
a final polish. Do NOT propose a rebuild, a new structure, new sections or a new style." The author called the next version
"like 90% good, the evidence the tables all are super nice, just integrate these points". The lesson: when the text
is the author's craft, agents audit the draft; they do not author a new one.

## The procedure

1. **Word-diff the author's latest source against yours.** At the start of every round, copy the author's latest
   downloaded files into a new folder and diff them word by word against the last version you worked on:
   `git diff --no-index --word-diff=plain -U0 last/ latest/`. Keep every change they made ("keep our newest changes
   as much as you can unless sth is obv wrong"), and list any you revert with the reason.
2. **Find the last version.** Pull every version of each text from the chat log or the draft folder, with its turn
   and length (a short regex over the log works), and take the last one the author wrote or accepted. Read it fully.
   When the author says an earlier version was better, collect every version on disk oldest first with its date and
   length, rebuild on the one the author names, and carry forward the fixes the author requested since. One abstract went back this
   way to an earlier shape after a version that listed ranks by scale ("who write an abstract like that??").
3. **Write `RULES_AND_FACTS.md`** from every "never", "always" and "do not" the author has repeated. These are hard
   constraints for every agent and every audit.
4. **Checkpoint before each change**: `checkpoints/replies_vNN_before_<change>.md`. About 20 named checkpoints made
   "go back to the better version" possible in one round.
5. **Edit by exact replacement**: each edit a pair (old, new) that asserts the old text occurs exactly once, applied
   by a script that writes nothing unless every anchor matches, keeping a backup. A multi-file patch whose anchor
   failed reported "nothing applied" and was rerun; it never half-applied. For TeX files the sibling skill's
   `latex-typesetting/scripts/apply_tex_edits.py` applies such an `edits.json`; `scripts/changelog.py` in this skill
   writes the change log from the same file and replays it on the pre-edit snapshot.
6. **List every change** in a few lines in the author's terms. Where a sentence is your reading and not the paper's
   wording, say so ("Cut the clause if you want the bullet to stay with the paper's wording").
7. **Allowed edits**: an error, a number, a pointer, a hard limit, and what the author names. Once the author has humanized a text,
   its wording is frozen: "please change only if you must and it's needed not for bettering it because you cant".
   One round had replaced 37 to 90% of the author's sentences, measured by a sentence drift script, and was reverted by script.
8. **Freeze what the author accepted**: "do not recompute man!! we're good with tables". New points go into the prose around
   the accepted tables and numbers.
9. **When the author takes over**, respect their text and price the risks. When their final note undid three audit fixes, the
   reply listed each with its cost in characters and left the choice to them.
10. **Close the round against the rules file.** Before closing a round, reread `RULES_AND_FACTS.md` and any saved
   notes, and correct every line whose value or decision changed in the round. One note still named the old
   statistics state after the values had changed.

## Recovering a forgotten instruction

When the author says a rule was already given, search the session transcripts (the `.jsonl` logs) with a short
script for the author's earlier message on the topic, quote it in full in the reply, act on it, and write it into
`RULES_AND_FACTS.md` at once. In the source work a terminology rule given in the early afternoon was lost by the
evening and had to be recovered this way. Terminology decisions go into that file the moment the author makes them.

## Taking in new results

When results may have arrived (from a cluster, a co-author, a running job):

1. Use the last delivered PDF as the watermark: `find <project> -type f -newer <last delivered PDF>`, plus files
   changed in the last hour or two in the downloads folder.
2. Convert each co-author Word file with `pandoc X.docx -t gfm` and diff it against the previous conversion to see
   what they changed.
3. Run a control build with nothing changed, to see whether a rebuilt upstream file moved an asserted number.
4. Run the selector (`assets/briefs/selector_brief.md`) and integrate what passes; update `WINS.md`.
5. If nothing new reached this machine, say so in the first line and give the exact fetch commands.

## Bundles sent out for editing

- **A bundle for humanizing** (for the author, a co-author or another model) holds every file that carries changed
  text, at the top level, the appendix included: the full source, a Word file of the same text, the built PDF and
  the figures. Add the `rev_passages.py` list (`NEW_TEXT_TO_HUMANIZE.md`: every marked passage with its section and
  the sentence before it) so the editor touches only new text. One bundle went out without the appendix; the
  author's answer was "add it immediately", and it was rebuilt.
- **When the edited bundle comes back**, extract it into its own dated folder (`returned_YYYYMMDD/`), read its
  notes, and `diff` each file against the copy you sent, so you know exactly what the author changed. Build on the
  returned text. Keep your own vector figures when the returned figures are rasterized copies. Apply any fix you
  still need as exact replacements, re-resolve every line token, re-run the number checks, run one focused audit
  (section 10 of `SKILL.md`), and list each fix in one line.

## Deliverables and scope

- List the deliverables at the start and keep to them. "don't make a complicated doc only the message ... and the AC
  and the new message of [the reviewer] hidable. that's it."
- An idea for an extra item gets one line in the report; it is never built unasked.
- Do not adopt an outside template or skill for a purpose the author did not name. Read a reference link for the narrow
  purpose given and ask before borrowing its style for anything else.
- Relayed advice from co-authors and senior authors is input to weigh: pull the idea out, check each factual phrase
  against the record, integrate it in the author's voice. "don't fixate, just consider" came with every pasted
  thread.
- Keep the governing request in charge. Before rewriting a summary, restate the document's one purpose and check
  the draft against it, not only against the latest message ("you fixate on the little things I tell you and then
  you completely diverge from the whole point").
- When a request can be read narrowly or broadly, take the narrow reading. "explain what each term is, underneath
  with brackets" meant the total loss only, not every equation.

## Deadlines

- **When the author says finalize, deliver the artifact first.** "but first finalize the pdf and give it to me!"; "no
  adversarial reauditing just the fixes. go". Report a running audit in one line and apply its findings only if it
  reports a factual error.
- **Near the end, show text before building.** "do not rebuild yet, rebuild when I accept your work ... be faster
  in these iterations". Hand over the drop-in LaTeX block with its revision macros intact, say which passage it
  replaces and its effect on lines and the page budget, then on "yes" apply, rebuild and re-resolve line numbers in
  one pass. If a build ran after "do not rebuild yet", say that nothing from it was sent and offer the restore from
  the backup.
- Do not trouble the author with logistics they can handle ("I'll compress it it's fine. Please focus on the content!!!").
- Every deliverable is handed over: the file, its absolute path, what to upload where, the size limits. Three
  "where is ..." messages in seven minutes came from files built and never surfaced.
- After an interruption (a dropped connection, a sleeping laptop), resume the pending step at once without a recap.

## Agents

- **Take the narrative spine from the author before any agent writes**: the claims in their order, in their words.
  Then one narrator agent, told that it is not a critic ("not an adversarial ... a narrator that really connects
  the points"), explains why each experiment exists. It reads the project's design and pre-registration notes and
  returns `NARRATIVE.md` (the project's narrative file, defined in the sibling skill,
  `project-structure/references/governing-documents.md`), a short argument section, a proposed summary and a claims
  ledger listing every claim it had to weaken. Copy the through-line into the shared brief so every later agent
  writes to it.
- An agent swarm is for evidence mining and simulation, not for authoring the reply. Default to one focused audit on
  the author's polished draft; fan out only when the author asks in so many words, and never under a deadline.
- Before fanning out writers, write a shared brief (`assets/briefs/shared_brief.md`) and build one exemplar output
  that every agent copies. Launch agents whose inputs depend on others only once those inputs exist.
- Auditors are read-only and report location, quoted text, problem and exact replacement. One writer applies changes.
  When an auditor and an editor could touch the same files, split the phases: audit only, then edit after release.
- Forward each new instruction from the author to every running agent, quoted in substance, labeled binding.
- Put a word cap in each brief and measure the answers (one set of agent answers had a median of 95 words, up to
  165); ask agents to list the rules of the brief they broke.
- **Look at every agent output before relaying it.** Looking means: open the returned image and its caption,
  rebuild and render the page where it lands, and grep that page's text for the brief's banned words. One figure
  agent returned an ablation panel with 14 dots per row that buried the bars; the lead replaced them with one
  worst-to-best line before relaying it.
- One writer for the text. When two sessions (a laptop and a compute cluster) worked on the same round, the cluster
  session supplied evidence and audits only and its prompts said "must not edit TeX or replies"; the laptop session
  wrote. Before reassuring the author, compare the files and say where the current version is in the first line.

## A reply document built from scratch

When the replies need an internal document with new figures and tables (a report for co-authors, built before the
posted text), this order held in the source work:

1. Read the code that produces the changed result (for a training change, the code that assembles the loss), so
   "what changed" reflects what runs.
2. Write the shared style, composer and table modules.
3. Build one exemplar panel; check that every font is embedded and none is Type 3 (`pdffonts`).
4. Test-compile the preamble.
5. Write the shared brief (`assets/briefs/shared_brief.md`).
6. Fan out one code-against-paper verifier for the change table, one agent per figure and one per table.
7. Launch the answer writers once the tables exist.
8. Edit everything into one voice: the answers went from 62 to 44 to 13 over successive rounds.
9. Run separate look and content audits in parallel, then rebuild and read every page.
