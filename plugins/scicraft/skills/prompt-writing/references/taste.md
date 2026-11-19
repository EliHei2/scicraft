# Briefing for taste

A receiver fills every choice the brief leaves open with its own defaults. For figures, decks, reports and prose
those defaults are what the author called "slidy", "AI slop", "weird" and "overwhelming". The fix is to close the
choices in the brief, with numbers, an exemplar and a list of what must not appear.

## Constraints, not adjectives

From the author's teaching: "Taste is constraints, not adjectives. Exact mm, hex, three type tiers; 'make it
cleaner' becomes a diff, not a re-guess."

| Adjective in a draft brief | Constraint that replaces it |
|---|---|
| clean figure | width 180 mm; three type tiers (7, 6, 5 pt); spines `#111111` at 0.9 lw; no gridlines; legend outside right |
| concise report | three-sentence summary, then counts, then top five; under 300 words; no glossary box |
| minimal docs | each notebook at most 15 code cells of at most 10 lines; under 2 MB with outputs; one question per page |
| human reply | each comment at most 5,000 characters; no colons, semicolons or dashes inside our sentences; quotes matched verbatim against the source |
| cleaner | remove: the subtitle, the second legend, the box around panel c (a list, not a restyle) |

The numbers in the table are examples taken from real briefs. A brief for another project uses that project's
numbers, from its style module or the author's notes.

## Point to the exemplar and require a match

- **Open the example before producing the deliverable.** An agent read "source data" by the category name and
  built and uploaded 73 per-panel files (coordinates, outlines, transcripts). The colleague's example held 5
  short reference tables, and 5 to 15 were wanted. The correction was the harshest of that session. The brief
  rule: list the example files with their row counts and column headers, write one line on what kind of thing
  each is, set a target count from them, and stage uploads through an explicit whitelist.
- **Give a reference to reproduce first.** Given a reference figure, reproduce it (aspect ratio within about 2%,
  the same arrangement and idioms) and polish second. Deviate only where asked.
- **Name the previous version the author liked** and say it is the base. "The previous one was so good, you killed
  it?" followed a redo that dropped an accepted element.

## One style lever

When several agents build parts of one artifact, each one sees only its tile. In the author's words, they "will
not catch 'the whole thing reads like a slide'". Two rules follow:

- **All style goes through one shared library**: palette, fonts and helpers. Agents may not hard-code a hex value or
  a font. "If it can't be slidy, the agents can't be slidy."
- **The lead owns the whole-artifact check**: render the assembled piece and look at it. Ask whether it reads as a
  slide, a dashboard or a template, and whether one part dominates.

## Size the deliverable to the question

- A first rebuttal document ran to 21 pages, 45 Q&A entries and a rhetorical "argument" box with three green
  questions. The author said "I told you to be minimalistic", and it was remade at 9 pages. Give the receiver a
  budget in pages, words or items.
- A report with a glossary or limits box at the top was "unnecessary and total AI slop"; the author's rule is
  "LESS IS MORE". Shareable reports open with a three-sentence summary.
- Bold for long text and oversized type were rejected ("why bold font and so big for such a long text"). Bold
  marks the one phrase that must not be missed.
- Unrequested extras are faults. List the deliverables at the top of the brief and say that an extra is offered in
  one line and never built.

## Words and forms that must never appear

Give the receiver the list for this deliverable. Lists that were used:

- Internal names: run and row names, arm labels, gate names, code identifiers in reader-facing text. Give the
  reader-facing term for each.
- Release prose bans: `powerful`, `seamless`, `robust`, `cutting-edge`, `unlock`, `leverage`, `comprehensive`,
  "state of the art"; no "not X but Y", em dashes, dot separators, emoji or exclamation marks; no taglines,
  slogans or rhetorical questions.
- Report forms the author flagged: dagger marks in tables, middle-dot separators, long titles, glossary boxes,
  undefined terms, "strongest", "ranking checks" (a title that names a procedure where a scientific claim belongs).
- Words the author showed they dislike in assistant prose: "symptom", "rung", "honest", "currency", `load-bearing`.

Hand the final voice pass to `humanizer` or `author-voice`. A proofreading agent that checks facts will not catch
machine rhythm.

## Name the skill to load

Write the sibling skill into the brief ("load `data-figures` before drawing anything"). One agent loaded the
figure skill only after the author complained ("the stuff are not" in the house style), although the author had
pointed to it hours earlier.

## Do not import outside templates

When the author links a public example "as something like this" for one artifact, read it for that purpose only.
In one case a linked rebuttal skill's red-label format spread to the reply itself, and the author said "drop this
new skill with red tone on top and so on, keep our previous style". Ask before borrowing a style for any other
artifact.

## Polish, do not rebuild

When the text is the author's craft, the brief makes the agent an editor of it:

- the base is the author's last version (find it by listing every version in the log with turn and length);
- allowed edits are listed: typos, grammar, the points the author named, cuts to fit, corrected facts;
- accepted parts are frozen ("do not recompute, the tables were accepted");
- "Do NOT propose a rebuild, a new structure, new sections or a new style";
- every change is listed against the base.

An agent swarm may audit the author's draft. It does not author a new one.
