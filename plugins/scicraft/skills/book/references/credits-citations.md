# Credits, self-citation and references

Wrong credit is a defect as serious as missing credit, and a citation that does not say what the sentence says
is a wrong citation. These rules came from incidents with real people's names in them; the names stay out.

## Credits

- **Credits come only from the papers' author-contribution sections or the author's own word.** Never from
  acknowledgements (courtesy and politics: a credit an audit took from a paper's acknowledgements was rejected at
  once), caption drafts, or an agent's inference.
- **An audit finding based on acknowledgements is a question for the author, never an edit.** Offer the minimal
  neutral form ("following a suggestion by X") as an option in AUTHOR_DECISIONS.md, not as applied text.
- **Never expand initials by guessing.** An earlier draft invented four full names from initials. Keep the
  initials and flag an author action.
- **Do not guess identities.** An agent assumed which collaborator "an old friend" referred to and credited the
  wrong person. Ask, or mark "please confirm".
- **Credit each contribution once.** A brief audit failed a chapter for crediting the same contribution twice.
- **State versions simply** when two people built successive versions of one tool: "version 1 mine; version 2 X's
  re-engineering", plus one provenance paragraph. "Make clear what was each one's contribution ... don't put it
  under the carpet either just make it obvious but smooth."
- **Make collaborator attribution explicit at every mention of their analysis:** the section opening, every
  caption, the conclusions, both summaries and the Discussion. A check also caught the author's own chapter
  crediting the author's analysis "to the study".
- **When the author gives credits in plain words** ("I did the rest :)"), set them as formal sentences.
- **Contested role statements go to the author.** A bibliography agent rewrote the author's role statements on
  the publications page from the published record; the author dropped the section. Rewrite nothing; ask.
- **Never attribute published results to a tool the record does not name.** A local benchmark tool's name had
  spread to 40 places in 14 files, while the published papers name no tool; it became "the benchmark and metric
  suite". Grep every tool, package and instrument name in the book against the papers' text and replace the ones
  the record lacks with the papers' own description. Do not over-correct by asserting the author wrote no code;
  state only what the record says.
- **Affiliations come from official pages** (the group's page, the papers' affiliation lists), only places where
  the work was done, main institution only. An invented affiliation line was wrong twice.

### The contribution slot

- One contribution box after each chapter's opening paragraph (a left-rule box in the source book), plus the
  publications-and-contributions page in the front matter. Name the specific artifact; state what the author
  did, never a sentence about what they did not do.
- A footnote at each chapter opener can carry "The contributions described in this chapter are my own, unless
  otherwise noted." where the exemplar does.
- Collaborators appear in body prose as cited authors or with their named role, never ranked.

## Self-citation and review status

| The author's own work is | In the text | In the bibliography |
|---|---|---|
| unpublished (under review, under revision) | status in words: "under revision at \emph{[Journal]}", "under review at [Venue] [Year]"; no `\cite`, no figure numbers | no entry, or an entry whose `note` carries the status, cited only where the publisher requires a list |
| a public preprint or a published paper | cited for attribution only: the work itself, a figure's source, a data or software release | normal entry; status in `note` when it changed |
| either, used as evidence for a general claim | replaced by an independent source whose fit was checked in full text, or by a `\cref` to the book section | |

- "Do not cite our unpublished work as fact or even our published work ok? If you make a claim, if you bring a
  new figure it's fine to say it's from our under revision." Older public preprints may be cited for
  attribution.
- **List every own citation with its context** before changing them (44 in one chapter). Take preprint metadata
  from the preprint server's API (metadata only; nothing from the book is sent out).
- **A result is never cited to an unpublished manuscript.** "Proved in the appendix of the [unpublished]
  manuscript" became "derived for the study, stated without proof".
- **Do not send unpublished text to external services.** Overlap checks run locally against the author's own
  source texts.

## Citing at the claim

- **Every factual claim gets a citation, right after the clause it supports.** A method or technology name gets
  its citation right after the name. No bundles (`\citep{a,b,c}` at sentence end); two sources for one claim means
  one is decoration. The Introduction was called "severely under-cited"; two citation lanes added about 130
  citations there and five lanes 250 elsewhere (72 new references, 2 wrong entries corrected).
- **Split citation lanes at section boundaries.** Each lane returns a claim map: the sentence, the key, and one
  line on why the source supports it, taken from its abstract or full text. After merging, list every sentence that
  now carries five or more citations and thin each to one primary source per claim; a coverage pass tends to
  overshoot into citation walls.
- **Reuse existing bib keys first**, then verify new ones by DOI (`curl -s https://api.crossref.org/works/<doi>`).
  Dedupe keys and DOIs across lanes against the main bib.
- **Leave the author's own design and results uncited.**
- **Cite the primary source, not a summary of it.** Editorials, research briefings, news pieces and reviews that
  restate a primary result give way to the primary paper. A "research briefing" summarizing a method paper was
  cited as if primary; a reprinted panel was named after another book's reprint instead of its original "Box 2".
- **A claim may not outrun its source.** One audit of about 290 claims about cited works found 50 wrong: 5
  contradicted by the paper, 10 absent from it, 2 citing the wrong paper, 33 material misstatements ("required"
  for "produces"; an atlas of healthy tissue cited for a disease claim; "up to 40 %" corrected to "on average 39 %
  (4 % to 84 %)" from the full text).
- **`\citealp{}` inside an existing parenthesis**; hand-typed "et al." becomes `\citet`.
- **A missing source is a placeholder that fails the gate**, `\citep{NEEDS_CITATION_shortdesc}`, never an
  invented key. "Prefer omission to a hedge, and a hedge to a fabrication."

## The reference audit

Run it with read-only subagents and check every verdict yourself ("I don't want even one single one to be
wrong"; "ask it to really defend its decision").

1. **Extract** the printed references from the `.bbl` (count `\bibitem`), parse the `.bib` with a brace-matching
   parser (a naive regex missed entries with odd bytes), and collect every citation context (the sentence around
   each `\cite`).
2. **Pre-compare** each entry against Crossref by DOI (unicode-normalized difflib on title, authors, venue, year,
   pages); list DOIs that fail to resolve (4 in one audit).
3. **Write house bib rules** (author lists exactly as published, "..., Name, ..." when the author is deep in a long
   list; full given names where the style prints them; title-case protection; DOI for every entry that has one).
4. **Split into chunks of about 56 entries**, one agent each. Brief: "You are an expert bibliographer and
   scientific referee. You audit, adversarially, these entries. The author wants not one wrong reference. You
   audit and propose. You do not edit any book file. Your verdicts will be double-checked." Per entry OK, FIX
   (bib only), REPLACE_IN_TEXT or QUERY; per citation context FIT, WEAK, WRONG or SELF. Agents compile their
   corrected entries with bibtex on a scratch copy (no warnings) and read the rendered `.bbl` for lost capitals.
5. **A style agent** checks conformance. The guidelines in the source work mandated no citation style; what is binding
   is attribution (sources indicated, quotes marked, joint and unpublished work named with status, AI tools
   disclosed). It produced a local `.bst` variant (author lists over 10 cut to 10 plus et al., DOI printed for
   `@misc`) and natbib options `[round,authoryear,sort&compress]`.
6. **The coordinator re-verifies each chunk's corrected entries against Crossref, spot-checks samples, applies
   them, rebuilds.** Keys never change (a key change breaks every `\cite`). One line per change with the source
   URL. 137 of 278 printed entries were corrected in one audit.
7. **After any scripted bib cleaning, diff the key set before and after.** A regex cleaner once lost two entries;
   the key diff caught it. Entries carrying transcription debris (148 had notes and markdown links that would have
   printed) are cleaned only after a snapshot.

Scraped-citation signatures to look for: a free superseded edition, a claim outrunning the source, a key year
contradicting the entry, a preprint title on a published record, truncated "and others", placeholder page
numbers, wrong author first names, a bare-acronym booktitle.
