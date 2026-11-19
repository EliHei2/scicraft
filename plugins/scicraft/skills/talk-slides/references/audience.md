# The audience switch

Every rule in this skill was tested on talks for people outside the speaker's field: clinicians, an institute
day, leadership. Many talks in a machine-learning group are given inside the field: a reading group, a lab
meeting, a conference oral, a job talk. Set the switch once, in the outline, and write it at the top of the
request ledger.

## Contents
1. What stays the same
2. What changes
3. Choosing the setting
4. Evidence

## 1. What stays the same

The look, the type, the palette, the pictures, the clips and the own-words rule do not change with the room. In the
original work the same figures and animations served a biology day and an ML venue; "the audience changes the
order, the formulas and the amount of explanation, not the look". So in both settings:

- one point per slide, a title that is one sentence of at most 10 words;
- every sentence is the author's own (`words.md`);
- one ink, nothing under 28 px, a legend for every color, no machine-made patterns (`look.md`);
- every number has a line in `SOURCES.md`, and the strongest claim the records support is stated once.

## 2. What changes

| Rule | outside-field (tested) | in-field (Suggested, not yet tested in real work, except where marked) |
|---|---|---|
| Formulas | none on the main slides; math waits in backup | the paper's own definitions and its labeled loss may stand on a main slide, typeset as in the paper (rendered from the paper's TeX as a picture). The author asked for exactly this once, on a slide away from the mechanism animation (evidence below) |
| How it works | the paper's figure or the website's animation, no math | the paper's architecture figure (flat blocks, same semantics as the paper), then the objective |
| Results | the comparison as one number in the line under the title | the paper's rank heat map or results table, with the one number in the line under the title (the author's ML figures were rank heat maps; evidence below) |
| Stake | what is measured and why it matters to the room | the open problem as the field states it and the gap in prior work, from the paper's introduction |
| Terms | the work's one term, field acronyms avoided | the field's standard acronyms as the paper uses them; still one name per thing |
| Backup | the table, the ablation, the math | ablations, seeds and variance, compute, hyperparameters, failure cases: the questions an expert asks |
| Word limit | at most 25 words per slide and 10 per sentence, counted by script | the same counts for prose. A formula or a results table placed as a picture is not counted as words, because it is read as a picture; its labels still follow the 28 px floor |
| Slides per minute | about N + 2 slides for N minutes | the same, unless the slot is a long seminar: then about one slide a minute (Suggested) |

Rendering a formula for a dark deck (the procedure used for the paper's labeled loss):

1. A `\documentclass[border=3pt,varwidth=40cm]{standalone}` file with the paper's own macros.
2. Set the ink to the deck's ink with `\color`.
3. Compile to PDF and rasterize on a transparent ground at twice the slide size.
4. Crop to the inked extent, and check that the braces and labels of an `\underbrace` are even.
5. Place it with `s.pic_in`, so the audit counts it as a picture.

Nothing in the scripts changes: `Deck(max_words=..., max_title_words=..., max_line_words=...)` keeps its defaults,
and formulas placed with `s.pic_in` are pictures, so `audit_deck.py` does not count them.

**A lecture deck for a method's math** (a reading group, a lab meeting; Suggested, not yet tested in real work as a
shipped template): one definition per slide, the formula typeset exactly as in the methods note, a small worked
example under it, and the symbols explained in words beside it. Build it from the methods note's own TeX, so the
slides and the note cannot drift, and print no results on it. The source work kept such a deck for the definitions
of a metric suite.

## 3. Choosing the setting

- Ask who sits in the room when collecting the occasion (SKILL.md section 0). A mixed room is outside-field.
- A job talk or a departmental seminar is in-field for its first half and outside-field for its framing: write the
  stake for the outsider, then switch.
- When unsure, build outside-field. It was the tested setting, and an expert follows it; the reverse fails.
- For an outside-field talk, reviewers taken from the room catch what the room will not follow (`check.md`
  section 8).

## 4. Evidence

- On the biology talks the author said "In slide 5 drop the formulas" and showed the architecture as the
  website animation, without math.
- On the same talk the author asked for "some math elsewhere (the paper's definitions and the labeled loss, typeset with
  LaTeX)", kept off the mechanism animation.
- For an ML venue the poster kept the paper's math properly typeset (definitions, a boxed equation, the labeled
  loss), architecture was drawn as flat block diagrams, and benchmark results were rank heat maps.
- Everything else in the in-field column is a gap filled so that a user is not stopped, and is marked as such.
