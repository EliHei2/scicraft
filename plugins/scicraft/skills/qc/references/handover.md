# Handing over

The last step decides what the author receives. The two failures here were the worst-received of the source work:
the wrong kind of deliverable built from a reading of a word, and a file the author had seen destroyed.

## Contents
1. Match the example
2. Names, versions and backups
3. The delivery folder
4. Size limits and channels
5. Text the author will paste
6. Remote writes
7. The message that goes with it

## 1. Match the example

Before producing a deliverable that has an existing example (a colleague's tables, an earlier deposit, last
round's package, the venue's template), open the example and match its type, granularity and count.

1. List the example files with row counts and column headers:

```bash
for f in example/*.csv; do printf '%s  rows=%s  cols=%s\n' "$f" "$(($(wc -l < "$f") - 1))" "$(head -1 "$f")"; done
```

2. Write one line per file on what kind of thing it is (gene list, parameter table, dataset table with links,
   enrichment result, benchmark table per task).
3. Set a target count from them and say it before building ("five to fifteen short reference tables").
4. Stage the delivery through an explicit whitelist file, and deliver only what is on it.

Why: "source data" was read as the plotted values of every panel; 73 files of coordinates, transcripts and
outlines were built and uploaded where five to fifteen short reference tables were wanted. The correction was the
harshest of that week ("understand the context"). The final deposit held 14 files, duplicates removed (one gene-pair
list equaled a subset of another, so only one went up). Heavy per-item data stayed local, "if a reviewer asks".

When a request has two parts ("tables are something, data are something else"), they go to separate folders, with
separate manifests, through separate channels: small tables from the laptop with checksums, bulk files by the
machine that holds them.

## 2. Names, versions and backups

- **Never rename, delete or overwrite an output the author has seen.** Build scripts take an output name; every
  variant gets a suffix (`fig3_noboxes.pdf`, `fig3_counts.pdf`); every delivery round gets its own name or folder
  (`round9/`, `Deck_r3.pptx`). Delete only when the author asks.
- **Back up before regenerating.** When a disk filled during a figure build, two composed PDFs were truncated; the
  scratch backup restored them, verified with `cmp`.
- **Keep earlier designs.** `figures/alt/`, `retired/`, versioned code folders (`code_r8/v11/`). "Bring back the
  previous one" must be possible in one copy.
- **Check for an open file before writing next to it.** A PowerPoint lock file `~$Name.pptx` means the deck is
  open; overwriting it gave "the picture can't be displayed". Never open a half-built file in the author's own
  application (it appears on their screen).
- **One writer per output file.** An old figure function left in a default build list overwrote the new figure
  another script had written.
- **A build announced as not final** (the author asked for the package mid-loop) may be followed by fixes under the
  same names in the same folder, because the author was told. Keep the not-final copy in `retired/`.

## 3. The delivery folder

- One folder holds what is current. Move superseded deliveries to `_work/roundN_superseded/` or `retired/`.
- A package for a paper round held: the PDFs, a light PDF, the replies as Markdown and Word, the changed-files zip
  for the online editor, `tex/`, `figures/`, the preview, and `NOTES.md` with every change.
- **Test the package in a clean folder**: unpack the changed-files zip over a copy of the previous project, compile,
  and compare page count, undefined references, where the main text ends, and the revision colors with the
  delivered PDF. Say which packages were missing locally and that line numbers could shift on the author's machine.
- **Say which file to upload**: "Upload THIS file as the revised paper: paper_revised.pdf".

## 4. Size limits and channels

- Know the cap of the upload (a venue's 50 MB, a publisher's limit) and of the channel the file travels
  through (a send tool capped at 30 MiB).
- A paper PDF over the cap: recompress images and keep vector content (PyMuPDF `rewrite_images(dpi_threshold=130,
  dpi_target=110, quality=70)`, then `save(garbage=3, deflate=True)`; `clean=True` broke a pattern resource). At
  150 dpi one book was still 64 MB. Split by chapter using the outline when the channel cap is smaller than the
  document.
- A deck over the cap: lighten what nobody looks at (poster frames of clips), then bitrate, never pixels (detail in
  `talk-slides`).
- `pdffonts` after any recompression: every font still embedded.

## 5. Text the author will paste

Copying from a chat window into a document editor carries its typesetting and background ("if I copy paste from
your thing to my google docs it also copies the typeset and background"). Write text the author will paste into
the deliverable itself: a plain Word file with the Markdown typed out literally, plus a `.md` file. A rendered
preview of how a platform will show it (an HTML card page screenshotted) is labeled as your rendering, not the
platform's.

## 6. Remote writes

- Read a prompt line by line before handing it to an agent that runs with the author's credentials; give it a hard
  scope (one destination folder), copy-only rules, a dry run that writes its plan first, and stop conditions.
- Dry run, then say exactly what will change: "4 new files, 2 updates of our own files, and nothing else is
  touched."
- After the upload, verify one-way checksums (`rclone check --one-way --checksum LOCAL REMOTE`) and report "all N
  files identical to the local copies". Never touch a colleague's files; deletes go to the trash.
- Rename a superseded prompt (`PROMPT_superseded.md`) so no agent can run the old one.
- Commands the author pastes are one line each, or one script run by path; say what success prints. A two-line
  rsync pasted without its continuation copied a 21 MB file over a 9.9 GB one.
- **Write commands for the author's own machine.** The stock `rsync` on macOS (2.6.9) has no `--chmod`, and
  macOS has no `timeout`; check the OS before handing over a command.
- **Say when an earlier instruction has gone stale.** When a later step has already done the job of an earlier
  instruction, say in the same message that the earlier one is now stale. An append (`cat >> config`) left standing
  after a plain copy had worked would have duplicated the config section.

## 7. The message that goes with it

Short, readable on a phone, in the shape of `assets/delivery_message.md`. Lead with what was delivered and where,
or whether it is live. If the author is waiting on a background job, give a one-line status before they ask: done
and verified, still running and why, what is in their hands.

- **Send the list of your own unconfirmed additions with every delivery.** Keep a running list of what you added
  that the author has not confirmed (a sentence, a table row, a label, a credit), and send it each time, under "What
  I did on my own judgment". A credit taken by an agent from another paper's acknowledgements was applied and then
  rejected by the author; the other unconfirmed credits were listed after that.
- **A disclosure the author wrote is the author's to cut.** Report it in one line and leave it in place ("that one
  is [theirs] to cut, not mine"). Removing it on your own judgment changes what the document discloses.
- **Correct a wrong interim detail in the final report.** A detail misstated in an interim message gets its own
  caveat line in the final report, with the wrong and the true value (a canvas growth reported as 1.7 mm was
  2.8 mm). Silently using the true value leaves the author holding the wrong one.
- **Never end a turn without a deliverable or a stated next action.** One turn ended after research tool calls
  with only "No response requested", and the author had to type "continue!". If work is still running, the last
  message says what is running, what it will produce and when.
