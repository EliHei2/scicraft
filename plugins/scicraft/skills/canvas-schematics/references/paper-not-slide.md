# Paper figure, not slide

The first schematic attempts in the source work were "slide-deck infographics (big titles, grey
subtitles, rounded cards with shadows, pill chips, numbered circle badges, loose proportions)". A
paper figure sits next to dense data figures at 5 to 7 pt and must look like it belongs there.

## Three ways to fail

| Name | What it looks like | Cure |
|---|---|---|
| the SLIDE | drop-shadowed rounded cards, pill tags, fat gradient arrows, a big title over a gray filler subtitle, keynote-sized fonts, rainbow palette, a square canvas where the reference was landscape | make the library unable to draw chrome; flat frames; three tiers; the reference's aspect ratio |
| the CLINICAL BLOB | identical cold circles for every cell, flat saturated fills, everything one size, mechanically gridded; technically flat and still lifeless (this is what got called "ugly") | cells with character from `LIB.cellShape`, warm pastels with a white halo, natural scatter, sizes and seeds varied |
| the CRAMPED CIRCUIT | too many boxes jammed together, arrows through labels, text touching borders, inconsistent arrowheads, a tiny illegible matrix ("goes over each other") | delete and align: fewer elements, a grid, whitespace budgeted before content |

The target threads all three: flat, warm where it shows living things, and with air.

## The anti-slide list

Delete on sight. `scripts/lint_regions.py` catches the ones a script can see.

- drop shadows (`shadowBlur`, `shadowColor`), glows, 3-D extrusion, bevels
- gradients of any kind; the only exception is `LIB.densityGlow` for a density blob
- pill or chip tags, rounded cards used as containers for text
- a second title size, a big figure title, full-width banners
- gray subtitles used as filler under a title
- sentence titles, titles with periods, titles over four words
- arrow narration (a sentence along an arrow), paragraph glosses, a caption block inside the image
- numbered discs in place of panel letters
- a filled "algorithm box" placed to fill empty space (the legacy templates prescribed it; it is banned)
- panel background boxes and hairline dividers between panels
- rainbow or more than two saturated accents in one figure
- monospace except for literal code tokens
- the method's name on a concept figure

## What stays

- **Panel letters**: bold lowercase, no period, top left, on the same baseline as a left-aligned title.
  Letter and title are drawn by `main.js`.
- **Small step badges** (`LIB.badge`) used sparingly inside a pipeline. They were banned once, then
  allowed, and both reference renders used them; the latest reading allows them.
- **No gray text.** A secondary gloss is a lighter weight in `PAL.ink`. Every primary label is near-black
  (`PAL.ink`). Category labels may take their category's color.
- **One boxed core equation** at most, plus on-object symbols, and numbers only where they are
  demonstrated (see `references/real-data.md`).
- **Legends**: small, flat, frameless, at L3. Label on the object when there is room.
- **Every symbol on the canvas is defined**, in the legend or on the object, and a symbol the text
  does not need is deleted. No illustrative numbers: a value appears only when it comes from the data.
  In about ten rounds on one method figure the author cut an undefined Greek symbol ("drop gammas,
  it's vague"), a toy tile count and a made-up window width, and kept a legend that defined each
  remaining symbol (the latent, the encoder, EMA, `sg`).

## The declutter standard

| Element | Rule |
|---|---|
| panel title | a bare symbol, or a noun phrase of at most four words, no period |
| axis or ramp gloss | a symbol plus a cue of at most three words |
| labels inside the image | about three words each |
| flow | one dominant direction (left to right or bottom to top); side notes attach with thin leaders |
| color | at most two dominant accents plus grays; ordinal values on a single-hue lightness ramp; categories in distinct hues; emphasis by weight and order, never by a louder hue |
| line style | the second channel: solid observed, dashed predicted or copied, dash-dot extrapolated; at most three edge relations |
| depth | an offset faded copy (`LIB.tensor`), never a blur |
| whitespace | budget it first; more than 40 to 45 % white in a concept figure |
| scope | two to four clean panels; a figure trying to be two figures is split |

**Architecture overviews are the exception on density**: the author asked for "more meat" there:
fill the canvas, keep about two accents, neutral data points, and make the core mechanism the
centerpiece. Block diagrams that need detail use three zoom levels (full model, one expanded block,
sublayer insets) instead of crowding one level.

## Taste words and what they mean

| The author says | It means |
|---|---|
| "nicer", "cleaner", "sexier" | simpler and bolder inside the current look; never add encodings |
| "looks like a slide", "AI aesthetics" | something on the anti-slide list is present |
| "ugly" (of cells) | the clinical blob |
| "goes over each other" | the cramped circuit; run `render.js --check` and look |
| "not obvious" | the mechanism is suggested; draw the operation with its operands |
| shape words ("irregular", "muted", "browner") | a judgment of the look; show two rendered options side by side, a description cannot be judged |
