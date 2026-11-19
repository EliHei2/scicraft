# The look

Find the deck, poster or website the author already likes and keep its look. In the original project a dark deck
with full-bleed tissue clips was the first thing built; three later looks (the author's own white slide template, a
restyle in another typeface, a "cleaner" redesign) all lost against it. "Make it cleaner" and "more minimal" ask
for less inside the same look.

## Contents
1. The default theme
2. Sizes
3. Layouts
4. The band
5. Spacing
6. Emphasis
7. What reads as machine-made
8. A light deck

## 1. The default theme

| | |
|---|---|
| Canvas | 1920 x 1080 px (16:9); all layout in these px |
| Ground | `141416` |
| Ink | `F4F4F5`, the only text color |
| Hairlines | `34343B` |
| Typeface | Helvetica Neue: Light for text, Medium for titles and emphasis; nothing else |
| Margins | 110 px left and right; titles start at y = 58; content ends at y = 956 when there is a band |
| Slide change | a plain fade |

`Deck(...)` takes `ground`, `ink`, `rule`, `family`. On a machine without Helvetica Neue the library falls back to
Arial or DejaVu Sans for measuring; `font_variant.py` makes the copy for a hall computer.

## 2. Sizes

Nothing is smaller than 28 px (24 px in lists of names). This is the size a back row reads; it also forces brevity.

| Element | Size | Weight |
|---|---|---|
| Name of the work on the title slide | 150 | Medium |
| Title (the point) | 54 to 58 | Medium |
| Line under the title | 40 | Light |
| Body sentence | 44 to 48 | Light |
| A big number / its unit | 56 to 96 / 32 to 40 | Light |
| Labels of pictures, legend | 28 to 32 | Light |
| Names under portraits / lists of names | 26 to 28 / 24 | Medium for the name |
| Band | 30 | Medium for section and page |

## 3. Layouts

Three layouts carry a whole deck. Using few layouts is what makes it look designed.

**Column and square.** Text in a column 780 px wide at the left margin, vertically centered between the top and the
band; a square picture or clip 956 x 956 flush to the top right corner (x = 964, y = 0). For the stake and the
question. The legend sits under the text in two columns.

**Title and one picture.** The title at the top left over the full width, optionally one line under it, then one
picture as large as fits between y = title + 24 and 956, centered (`s.pic_in`). For the idea, how it works, and
most results.

**Title and a grid.** Panels of equal size in a row or grid with equal gaps, labels above, a name below each
column. For "three samples" and "selection and matches". Compute panel size from the space; never eyeball it, and
never let the sum of panels exceed the width (that is how panels came to overlap).

**Statement.** For a point that has no honest picture: the sentence alone, 84 px, with at most one line under it,
centered between the top and the band (`s.statement`). A slide with a title at the top and two thirds of empty
ground under it looks unfinished; either the picture fills that space or the sentence takes the middle. Use it
once or twice in a talk.

The title slide is a full-bleed slow loop with text at the left; the ending is described in `story.md`.

## 4. The band

On every slide except the first and the last. It tells the room where the talk is and carries the host's mark.

- Four things with air between them: the current section (left, Medium), the event with place and date (center),
  the host's logo, the page as n/N at the far right (N is the last slide of the talk; backup slides show their
  number alone).
- Under a hairline at y = 990, type of 30 px, in the ink. No color fill, no row of all section tabs (five tabs
  were "crowded" and "a distraction"), and not so small that it disappears.
- Content stays 34 px clear of it. The audit checks pictures and clips.
- The event's name is the organizers' own; ask for the date rather than writing a month alone if the day is known.

## 5. Spacing

- Equal margins, equal gaps between like things, one baseline for labels in a row.
- A block is centered in the space it has; do not leave a third of the slide empty under a picture that could be
  larger, and do not pack to the edge either. The author's words: "don't pack things or go asymmetric or weird".
- No lone word on a last line. `Deck.para` balances lines by measured width; `Slide.names` sets a list of names in
  lines of equal length. Check both renderings (the Arial copy can shift a break).
- Text over a picture always sits on a plate in the ground color (`s.plate_label`).
- Look at the whole deck on one sheet (`slide_sheet.py`): slides of the same kind should look the same.

## 6. Emphasis

- Weight (Medium) on a key phrase inside the author's sentence, as on a poster. Size for hierarchy.
- Italic only for the work's own term.
- No accent color for text. Color belongs to the data.
- No underline, no all-capitals, no boxes around text.

## 7. What reads as machine-made

Each of these was removed at the author's request. Do not build them:

| Pattern | Use instead |
|---|---|
| a card with a rounded border and a short claim in it | the sentence, plain, large |
| three columns, each with a bold header and two lines | one sentence and one picture; or three slides |
| boxes joined by arrows to explain a method | the paper's figure |
| a numbered list with large numerals | nothing; the talk's order is the list |
| a punchline in the accent color under the content | the title already says it |
| pill-shaped labels on pictures | plain labels on ground-colored plates |
| a code card on a talk for non-programmers | the planned interface in backup, if at all |
| a small provenance caption under each picture | the speaker says it; the notes hold it |
| initials in a disc for a missing photo | the photo |
| a footer with all section tabs | the current section only |
| statistic tiles in a row | numbers in the order of the argument, on one line |
| a decorative gradient or icon | the data |
| a picture on a white plate in a dark deck | the picture recolored |

## 8. A light deck

If the author's house style is a white ground, set `ground='FFFFFF', ink='111111', rule='D0D0D5'` and keep every
other rule. The audit's "gray text" check compares against the ink of the theme, so it works on both grounds.
Pictures of fluorescence or tissue on black then need a deliberate frame; clips are whitened to pure white
(a clip encoded on "white" often decodes as 253 and shows as a box against the slide).
