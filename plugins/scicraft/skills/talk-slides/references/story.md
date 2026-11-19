# The story

A talk for people outside the field succeeds when a listener can tell a colleague afterwards what the work is, why
it matters to them, and one thing they saw. Everything here serves that.

## Contents
1. The outline table (do this first)
2. The arc, slide by slide
3. Titles
4. Claims
5. Translating for the room
6. Order and transitions
7. Timing
8. The ending and the backup

## 1. The outline table

Before any slide exists, give the author this table and let them move rows. It is the cheapest place to be wrong.

| # | Role | Title (their sentence, at most 10 words) | Source of the sentence | The one picture | Seconds |
|---|---|---|---|---|---|
| 1 | title | ... | poster, title | slow loop of the showcase data | 10 |
| 2 | the stake | ... | paper, introduction | the whole sample with its size | 40 |

Fill the title column from their texts only (see `words.md`). If no sentence of theirs makes the point of a slide,
the slide's point is probably yours and not theirs: drop the slide or ask them for the sentence.

## 2. The arc, slide by slide

**Title.** The name of the work, then what it lets people do, in the title of the paper or poster. Speaker, group,
event. A slow loop of the real data behind it does more than any tagline. A speaker who has moved gets a star and
"currently at ..." in the byline.

**The stake.** What is measured, how much of it there now is, and why hand analysis no longer keeps up. Use the
paper's introduction and the poster's abstract: they already hold the author's framing. Show the real data whole,
with its size. Do not open on the method and do not shrink the problem to a preparatory step.

**The question.** The single question the work answers, as the paper asks it. One line. The picture lets the
audience feel the question (a zoom through the scales the question is about).

**The idea.** One sentence the audience could repeat, in which the work's own term appears for the first time. From
here on that term is always in italic, so it becomes a thing with a name.

**How it works.** One picture: the paper's architecture figure or the animation that already exists. The audience
needs to believe there is a mechanism, not to follow it. Add the scale of what it was trained on, as numbers in the
order of the argument, and one phrase that says why that amount matters.

**Results.** Three or four slides, each one claim. Order them from what the audience can verify with their own
eyes (the expert's annotation beside the method's output), through what the method lets them do (ask for a
structure, see the matches), to breadth (other samples, other tissues), and last the comparison with other methods
as one number. A result is ready for a slide when its title is true without a footnote.

**What comes next.** Concrete assets: the data that exist and are not used yet, shown as thumbnails; the people who
generated them, with photographs; what the host institution would gain. If a number is the group's own and not yet
part of the published work, mark it (an asterisk and one small line naming the source).

**Acknowledgements.** See section 8.

## 3. Titles

The title is the slide's point as one full sentence, fact or question of at most ten words, taken from the author's
texts. Read only the titles in order: they must tell the talk.

| Weak | Why | Strong (if it is in their texts) |
|---|---|---|
| Results | names a section, makes no point | "Our model has the lowest mean rank on all [N] tasks." |
| Masked tabular pretraining | a term | "Pretraining on public tables transfers to unseen schemas." |
| Our approach outperforms prior methods across tasks | yours, vague | the one number, in their words |
| What is the unit? + "There is no unit." | two versions of one thought | the question alone |

A title may be a noun phrase only when the author asks for it by name ("Acknowledgements", a goal line such as
"Goal: from ... to ..."); mark it `free=True` in the builder so the audit knows it is deliberate.

## 4. Claims

- State the strongest claim the records support and the author will defend in questions, and state it once. Where
  the method is first, say "first" with the number; "among the top three" undersells and invites the question why.
- Move what is weak, mixed or needs caveats to backup, with its number and stated honestly, unless someone asked
  for exactly that on a main slide. It leaves the main slides; it never leaves the record. Never write a claim the records do not support, and never "first at everything" when it is second
  somewhere.
- A title that claims a visible match ("the field follows the annotation") must be measured or made neutral. A
  drawing of a mechanism is checked against the paper's own statement of it.
- Estimates the author cannot defend (world totals, projections) go out. An estimate they do stand behind is shown
  as theirs ("We estimate ...").
- If examples were chosen by eye, the notes say so; if by score, the notes say which score.
- **A claim of visible agreement gets a number and a null.** Compute the agreement (the share of a point's
  neighbors that share its label, the share of adjacent regions that share a class) and the same share after
  shuffling the labels. The title claims a match only if the margin is clear; both numbers go in the notes and in
  `SOURCES.md`. In the original project a margin that was small next to chance turned a title neutral; a clear
  one kept it.
- **A new analysis made for the talk is flagged as unreviewed** in the report, with the offer to drop it. One such
  slide held an "in every case" claim that the final proofread found false for several cases; the author cut the
  slide.
- **Outside facts are opened, not remembered.** Only facts whose primary page was opened go on a slide; snippets
  and memory are marked as such in `SOURCES.md` (`check.md` section 6).
- Keep `SOURCES.md`: one line per number, with the file or sentence it comes from. Check each against the record
  before delivery; a wrong number found by the audience ends the talk.

## 5. Translating for the room

This section is the outside-field setting. For a talk inside the field, `audience.md` says which of these rules
change.

- Name things as the audience names them: a blood vessel, a lymphoid aggregate, the tumor-stroma interface, not
  cluster 7. If a structure has no name they know, pick another example.
- Show the raw measurement before the model's view of it, and the expert's view beside the model's.
- Every new term costs attention. Introduce the work's one term; avoid the field's acronyms or say them once.
- No formulas, no loss functions, no layer counts on the main slides. They can be in the notes ("if asked") and in
  backup. If the author asks for "a technical touch", it is the paper's own figure.
- Say what was held out or public, in positive form and with its data stage named ("pretrained on [data]"),
  never as a negative about what was not used.
- Do not explain what the room knows better than the speaker (their own biology or clinic).

## 6. Order and transitions

For every neighboring pair of slides, write down the question the first leaves in the listener's head. The second
must answer that question. Typical repairs:

- the need comes before the named idea (first "the unit should be chosen when you ask", then "so we start from the
  finest measurement");
- the thing the audience can verify comes before the thing they must take on trust;
- the widest view comes before its zoom-ins.

A section label in the band (Motivation, Idea, Method, Results, Future) tells the room where they are without a
separate agenda slide. Do not spend a slide on an outline in a short talk.

## 7. Timing

- A calm pace for a mixed audience is about 140 words a minute. Notes start with `[40 s]`; `talk_script.py` sums
  them against the slot and counts the spoken words.
- Leave a tenth of the slot unused. Conference chairs cut speakers off.
- A slide that needs more than 50 seconds has two points: split it or cut one.
- Clips set the rhythm: a clip that plays once should finish within the time its slide is spoken.
- Check the rate per slide, not only in total: a calm total hid one slide at about 190 words a minute (95 words in
  30 s). `talk_script.py` prints each slide's rate and lists those above 140.
- **A decision about cuts comes as one decision**, not options: the slides kept, with seconds per slide and a running
  sum, the slack before the target and before the hard cut, and the order in which to cut further if the speaker
  runs long. Whoever selects (you or a helper) edits no file while deciding.

## 8. The ending and the backup

The last slide stays up during the questions, so it works as a poster: the people, the announcement, where to find
the work.

- Title it "Acknowledgements" (or the author's word). No "Thanks!" in huge type, no "Questions?".
- People with faces and one line each: supervisors, those who built infrastructure, co-authors with their current
  affiliations. Roles exactly as the author gives them. Then both labs as lists of names in lines of equal length,
  with the names the author wants in bold.
- Compute and infrastructure are thanked with a number the records give ("about N GPU hours", with N from the compute records).
- The announcement: what is released and when, in the author's line, and a QR code that leads to a page which opens
  for a stranger. Scan it before delivery.
- Only the logos the author asks for (often just the host's).
- No band on this slide and none on the title.

Backup slides answer the questions the talk invites: the full table, the ablations, the alternatives tried, the
training objective with its formula, the corpus by tissue. Each has a sentence title like the others. Take them
from the paper, the poster and the website; do not design new figures for backup.
