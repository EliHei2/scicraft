# Deck gate

For a slide deck and its PDF twin before they are sent or uploaded. The full builder, audits and the deck-specific
rules are in `talk-slides`, whose own check section is the detailed form of this one. Without that skill, this list
still catches what the author caught.

## Scripted

- **Words**: at most 25 words on a slide and at most 10 per sentence, counted by script, names of people and data
  labels excepted (the author's limit after "what don't you understand from max 30 words").
- **No gray text and nothing under 28 px** on a 1920 x 1080 canvas (24 px in lists of names).
- **Nothing lies over anything else** unless on purpose: pairwise box overlap of pictures, text and the footer band
  ("make sure things don't go over each other, this is QC").
- **No picture shown larger than its pixels**; for the PDF, two pixels per slide pixel.
- **Clips decode** to the last frame, are H.264 yuv420p with an even size, autoplay, no click builds, no media
  controls. Never build while a clip is still encoding: a deck built during an encode embedded a broken clip.
- **The package opens**: every relationship target exists, every picture opens, the size is under the cap (50 MB
  for the deck upload in the source talk; 137 MB was "too big").
- **Dashes, double spaces, repeated words, mixed spelling** by script.

## With eyes

Render every changed slide at 1600 px and the whole deck on one sheet; read the frames of every new clip. For each
slide: does the picture show the title's point to a stranger; is every color keyed; does anything collide; is the
slide balanced; is anything soft; is a stand-in or an old label left over. Check the static twin and the deck
separately: they differ.

## Facts

Every number on a slide against the sources sheet and its record; names and affiliations against institute pages;
the event's name, place and date against the organizers' page; the QR code decoded and opened in a private window.

## Say what was not checked

The slideshow itself (clips starting, fades running) is proven only by playing it, which puts the file on the
author's screen; ask first, or say it was not run. The hall computer's fonts and codecs are covered only by an
Arial copy and H.264.
