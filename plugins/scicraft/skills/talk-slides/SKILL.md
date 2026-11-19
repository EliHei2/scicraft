---
name: talk-slides
description: Builds, polishes, checks and delivers the slide deck of a scientific talk, from one builder file that gives a PowerPoint deck whose clips start by themselves, a static PDF twin, a speaker script and a sources sheet. Use it whenever the user asks for slides, a deck, a talk, a presentation or a keynote (a lab meeting, a conference oral, an institute day, a talk to clinicians), wants a paper, poster or website turned into a talk, sends notes on slides (slide 5 is ugly, too much text, make it cleaner, swap 4 and 5, this looks like AI), wants zoom-ins or animations, needs a deck smaller, as a PDF or safe for a hall computer, or is close to a deadline, even if they only say the slides. Holds one point per slide in the author's own words, a picture that proves it, legends and scales, no gray or small text, an audience switch for talks inside or outside the field and a tested builder with audit scripts. Prefer it over generic slide skills; use poster for posters and data-figures for the charts themselves.
---

# talk-slides

How to make the deck of a scientific talk so that its author sends it without rewriting it. Distilled from
fifteen rounds of notes on one eight-minute talk for an audience outside the field. Almost
every rule here is something the author asked for or something the author threw out, so each comes with its
reason. Where the author of the talk at hand says otherwise, they win: write their rule into the request ledger
(section 8) and follow it.

> **PRIME DIRECTIVE: every slide makes one point, in the author's own words, that the audience can check with their
> own eyes.** The title says the point as a sentence. The picture shows it. Nothing else is on the slide.

The failure to fear is a deck that "looks like AI slides": claim cards, three columns with bold headers, a redrawn
chart, a blue punchline, small gray captions, a picture that decorates instead of proving. An author spots it in a
second and stops trusting the rest. Section 9 lists what was thrown out and what replaced it; read it before
designing anything.

Three failures cost the most time in the original project. Guard against them from the first minute:

1. **Writing for the author.** Text composed for someone reads as machine-made to them however well it is edited.
   Every sentence on a slide is theirs (section 2).
2. **Restyling.** "Make it cleaner" means remove things inside the look they already like. A new look, a new
   typeface or new layouts were rejected every time (section 4).
3. **Losing a request.** The author reads the PDF on a phone and sends ten short notes in five minutes. Each one is
   a requirement. Keep a ledger and trace every line before anything is sent (section 8).

## 0. Before building

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The author's texts**: the paper (TeX preferred), the poster, the book, the website, and the folder of their
  earlier talks. These are the only source of words (section 2). Note which earlier deck they liked: its look is the
  look.
- **The pictures**: the paper's figures as PDF, the data and color rules of its showcase example, animations that
  already exist (a project website often has the best ones).
- **The records behind every number** the talk will state.
- **The occasion**: the event's name exactly as the organizers write it, the date, the length of the slot, who sits
  in the room (this sets the audience switch, section 1), how the deck reaches the hall (an upload portal with a
  size limit, an email attachment limit, often 20 to 25 MB, so a large .pptx needs a link; a hall where a technical
  team streams every talk from its own machine) and which program shows it (PowerPoint, Keynote, a PDF viewer).
- **People**: who is thanked, with what role, and photos of them; which logo may appear.
- **What may be shown**: unpublished results, patient or in-house data, anything under review.

Then show the author the outline before building: a table with one row per slide, giving its role, its title
sentence (taken from their texts) and its one picture. Changing a row costs nothing now and an hour later. If the
author cannot be reached, build from your outline and put that table at the top of the report.

Work in a folder of its own beside the paper, never inside its repository:

```
talk_<event>/
├── build/      build_deck.py (copy of scripts/starter_deck.py), deck.py, the render scripts, corpus/, notes/
├── media/      clips (.mp4), media/posters/, media/stills/, media/fit/ (clips fitted to a size)
├── assets/     figures, portraits, logos
├── REQUESTS.md   the ledger of the author's instructions
└── <Name>_<Event>.pptx, _windows.pptx, .pdf, TALK_SCRIPT.md, SOURCES.md      what is delivered
```

## 1. The story

**Set the audience switch first.** `outside-field` (clinicians, an institute day, leadership, funders, a mixed
room) is the tested setting and the default. `in-field` (a reading group, a lab meeting, a conference oral) keeps
every rule of look, words and pictures and changes four things: formulas, results, backup and terms
(`references/audience.md`; the in-field column is marked "Suggested, not yet tested in real work" where it has no
evidence). When unsure, build outside-field: an expert follows it, and the reverse fails.

The arc that works. A slot of N minutes takes about N + 2 slides at 30 to 50 seconds each; an eight-minute talk is
a title, ten slides and the ending. The author gave the same order in a note: problem, data, idea, results, outlook,
acknowledgements, "adjusted for 8 mins".

| Slide | Holds | It fails when |
|---|---|---|
| Title | the name, what the work lets people do, speaker, event | it carries a tagline |
| The stake | what is measured and why it matters now, on the real data shown whole | it opens on the method, or on a narrow technical sub-problem |
| The question | the one question the talk answers | the question and its answer both stand on the slide |
| The idea | one sentence the audience can repeat, the work's own term introduced once | it needs a formula (outside-field) |
| How it works | one picture (the paper's own figure or animation), the scale of the data | it lists components |
| Results, three or four | each one claim made visible: first what the audience can verify themselves, last the comparison as one number | a result needs three caveats |
| What comes next | what exists already, what it could become for this audience, who made the data | it is a list of plans |
| Acknowledgements | people with faces and roles, compute, the announcement, a QR code | it says "Thanks!" and "Questions?" |
| Backup | one likely question per slide: the table, the ablation, the math | |

Rules that shaped it (detail and examples in `references/story.md`):

- **Start where the audience is.** An outside audience knows the measurement or the task, not the model. Show the
  raw data (the benchmark's tables, the tissue, the scans) before anything computed from it.
- **Frame the problem as the paper's introduction does.** Shrinking it to a technical step the audience finds
  boring was called "such a reduction". Re-read the introduction and the poster's abstract first.
- **Order: need before answer, principle before the named idea.** For each neighboring pair ask what question the
  first slide leaves open; the second must answer exactly that. When the author swaps two slides, this is why.
- **One line of thought per slide.** A question and the statement that answers it, both large on one slide, read as
  filler. Keep the question; say the answer.
- **No formulas on the main slides outside the field.** The "technical touch" is the paper's own architecture
  figure; math waits in backup. In-field, the paper's definitions and labeled loss may come forward.
- **State the strongest claim the records support, once.** "First" when it is first, not "among the top three"; never
  "first at everything" when it is second somewhere. A weak or mixed result moves to backup with its number and an
  honest answer ready; it never leaves the record. Every stated number has a line in the sources sheet.
- **Real numbers or none.** "Drop this number ... if you don't have any idea." Use the real total of the thing named
  (the dataset's full row count, not the sample a rendering drew). Numbers go in the order of the argument (sources,
  datasets, kinds, units, measurements), each large, with its unit.
- **The future slide shows assets**: the data that exist, the people who made them, what the host gains.
- **Time it.** Each note starts with its seconds; `talk_script.py` adds them up against the slot.

## 2. Words

**Every sentence on a slide is the author's own**: pasted from their paper, poster, book or earlier slides and
shortened only by cutting, or dictated by them in the conversation and kept as given. Do not paraphrase, merge two
sentences, add a connective or reorder a dictated line. In the author's words: "you are only allowed to use text
that I have used in my previous slides or poster or paper." `references/words.md` has the procedure and examples.

- Build the corpus first (`corpus_extract.py`), then choose. Titles come from section titles, bold captions,
  abstract sentences and their earlier slide titles.
- **The title is the point**: one full sentence, fact or question, at most 10 words.
- **At most 25 words on a slide**, counting the words visible in its clip; names of people and labels of data do not
  count. **Every sentence on a slide has at most 10 words**, the title and the lines under it alike (the audit
  counts the words of each sentence, not of each rendered line; `Deck(max_line_words=...)` changes the limit if
  the author allows longer). A longer thought is spoken, not shown. No footnotes, no caption lines. The author once
  said 30; the skill settled on 25 and that is the latest.
- **The work's own term is set in italic everywhere**, including inside pictures, and it is the only italic.
- **One name per thing.** Working names of internal variants and baselines stay off the slides.
- Words drawn inside pictures and clips are text too: keep them in one file and check them with the rest.
- Names of people are spelled as on their institute's page; affiliations are current; roles are as the author gives
  them; nobody is given a role they did not have.
- Speaker notes are the author's sentences as spoken text; your own cues go in [brackets].
- Record the source of every sentence in the builder (`own()`); `own_words_deck.py` then proves the rule or lists
  what breaks it. Without the author's texts at hand (a round of notes on a deck you did not build) run it without
  `--corpus`: it lists stand-ins and dictated lines, and the report says the rest was not checked. For display copy
  outside a deck (a site, a poster, a page), use `own_words.py` from the sibling `author-voice` skill; both read the
  corpus that `corpus_extract.py` writes.
- Run the `humanizer` skill on anything you had to compose yourself (cues, messages to the author, the sources
  sheet), never on the author's sentences.

## 3. Pictures

Ask of every picture what the author asked: **"what is the point of what you are showing?"** The picture must make
the title's claim visible to someone who has never seen the data. The patterns that did this, with an instance from
machine learning beside the one they came from (`references/pictures.md` has each in detail):

| The claim | The picture that shows it | ML instance |
|---|---|---|
| the data are vast and varied | the whole corpus or sample with its size in a box (units, measurements, features), then zoom-ins down to the finest unit | the pretraining corpus as a grid of its tables, with rows, columns and sources counted |
| our view agrees with the expert's | the same input twice, expert labels and the method's output, split by a divider that moves | human labels against model predictions on one image or one table |
| it finds similar things | the whole view with the query ringed and its matches numbered, and zoom-ins of the query and of two matches found elsewhere | a retrieval query and its top matches from other datasets |
| different objects share one space | one picture of that space with each kind of object marked, and a key | rows, columns and tables as points of one embedding |
| it works at any unit | the same window drawn as units of different size | the same input tokenized at three granularities |
| it generalizes | three samples side by side in one visual grammar, each with its size | three held-out benchmarks in the same layout |
| it is better | the ranks per task with the method on top, the one number in the line under the title | the rank heat map of the benchmark table |
| how it works | the paper's own figure, recolored for the ground of the deck, every component visible | the architecture figure of the paper |

- **If a color means something, say what.** A legend on every slide that uses categorical colors; a word for what a
  color scale encodes. Keep one palette across slides so the audience carries the legend with them.
- **Every picture with a physical or data scale carries it**: a scale bar on a plate in the ground color, inside the
  picture, or the units and denominators of a chart. The size of the data stands with the first whole view.
- **Zoom-ins never cover what they zoom from**, and nothing lies over anything else by accident.
- At the finest level draw units as thin light outlines, never as filled translucent shapes ("only mask boundaries,
  thin white").
- **Never redraw the author's figures and never place a figure on a white plate in a dark deck.** Reuse the paper's
  figure (`dark_figure.py`) or a frame of an existing animation. Charts that must be drawn new follow the
  `data-figures` skill; schematics follow `canvas-schematics` or `tikz-figures`.
- **Resolution**: no picture is shown larger than its pixels; for the PDF twin aim at two pixels per slide pixel. The
  builder warns, the audit fails.
- **When no figure exists yet**, draw plain panels from the paper's own numbers (one mark per patient or per run, a
  timeline to scale), say in the notes and the report what is drawn to scale and what only shows an order, and
  never invent a value. A point with no honest picture gets a statement slide (`s.statement`): the sentence alone,
  large.
- People are shown with real photographs. An initials disc, an empty ring or a stand-in face is worse than no
  picture, and a wrong face is the worst of the three: find the photo on the institute's or lab's page, or ask.
  Until it is there, the person is name and role as text (`photo=None`), and the report asks for the photo.

## 4. The look

Keep the look of the deck, poster or website the author already likes, and polish inside it. The default below is
the one that won against three restyles (`references/look.md` has sizes and layouts; the `design-system` skill
holds the same tokens across media):

- A dark ground (`141416`), one typeface (Helvetica Neue Light, Medium for emphasis), **one ink** (`F4F4F5`).
  Hierarchy comes from size and weight. No gray text anywhere and nothing under 28 px on the 1920 x 1080 canvas
  (24 px in lists of names): the hall's last row has to read it. A light variant is `FFFFFF` ground, `111111` ink.
- One large picture per slide, full bleed where the picture allows; text in one column of 780 px beside a square
  picture of 956 x 956, or a title over one centered picture.
- A band at the bottom of every slide but the first and the last: the current section, the event with place and
  date, the host's logo, the page as n/N at the far right. Four things with air between them, in 30 px type, under
  a hairline at y = 990. The content keeps clear of it.
- Equal margins (110 px), equal gaps, optically centered blocks, no lone word on a last line (the builder balances
  lines; lists of names are set in lines of equal length).

## 5. Motion and the static twin

A clip earns its place when movement is the argument: a zoom through scales, a divider crossing a picture, points
leaving the input for the embedding, a query and its matches lighting up. `references/motion.md` has recipes,
encoding and the size budget.

- **Nothing waits for a click.** Clips start with the slide and loop, or play once and rest on a last frame worth
  looking at; staged elements fade in by themselves. The speaker should be able to just talk.
- One clip per slide. No sound. No time bar (the builder switches media controls off).
- H.264, yuv420p, even size, CRF 18 to 22, 24 or 30 fps, at least the pixels the slide shows. Keep the animations the
  author already liked and change their labels, not their pictures ("use our previous vid for this").
- **Two files from one builder**: the deck with clips and a static twin for the PDF. They may differ slide by slide,
  because each has different strengths: where the deck zooms, the PDF shows the whole view with zoom-in panels.
- A size limit is met by lightening what nobody looks at (poster frames of clips at `poster_quality=65`), then by
  bitrate, never by pixels; when the deck may be shown from Keynote or the slideshow was not run, keep posters full
  and lower the bitrate first.

## 6. Build

Scripts are in `scripts/`; copy `deck.py`, `starter_deck.py` (as `build_deck.py`) and, while stand-ins are in use,
`placeholders.py` into `build/`, and run the rest from the skill folder. Every Python, Node and shell script answers
`--help`; the AppleScripts print their usage when run without arguments. Python 3.9 or later with python-pptx,
Pillow, lxml, numpy, opencv-python; PyMuPDF for PDFs in the corpus and the LibreOffice preview; PyAV
(`pip install av`) for `fit_clip.py`, `compose_clips.py` and `divider_clip.py`; Node 18 or later with
`puppeteer-core` and a Chrome binary for `record_canvas.js`. Install into a project environment, never the system
Python.

| Script | Does |
|---|---|
| `deck.py` | the builder library: measured and balanced text, titles, pictures, clips with autoplay, fade-ins, band, legend, people, name lists, QR code |
| `starter_deck.py` | a whole deck in the arc of section 1 with stand-ins; builds the deck and, with `--static`, its twin |
| `placeholders.py` | stand-in pictures and clips marked REPLACE, so the starter builds before any material exists |
| `corpus_extract.py` | the author's texts (TeX, PDF, PowerPoint, Keynote, Markdown) into a corpus folder |
| `own_words_deck.py` | is every sentence on the slides, in the clips and in the notes the author's own? |
| `audit_deck.py` | words, titles, gray and small type, italics of key terms, band clearance, overlaps, enlarged pictures, clicks, clips |
| `check_pptx.py` | the file as a package: every picture and clip opens, relationships resolve, size against a limit |
| `preview_slides.py`, `slide_sheet.py` | a picture of every slide without opening PowerPoint; all slides on one sheet |
| `clip_sheet.py` | frames of every clip side by side, with codec, size and duration |
| `make_pdf.py` | the PDF from 3840 px previews under a size limit (JPEG quality 95 down to 72) |
| `fit_clip.py` | a clip at the best quality under a size, in at most five encodes |
| `font_variant.py` | a copy in Arial at 96% for a computer without the deck's typeface |
| `dark_figure.py` | a paper figure recolored for a dark ground (lightness inverted, hue kept, `--chroma 1.35`) |
| `talk_script.py` | the spoken script with running time against `--limit-min` |
| `requests_ledger.py` | the author's instructions out of a session transcript (.jsonl), as a checklist |
| `compose_clips.py` | two clips side by side, locked frame to frame, as one clip (two linked views on one slide) |
| `divider_clip.py` | the divider clip from two aligned renders of one view; the first frame has the divider in the middle |
| `record_canvas.js` | Node: a canvas figure of a served local site, frame by frame on its own timeline, resumable |
| `display_axes.py` | three display directions of an embedding that separate the labeled kinds, with a held-out check against chance |
| `to_keynote.applescript` | macOS: .pptx to .key with notes, looping movies, images and an all-stages PDF for read-back |
| `keynote_try.sh` | macOS: bisect a Keynote import that stalls; never quits a Keynote it did not launch |
| `ppt_pdf.applescript` | macOS: read a deck back in PowerPoint (shapes, movies, effects per slide) and save a PDF |
| `readback_compare.py` | the read-back against the file as built; names a slide whose clip lost its timing |

**Previews are pluggable.** `preview_slides.py --backend quicklook` uses macOS QuickLook (the tested path; its text
is close to PowerPoint's). `--backend libreoffice` converts the deck to PDF with LibreOffice in a private profile
and rasterizes the pages; use it on Linux or Windows, and expect substituted fonts and other line breaks (pass
`--soffice PATH` if `soffice` is not on PATH). `auto`, the default, takes QuickLook where it exists.

```bash
P=python3; S=<skill>/scripts; T=<talk folder>
$P $S/corpus_extract.py $T/build/corpus paper=<paper tex folder> poster=<poster.tex> <folder of earlier talks>
$P $T/build/build_deck.py --root $T && $P $T/build/build_deck.py --root $T --static
$P $S/audit_deck.py $T/<Deck>.pptx $T/build/deck_meta.json
$P $S/audit_deck.py $T/build/<Deck>_static.pptx $T/build/deck_meta_static.json
$P $S/check_pptx.py $T/<Deck>.pptx 50
$P $S/own_words_deck.py $T/<Deck>.pptx --corpus $T/build/corpus --sources $T/build/deck_sources.json --notes $T/build/notes
$P $S/preview_slides.py $T/build/<Deck>_static.pptx $T/build/preview/pdf 3840 && $P $S/make_pdf.py $T/build/preview/pdf $T/<Deck>.pdf 48
$P $S/font_variant.py $T/<Deck>.pptx $T/<Deck>_windows.pptx
$P $S/talk_script.py $T/<Deck>.pptx $T/build/notes $T/TALK_SCRIPT.md --limit-min 8
```

In the builder, layout is in px of the 1920 x 1080 canvas and the content of a slide with a band ends at y = 956.
Give every picture that lies over another on purpose `overlay=True`, and count the words visible in a clip with
`words=`. Slides are numbered by their order in the file, so two slides are swapped by moving their blocks. A build
takes seconds, so rebuild after every change.

Working previews go to `build/preview/deck` and `build/preview/static` at 1600 px, for the slides that changed
(`preview_slides.py DECK OUT 1600 2,5-7`); the 3840 px set in `build/preview/pdf` is only for the PDF. Keep the talk
folder's top level for what is delivered. Set `PYTHONNOUSERSITE=1` with `export`, not inside a variable that holds
the interpreter (zsh does not split it).

## 7. Check before anything is sent

The author's patience ends at the first slip they find themselves ("no mistakes allowed anymore"). In this order
(`references/check.md`):

1. Build both files. Read the builder's warnings.
2. `audit_deck.py` on both, `check_pptx.py`, `own_words_deck.py`: zero problems, or each one named in the report with
   the author's own words that cause it.
3. **Look at every slide you changed**, rendered at 1600 px (`preview_slides.py`), and at the whole deck on one sheet.
   An audit cannot see that a zoom-in hides its source, that a legend is missing, or that a picture makes no point.
4. `clip_sheet.py`: read the frames of every new or changed clip.
5. Trace the ledger: every instruction is ticked against a slide you looked at, or listed as not done.
6. Check the facts (`references/check.md` section 6): every number against `SOURCES.md` and its record, with one
   rounding everywhere; every visual claim of agreement against a shuffled baseline; every "1 in N drawn" label on
   the frame where it stands; every "only", "all" or "alone" about data for its stage (pretrained on is not
   evaluated on); outside facts opened, outside pictures licensed. Scan the QR code's address as a stranger would:
   it must open without a login.
7. Never build while a clip is still encoding, never overwrite a file the author has open (give each delivery
   round's files a name they do not have open; a `~$Name.pptx` lock file means it is open), and never open a
   half-built deck in PowerPoint or Keynote on their machine.

When there is time, and only then, let independent readers attack the rendered slides, each with one lens (design,
science against the paper, story and timing for this audience, text). **Every brief asks for the author's sentence,
never new wording, and states corrections in positive form**: reviewer-reworded lines went onto the slides in the
original project and caused the rebuild the author demanded. Once the look and order are approved, readers report
defects only. They report; one writer changes the deck, and keeps the author's line where a reader disagrees with
it. Cap heavy work at two encodes or recordings at once on a laptop, even when the author asks for a fleet
(`references/process.md` section 5). The `adversarial-audit` skill has the general reader brief.

Converting to Keynote by script, and what to do when Keynote stalls, is in `references/traps.md`: never force-quit
Keynote while the author's decks may be open.

## 8. Deliver and iterate

Deliver the deck, its Arial copy, the PDF, `TALK_SCRIPT.md` and `SOURCES.md` (where every number comes from). The
author asked for fonts inside the .pptx; python-pptx cannot embed them, so the report says which fonts are embedded
(`check_pptx.py` prints it) and the Arial copy is the fallback (`references/check.md` section 7). On a
round of notes, send what they asked for (usually the PDF) and rebuild the others so that all files stay in step.
Report in this shape, short enough to read on a phone:

- what is delivered, with paths and sizes, and each format asked for and not delivered (a .key that could not be
  made says so); what was checked and what was not (say plainly if the slideshow itself was never run in the
  presenting program, and which preview backend drew the slides);
- what changed, one line per slide, in the author's terms;
- what to check: every reading you had to guess ("I read X as Y"), names, dates, numbers you could not verify;
- what is not done, and why.

No praise of the deck, no list of everything that is fine. Then the notes come. The loop that works
(`references/process.md`):

- **Ledger first.** Append every note to `REQUESTS.md` in the author's words before touching anything. A later note
  overrides an earlier one; a specific note overrides a general rule; a note on one file (PDF or deck) may apply to
  the other, so ask yourself, not them.
- A correction reaches everywhere the thing appears. The event's name stands on the title slide, in the band, in
  the notes, in the script and in the names of the files: change all of them and say that the files have new names.
- Apply all of them, rebuild, audit, look, resend. Minutes, not hours. Polish what they have; do not rebuild.
  "Bring back" or "the old one" means restore that version from disk; do not approximate it. Keep every delivered
  version in `deliveries/vN/` (deck, PDF, builder copy, slide sheet): the author may pick slides across versions.
- **Under a deadline**: hand over what builds now, then iterate. Send status lines of one sentence about once a
  minute ("you going?" came after four silent minutes). Do not start helpers or long renders the author did not
  ask for, and do not explain.
- If a session was cleared or stalled, recover the notes from its transcript (`requests_ledger.py`) and the work
  from the talk folder before doing anything new.

## 9. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| text written for the author | "you are only allowed to use text that I have used" | the author's sentences, cut; a script that checks it |
| a new look, a new typeface | "what you did before was better, bring that back" | the first look, polished |
| claim cards, boxes with arrows, three columns with bold headers, pill labels, a code card | "AI slides", "AI aesthetics patterns" | one sentence and one picture |
| small gray captions and footers | "no grey small text" | one ink, 28 px and more |
| 40 words on a slide | "what don't you understand from max 30 words" | 25 words, counted by script |
| the problem as a technical step | "it's not any of the problem and just such a reduction" | the stake as the paper's introduction frames it |
| a question and its answer on one slide | "AI slop" | the question; the answer is spoken |
| formulas on the idea slide for an outside audience | "drop the formulas" | the picture; math in backup (in-field: the paper's own definitions) |
| paper figures on white plates | "do not bring white background figs" | the same figures recolored |
| redrawn charts and diagrams | "really low quality figures" | the paper's and the website's own |
| a remade architecture animation | "use our previous vid for this" | the animation the author already liked |
| a crowded five-tab footer | "distraction" | four items with air |
| initials discs, empty rings | "put the photo I gave you" | real portraits |
| colors without a key | "if you use a color explain what it is" | a legend on every such slide |
| a similarity map alone | "show 2 different FOVs so that they know this captures similarity" | whole view plus zoom-ins of matches |
| a cloud of dots | "what's the point of what you're showing" | different objects marked in one space |
| filled translucent shapes | "ugly", "only mask boundaries, thin white" | outlines |
| insets over neighbors | "things don't go over each other, this is QC" | an overlap check and a look |
| "top three" | "don't call top 3, rather top one" | "first", with the number |
| blurry or pixelated stills | "the quality of images" | two pixels per slide pixel |
| a 137 MB file | "this is too big, make it smaller with no loss" | lighter posters, fitted clips, same pixels |
| a helper fleet under deadline | declined | hand over, then iterate |
| reviewer-reworded titles and lines | "change the AI slop harshly" | the author's sentences; readers quote the corpus |
| a correction phrased as a negative | rejected | the positive form, with its data stage named |
| six helpers beside heavy renders on one laptop | "it was not moving" | at most two encodes at once; cheaper fixes |
| a projection on an input nobody could open | "drop this number ... if you don't have any idea" | opened facts only |

## Reference files

- `references/audience.md`: the audience switch, what changes in-field and what stays, with its evidence.
- `references/story.md`: the arc slide by slide, titles, claims, timing, the outline table.
- `references/words.md`: the own-words procedure, cutting, dictated lines, terms, names, notes.
- `references/pictures.md`: each picture pattern, legends and scales, resolution, reuse of figures, people.
- `references/look.md`: sizes, layouts, the band, spacing, what reads as machine-made.
- `references/motion.md`: clip recipes, encoding, recording website figures, the twin, the size budget.
- `references/check.md`: the full check, what to look for on a rendered slide, independent readers, the report.
- `references/process.md`: the ledger, the note loop, deadlines, recovering a session.
- `references/traps.md`: PowerPoint, Keynote, QuickLook, LibreOffice, encoding and shell traps met on the way.
