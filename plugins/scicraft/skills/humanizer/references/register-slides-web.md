# Slides, project pages, posters and captions

Display copy is read in seconds, so every tell costs more there than in a paper. This module adds what the
general catalog and the technical register do not cover. Building the deck or the page itself belongs to
`talk-slides`, `poster` and `paper-website`; this file covers only the words.

## The first rule of display copy: remove, do not write

When the copy appears under the author's name, it uses only sentences the author wrote, shortened only by
cutting. Do not paraphrase, merge two sentences, add a connective or reorder a dictated line. A humanizer pass
on display copy therefore deletes words and never adds its own; the sibling `author-voice` skill ships `own_words.py`, which checks
each line against the author's texts. Text composed for an author reads as machine-made to them however well it
is edited.

After cutting a sentence out of its paragraph, strip the connectives left hanging: "Finally", "Thus", "Yet",
"therefore", "such fields", "this".

## Separators and chains

- **No symbol between phrases.** Middle dots, bullets inside a line, pipes, slashes and multiplication signs
  that chain phrases read as generated at a glance. Use a comma or a sentence.
- Rejected on a project page:
  <!-- voice-lint: off -->
  "self-supervised learning × tabular data × clinical prediction" (as a tagline), and
  "foundation model · one embedding per row · ranked first of [N] methods" (as a subtitle).
  <!-- voice-lint: on -->
  Both were removed entirely, and the build now fails if a separator comes back.
- Guard it in the build. The page checker that held up uses two patterns: `/·|•/` and `/ \| /`. A deck audit
  counts dashes and middle dots in every text box.

## Taglines, tiles and repeats

- **No tagline over the title and no result claim at the top of the page.** The name stands alone; the first
  statement under it says what the work lets people do.
- **No row of stat tiles, claim cards or three columns with bold headers.** One number, with what it counts and
  its unit, in a sentence.
- **Never the same statement twice** on one page or slide: a heading that repeats its first line (upstream
  pattern 24) and a caption that repeats the title are the common forms.
- **No filler or provenance captions** ("Figure generated from our pipeline", "Source: internal analysis").

## Evaluative words

`best`, `leads`, `wins`, `beats`, `strongest` and `dominates` become the measured relation: "ranks first",
"is rated above X", "ranks first on 9 of 12 tasks". The relation must be the one the records show; the rewrite
changes the wording and never the rank, the comparator or the number. `first` is kept when the method is first
(a deck that said "top three" for a method ranked first was corrected to "first"). Contest words (`winner`,
`runner-up`) do not describe a comparison of two methods.

## Labels and numbers

- **A label says what the number counts, with its unit beside it**: "48 of 50 seeds", "12 of 15 datasets",
  "3.2 GB". Bind number and unit so a line break cannot split them (`45&nbsp;ms` in HTML, `45~ms` in TeX).
- **One statistics language: the paper's.** A page or a slide never swaps in a friendlier statistic than the paper
  reports (`stats-reporting` holds the rules).
- **One name per thing.** Working names of internal variants stay off every public surface, and a renamed variant
  is renamed everywhere, data keys a reader can see included.

## Captions

Write captions in full sentences. A caption written as fragments ("Open circles: no change. Band: spread
across seeds.") was rejected as machine-made; the fix was "Open circles mark runs with no change. The band
shows the spread across five seeds." Name every encoding the figure uses: each color, each dashed line, each
marker. A caption that left a dashed line unexplained was a proofreading defect. Caption structure for papers is
in `figure-development` and `paper-writing`.

## On slides

The deck rules that touch wording are in `talk-slides`: the title is the point as one sentence of at most 10
words, at most 25 words on a slide, every sentence at most 10 words, and a question and its answer never stand
on the same slide. Run this module on the speaker notes and on any line the author dictated only to fix typos;
a dictated line is otherwise kept as given.
