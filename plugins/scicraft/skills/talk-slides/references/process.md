# Process

How the work actually goes: the author looks at a PDF on a phone, sends short notes in bursts, and wants the next
version in minutes. The deck converges through ten to twenty such rounds. The craft is in losing nothing and
changing nothing they did not ask for.

## Contents
1. The request ledger
2. Reading a note
3. The loop
4. Status lines
5. Under a deadline
6. Recovering a session
7. Helpers
8. What to remember afterwards

## 1. The request ledger

`REQUESTS.md` in the talk folder holds every instruction in the author's own words, with the time, in the order
given. Append before acting. It exists because notes arrive faster than they can be applied, sessions get
compacted, and "I remember that one" is how requests vanish.

```
- [x] `05:15` research day 2027*                               -> title slide, band, notes, file names (looked: 1, 2)
- [x] `05:24` for 10 drop the text about who made the data ...   -> slide 10 subtitle
- [~] `05:21` slide 6 in pptx should be the new architecture clip (overridden 06:24: "the og one ... website colors")
- [ ] `06:33` for query ... move the pointer across the picture  NOT DONE: needs a new clip, about an hour
```

- Tick a line only after looking at the slide that answers it.
- A later note overrides an earlier one; strike the earlier, keep it readable.
- A specific note overrides a general rule ("max 25 words" yields to a line they dictate for that slide). Say so
  in the report.
- Standing rules the author states once ("no gray small text", "the method's name always italic") go at the
  top of the ledger and into the builder's configuration, so a script enforces them.
- `requests_ledger.py TRANSCRIPT.jsonl SINCE REQUESTS.md` rebuilds the list from a session transcript.

## 2. Reading a note

Notes are terse, typed fast, sometimes dictated. Read them as specifications:

- **Which slide?** They number slides as in the file they are looking at (usually the PDF, where page = slide).
  After a reorder, their numbers refer to the new order. If unsure which version they see, check what was last
  sent.
- **Which file?** "For the pdf" limits a change to the twin only when the change is about what a PDF can do. A
  wording fix or a legend applies to both.
- **What exactly?** Change what the note names and nothing around it. "is chosen -> should be" is two words.
- **Literal first.** When a note can be read two ways, take the literal reading, act, and state the reading in the
  report. Ask only when both readings are expensive and wrong guesses cannot be undone in one more note.
- **A complaint is a requirement.** "What's the point of what you're showing?" means the picture fails the test of
  `pictures.md`; fix the picture, do not defend it.
- **A repeated note** means the last fix did not land where they are looking. Check that the file they have is the
  new one before changing more.
- "Bring back", "the old one", "the OG": find that version in the talk folder and restore it; do not approximate.
  The author may compose the next deck from slides of several versions ("from the new version slides 6, 8, 9, 10,
  13 are great", "from the OG version the first slide"). That works only if every delivered version survives:
  keep `deliveries/vN/` with its deck, its PDF, a copy of its builder and its slide sheet, and never overwrite a
  clip that a delivered version uses (write `name_v2.mp4` instead).

## 3. The loop

1. Append the notes to the ledger.
2. Sort them: text changes (seconds), layout changes (minutes), new stills (minutes), new clips (long).
3. Apply everything that is seconds or minutes, in one pass over the builder. Start long renders in the background.
4. Rebuild both files, run the audits, render and look at the changed slides.
5. Send the PDF with a report of a few lines. Do not wait for the long renders: say what is still rendering.
6. When a render lands: wire it in, rebuild, check, send again.

Keep the loop short. One builder file, edited in place; a build of seconds; previews of the changed slides only.
Do not regenerate what did not change. "Polish, don't rebuild": a three-hour rebuild in a new style was rejected
in favor of the previous version with the named changes.

Put the delivered file in front of the author the way they read it. If they follow on a phone, send the PDF there.

## 4. Status lines

While working, the author sees nothing. Say in one sentence what you are doing, about once a minute during long
steps, and when something finishes. Lead with what they can use ("Both files build; fixing the legend, then the
PDF"). Never go silent for many minutes: "you going?" was typed after four.

## 5. Under a deadline

When the author has minutes:

- **Hand over what builds now.** A correct deck from an hour ago beats a better one that is not finished. Then
  iterate on their notes.
- Do the scripted checks anyway; skip only what takes long (independent readers, new clips).
- Do not start helper agents or new long renders on your own initiative, even if they asked for helpers earlier:
  in the original project an agent launch during the last minutes was declined.
- **If the author asks for a fleet under a deadline anyway**, cap the heavy work at what the machine can run: at
  most two encodes or recordings at once on a laptop; read-only checking helpers may run beside them; production
  helpers wait in a queue. Say so in one line. In the original project six helpers with nine-minute deadlines ran
  beside four heavy clip renders and several fitting passes; a headless recording crashed under the load, the
  session stalled for about an hour, and the author broke it off. The recovery session delivered in about fifty
  minutes with fewer parallel encodes, lighter poster frames instead of refitted clips, and the clips untouched.
- Fix by the cheapest means that keeps quality: a lighter poster frame instead of re-encoding a clip, a panel
  layout instead of a new animation.
- Use a new file name for each delivery if their presentation program may have the previous file open.
- Report in five lines.

## 6. Recovering a session

When the conversation was cleared or compacted, or a previous session stalled:

1. List the talk folder by time. What was built last, what is half-written?
2. Rebuild the request list from the transcript (`requests_ledger.py`), from the last delivery on.
3. Find where the work stopped: the last tool calls in the transcript, unfinished recordings (count the frames),
   stale fitted clips, a builder that was patched after the last build.
4. Build what exists before starting anything new, so there is something to hand over.
5. Then continue down the ledger.

Processes of the old session may still run (local servers for recorded sites); reuse them, do not start duplicates.

## 7. Helpers

Helper agents are worth their cost in three places:

- **independent readers** before a delivery that matters (see `check.md` section 8), read-only, briefed to quote the
  author's sentence for any wording defect and never to supply new wording;
- **one contained production task** that runs beside your own work: a single slide rebuilt in a sandbox copy of the
  builder and handed back as a block to paste, or a single clip;
- **research on outside facts** (the history of a method, use cases for the room). The brief carries a privacy
  rule: web queries are generic and never contain the model's name, the author's name or any unpublished detail.
  Each item comes back ranked, with a status tag (`[shown in the paper]` or `[planned]`), a source marked opened,
  snippet or memory, and a "do not claim" list. Save each hand-back to a notes file in the talk folder before using
  it, because the session will be compacted.

The production brief that worked, as a template:

```
Deliver in [N] minutes; if something is at risk, ship the simpler variant and say so.
Stay in your own files: do not edit the builder, the words file, the deck files or anyone's render scripts.
Work in a sandbox copy of the builder (build/[x]_sandbox.py writing _[x].pptx and notes_[x]/); hand back a block to paste.
Do not open PowerPoint or Keynote, do not kill any process, do not stop the local servers.
Exact specs: [each panel exactly W x H px on ground RRGGBB].
Report every deviation from the spec and why. Write no sample names.
For any wording, use only sentences from build/corpus; where none fits, write 'needs the author's line'.
```

Rules that kept this from going wrong: one writer for the builder; a helper writes only new files under its own
name; give it the files and the author's words, not a summary; cap what it may run at once (two encodes or
recordings on a laptop), because parallel renders slow each other down until recordings time out. Many authors do not want fleets of helpers at all: ask
once, remember the answer.

## 8. What to remember afterwards

If there is a memory to write to, keep what will change the next talk for this author:

- the look they chose and the looks they rejected, in their words;
- their standing rules (word limits, forbidden terms, how they want claims stated, who is thanked how);
- where their texts, figures and earlier decks live;
- the readings of ambiguous notes that turned out right or wrong;
- tool traps met on their machine.

Not the content of the slides and not a log of the rounds: the files hold that.
