# The check

The author's words near the end: "no mistakes allowed anymore", "this is QC". Each slip they find themselves costs
trust in everything they have not looked at. So nothing is sent that has not been through this, even under a
deadline: the scripted part takes a minute.

## Contents
1. The order
2. What the scripts cover
3. Looking at a slide
4. Looking at a clip
5. The request trace
6. Facts
7. What cannot be checked here
8. Independent readers
9. The report

## 1. The order

1. Wait until no clip is being rendered or encoded. Build the deck and its twin.
2. Read the builder's warnings (enlarged pictures, stale fitted clips, lines wider than their box).
3. `audit_deck.py` on both files; `check_pptx.py` on the deck (with the size limit); `own_words_deck.py`.
4. `preview_slides.py` at 1600 px for the slides that changed, in both files; `slide_sheet.py` for the whole deck.
   Read them (section 3).
5. `clip_sheet.py` for new or changed clips. Read them (section 4).
6. Trace the ledger (section 5). Check the facts (section 6).
7. Render the PDF at 3840 px, make the Arial copy, the script and the sources sheet. Look at two pages of the PDF
   and two slides of the Arial copy.
8. Report (section 9).

A problem the audit reports is either fixed or named in the report together with the author's own instruction that
causes it (their eleven-word title, their 26 words).

## 2. What the scripts cover

| Script | Catches |
|---|---|
| `audit_deck.py` | too many words; a title that is missing, too long or not a sentence; a long line; gray or small type; a key term not in italic; a picture or clip near the band, off the slide, enlarged, or over another picture; a click build; a clip without autoplay, that does not decode, or with controls on; dashes, double spaces, repeated words, mixed spelling; every builder warning |
| `check_pptx.py` | a broken package: missing relationship targets, wrong content types, pictures that do not open or are of a kind PowerPoint cannot show (CMYK, 16 bit, interlaced, wrong extension), clips that are not H.264 yuv420p or do not decode to the end, clips without a poster, the size limit |
| `own_words_deck.py` | a sentence on a slide, in a clip or in the notes that is not in the author's texts; stand-ins left in |
| `deck.py` at build | a picture shown above its pixels, a still too coarse for the PDF, a missing clip, a stale fitted clip |

They cannot see meaning. Section 3 is not optional.

## 3. Looking at a slide

Render it and look at the picture itself, at 1600 px or larger; zoom into crops where detail is fine. For each
slide ask, in this order:

1. **The point.** Read only the title, then look only at the picture. Does the picture show what the title says,
   to someone who has never seen these data? If the picture needs explaining, it is the wrong picture.
2. **Keys.** Is every color explained (legend or a word)? Is there a scale bar where there is a sample? Is the size
   of the data given where the sample first appears? Do markers (rings, numbers) mean the same as on other slides?
3. **Collisions.** Does anything lie over anything else: an inset over its own source or over a neighbor, a label
   over data without a plate, content against the band, a panel into the margin?
4. **Balance.** Equal margins and gaps? Is the block centered in its space, or is a third of the slide empty? Does
   any line end in a lone word? Do slides of the same kind look the same on the sheet?
5. **Sharpness.** Any picture soft, blocky or stretched? Fine labels inside pictures readable?
6. **Leftovers.** A stand-in, a placeholder ring, a label from an earlier version, a name that should not appear,
   a white plate, a debugging mark inside a recorded figure.

Do this for the static twin and for the deck separately: they differ, and each has slides the other does not.
Then compare them: a change the author asked for in "the PDF" usually belongs in the deck as well, unless it is a
matter of what each can do.

## 4. Looking at a clip

On the contact sheet of each clip:

- first frame and last frame: sensible as stills (the poster, the resting frame)?
- labels readable, on plates, not cut by the edge, in the author's words?
- anything jumping between frames that should move smoothly? A loop that closes?
- the codec column: H.264, yuv420p, even size; the size at least what the slide shows.

## 5. The request trace

Open `REQUESTS.md`. For each line since the last delivery: find the slide that answers it, look at that slide
rendered, then tick the line. A line overridden by a later one is struck, not deleted. What remains unticked goes
into the report under "not done", with the reason. Twice in the original project a request was dropped for a day
because it was only "remembered"; one of them was the author's own three motivation points.

Requests that are easy to lose: a correction of the event's name (it appears in five places), a change asked "for
the PDF" that also applies to the deck, a person's affiliation, a wording change of two words, "also for slide 3".

## 6. Facts

- Every number on a slide and in the notes against `SOURCES.md` and the record behind it. The sheet is a table
  you write by hand as the slides fill: slide, the statement as shown, the file and place it comes from, and the
  date you checked it. A number without a row is not on the deck.
- Names and affiliations against institute pages; photos against the page they came from.
- The event's name, place and date against the organizers' page or the author's word.
- The QR code: decode it, open the address in a private window. A code that leads to a login page is a dead end
  for the room. If the page is gated, tell the author what has to happen before the talk.
- A statement about what a picture shows ("chosen by score", "three directions of the embedding") in the notes.
- Claims: nothing stated as existing that is only planned; no claim the paper does not make.
- **Visual claims against chance.** A title that says a picture shows agreement ("the types fall into place",
  "neighbors share the region") has a number and a shuffled baseline in the notes and in `SOURCES.md`. In the
  original project this measurement made one title neutral and kept another. See `story.md` section 4.
- **Labels about the rendering** ("1 in N points drawn") are measured on the frame where they stand. One such label
  was true on average and false in the densest view; the clips then printed the real count of their last view.
- **Data stages.** For every sentence with "only", "never", "all" or "alone" about data, name the stage it covers:
  pretraining, fitting a probe, or evaluation. A sentence that says everything shown was learned from one source is
  false when a later stage (a probe, a fine-tune) used other labels; name the stage the claim covers. The same slip
  appeared twice more (a negative line about unused data, a backup table that listed evaluation data under
  pretraining).
- **One rounding per number.** Each number has one printed form across slides, notes, script and pictures. A
  table rounding a value to one decimal beside a sentence giving it to two, on the same slide, was a final-check
  catch. Round once, from the record, at the precision the paper uses.
- **Outside facts were opened.** `SOURCES.md` has a column for each outside fact: opened (with the URL), snippet,
  or memory. Only opened facts go on a slide. A projection that rests on any input that was not opened stays off
  the main slides; one such projection was thrown out ("drop this number ... if you don't have any idea").
- **Licenses.** Every picture, clip or dataset from outside the project has a license that allows the use (for
  example CC BY 4.0 on its record page), recorded in `SOURCES.md` with the page, the author and the license.
  Portraits from institute pages are recorded with the page and image address.

## 7. What cannot be checked here

Say these plainly in the report instead of implying they were tested:

- **The slideshow itself.** Whether clips start, loop and rest, and whether fade-ins run, is only proven by playing
  the deck in the program it will be shown from. In the original project the slideshow was never run in any round,
  and the one report from the author's own screen (Keynote) showed low-quality stills and clips that did not move.
  Opening the file there puts it on the author's screen, so ask before doing it, and press for the author to run
  slides 1 to 3 once in the presenting program well before the talk.
- **A read-back in PowerPoint** is the next best thing. Tell the author first, since it opens on their screen. Open
  the deck through the system (`open -a "Microsoft PowerPoint" DECK.pptx`): a scripted open stopped on the "Grant
  File Access" dialog, and once the deck was opened this way the read-back worked. Then run
  `scripts/ppt_pdf.applescript` with a time limit. It returns, for each slide, the shapes, the movies and the
  animation effects of the timeline's main sequence, and saves a PDF. `scripts/readback_compare.py DECK.pptx
  readback.txt` counts the same three in the file as built and lists every slide that differs. A slide whose
  movie is there but whose effect count is 0 has lost the timing that starts its clip. The read-back proves the
  file imports and keeps its timing; it does not prove autoplay in a show, and the report says so. The slide and
  shape counts were used in the original project; the movie and effect counts are Suggested, not yet tested in
  real work. Without PowerPoint, use the QuickLook previews.
- **Delivery targets.** Name each format that was actually delivered (.pptx, the Arial copy, .pdf, .key) and each
  that was asked for and not delivered. In the original project the .key stopped being delivered for two days
  because Keynote was stuck (`traps.md`), and the reports did not make that plain.
- **Fonts.** The author asked "for pptx also include fonts". python-pptx cannot embed a font, so a built deck has
  none inside it; `check_pptx.py` prints which fonts are embedded. Where the author's PowerPoint offers it (the
  Save options, "embed fonts in the file"), the author can open the finished deck, switch it on and save; only
  fonts whose license allows embedding go in. A deck saved by PowerPoint is a new file: run `check_pptx.py` and
  `audit_deck.py` on it again before it is delivered (the audit checks that every clip still has its timing).
  Always ship the Arial copy beside it as the fallback, and state in the report which fonts are embedded, or that
  none are. The PowerPoint step is Suggested, not yet tested in real work.
- **The hall computer.** Fonts and codecs there. The Arial copy and H.264 are the insurance.
- **Keynote.** An import can drop or change things (see `traps.md`). If they present from Keynote, they should
  open the .pptx there well before the talk.

## 8. Independent readers

When there is time (hours, not minutes) and the author has not declined helpers, let a few independent readers
attack the rendered slides.

**Every brief says this, in these words or close to them:** "For a wording defect, quote the sentence from the
author's texts that should replace it, or write 'needs the author's line'. Never propose new wording. State a
factual correction as what is true, in positive form." In the original project several reviewers returned
rewritten titles and lines, those lines went onto the slides, and the author then banned all of it as "AI slop"
and the deck was rebuilt from the corpus: the costliest round of the project. A correct fact-check phrased as a
negative was rejected; the author wanted the same fact in positive form, with its data stage named.

**Give readers a review package, not the deck**: `review/slides/*.png` at 1600 to 1920 px, contact sheets of every
clip (`clip_sheet.py`), and `review/text.md` with all slide text and the spoken script, slide by slide. Readers do not
open the .pptx or any application.

**Late readers are scope-locked.** Once the look and the slide order are approved, the brief says so: "Do not propose
a redesign or new content: the speaker has approved this style and this order. Report only defects a viewer in the
hall would see." Each defect comes back as slide, location in px, defect, fix. Run this way, the final readers
returned 24 concrete defects and reopened nothing; earlier open-ended "make it world-class" reviewers pushed
restyles that were all rejected.

**Lenses.** It worked when each reader had one lens and none could edit:

- **design**: balance, collisions, legibility from the back row, slides that look machine-made;
- **science**: every statement and number against the paper's source and the records; mechanism drawings against
  the paper's own description;
- **story**: does a listener from this audience follow, where do they get lost, does it fit the slot;
- **text**: every sentence against the author's texts, terms, names, spelling.

For an outside-field talk, readers taken from the room work as well (used once, and it caught the jargon, a
planned feature stated as existing, a number rounded past its source and a missing ask): for example a domain
expert, a practitioner with no ML background, someone from leadership, a talk director, and always one
fact-checker. Write the brief once to a file (the audience, the slot, the facts allowed, the claims not allowed,
the house rules) and point every reader at it.

Give each the review package and the brief file, not your opinion of them. Ask for a numbered list of defects,
each with slide, evidence and the exact fix taken from the author's texts, and a list of slides found clean. The
science lens asks, for every reused figure or animation, which version of the method it shows (a reused animation
showed the submitted version of the model where the talk was about the evaluated one) and checks captions and spoken
text apart from the drawing (a drawing was right while the spoken reach was off by an order of magnitude). A
fact-checker opens primary pages; when a page refuses scripted access, it looks for another primary record
(a filing, the press release) and marks what it could not open.

One writer (you) applies the fixes, except fixes that change the author's words: keep the author's line and report
the disagreement to them ("I kept your wording on slide 16, although one reader wanted 'first' dropped"). Then one
fresh reader does a last readiness pass. Their best catches in the original project were factual: a reach stated
too large, "largest" true by one measure only, a lead smaller than the run-to-run spread presented as a win.

Do not start readers under a deadline, and never to make up for not looking yourself.

## 9. The report

Short, readable on a phone, in this order:

1. The files with paths and sizes. One sentence on what was checked and what was not ("both files pass the
   audits; I looked at every changed slide as a still; I have not run the slideshow").
2. What changed, one line per slide, in the author's words for things.
3. Please check: each reading you had to guess, each name, date or number you could not verify, each place where
   their instruction breaks a general rule (and that you followed the instruction).
4. Not done, with the reason, and what it would take.

No praise of the deck, no list of everything that is fine, no explanation of how the tools work.
