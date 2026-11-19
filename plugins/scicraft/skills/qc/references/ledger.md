# The request ledger

Notes arrive faster than they can be applied, typed on a phone, sometimes dictated. Sessions get compacted or hit
a usage limit. In the source work a request that was "only remembered" was dropped for a day twice; once it was the
author's own three motivation points, once a terminology decision given at one o'clock and broken by five. The
ledger is the defense: every instruction in the author's words, appended before acting, ticked only after looking.

## Contents
1. The file
2. Reading a note
3. Overrides and standing rules
4. Tracing before delivery
5. Rebuilding from a transcript
6. What goes to memory afterwards

## 1. The file

`REQUESTS.md` beside the deliverable (`assets/REQUESTS_template.md` is a blank one). One line per instruction, in
the order given, with the time, in the author's words, typos included: the wording is the specification.

```
## Standing rules
- one statistics language: "significant" means adjusted p < .05, one correction method   (guard: grep "Holm|q =|whisker")
- every change from the submitted version in one light blue                             (guard: color check on the PDF)

## Requests
- [x] `13:45` dont say backbone, keep the term the submitted paper used          -> paper, figures, replies (looked: p. 3, 7, Fig. 2)
- [~] `17:31` call the auxiliary target "column statistics"                   (overridden 21:18: "the per-column mean and variance it predicts")
- [x] `21:18` the per-column mean and variance it predicts ... across the board  -> replies 1 to 3, paper l. 112, 340 (looked)
- [ ] `21:38` cite every architecture by name and year when it is introduced     NOT DONE: two of five; bib keys missing, asked
```

- `[x]` done and looked at, with where; `[~]` struck by a later line, kept readable; `[ ]` open, with the reason.
- Append first, act second. A note acted on before it is written down is the one that gets lost when the next
  three arrive.

## 2. Reading a note

- **Which unit, which file?** Authors number pages or slides as in the file they are looking at. After a reorder,
  their numbers refer to the new order. If unsure which version they see, check what was last sent.
- **What exactly?** Change what the note names and nothing around it. "is chosen -> should be" is two words.
- **Literal first.** When a note can be read two ways, take the literal reading, act, and state the reading in the
  report ("I read X as Y"). Ask only when both readings are expensive and a wrong guess cannot be undone in one
  more note. When offering the other reading, name its problems up front.
- **A complaint is a requirement.** "What's the point of what you're showing?" means the picture fails; fix it.
- **A repeated note** means the last fix did not land where they are looking. Check that the file they have is the
  new one before changing more.
- **"Bring back", "the old one", "the OG"**: find that exact version on disk and restore it; do not approximate.
- **Dictated text** has speech-to-text errors; decode them from context and flag every guess.
- **A misremembered name** (a paper named by a word that only sounds like its title): find the likely match and
  say so explicitly.

## 3. Overrides and standing rules

- A later note overrides an earlier one. A specific note overrides a general rule; the report says that the
  instruction was followed against the rule.
- A pasted text from the author is the latest version even when it silently drops their own earlier edits. Put it
  in as given and list exactly what it reverts (a pasted summary once dropped a dozen of the author's own one-phrase
  edits; the author did not restore them, but knew).
- Standing rules go at the top of the ledger and into a guard the build runs: a grep over the extracted text, a
  build check, a configuration value. A rule that only lives in the ledger comes back.
- A rule given for one place holds everywhere. A correction to the event's name reaches the title, the footer, the
  notes, the script and the file names; a term change reaches figure labels, table rows, code identifiers and data
  keys on the site. Sweep, then guard.
- Write terminology decisions down the moment they are made, and check them before each round.

## 4. Tracing before delivery

For each line since the last delivery: find the unit that answers it, look at that unit rendered, then tick it.
What stays open goes into the report under "not done", with the reason. Requests that are easy to lose:

- a correction of a name that appears in five places;
- a change asked "for the PDF" that also belongs in the source deck, or the other way round;
- a two-word wording change inside a long paragraph;
- "also for slide 3", "same for the appendix";
- a rule stated in passing inside a longer complaint;
- a request from a co-author relayed by the author ("my supervisor says one page max").

## 5. Rebuilding from a transcript

When a session was cleared, compacted, stalled or killed by a usage limit, recover the notes before doing anything
new. Claude Code keeps transcripts at `~/.claude/projects/<project folder>/<session id>.jsonl`, times in UTC.

```bash
ls -t ~/.claude/projects/<project folder>/*.jsonl | head -3        # the newest sessions
python3 <skill>/scripts/ledger_from_transcripts.py SESSION.jsonl --since 2026-11-17T05:00 --out REQUESTS.md
python3 <skill>/scripts/ledger_from_transcripts.py OLD.jsonl NEW.jsonl --out REQUESTS.md   # across a compaction
```

The script keeps the author's messages only (no subagent traffic, no system reminders, no exact repeats, no nudges
like "go" shorter than 14 characters and four words). Then mark by hand what later lines override, and tick only
what you can see done in the files.

Messages typed while an agent was busy may sit in the transcript without ever having been acted on. After a crash,
search for them explicitly and answer the author with what was recovered ("none of your messages were lost", or
the list of those that were). To find one earlier message on a topic:

```bash
python3 - <<'EOF'
import json, sys
for line in open('SESSION.jsonl', 'rb'):
    d = json.loads(line)
    if d.get('type') != 'user' or d.get('isSidechain'): continue
    c = d['message']['content']; t = c if isinstance(c, str) else ' '.join(b.get('text', '') for b in c if isinstance(b, dict))
    if 'backbone' in t.lower(): print(d['timestamp'][:16], t[:400], '\n')
EOF
```

## 6. What goes to memory afterwards

The looks the author chose and rejected (in their words), standing rules, where their texts live, how ambiguous
notes were read, tool traps. Not the content of the deliverable and not a log of the rounds. When a rule changes,
fix the stale note before closing the round: a memory entry still naming the old statistics state after the
values changed was caught only at the end of a round.
