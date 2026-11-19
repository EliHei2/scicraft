# Front matter and the publisher's own forms

Every publisher, series and institution has its own rules for title pages, required statements, summaries, AI use
and whether a book may be presented as a collection of published papers at all. This file never states one
publisher's rules. It says how to find the publisher's own forms, follow them word for word, and copy the rest
from real books of the same publisher or series.

## 1. Find and follow the publisher's own forms

1. **Download every document linked from the publisher's or institution's author page**: the author guidelines,
   the title-page template (each language offered), the statements the author has to sign, the policy on text
   reuse, the delivery instructions, and the guidance on generative AI. Convert
   them to text (`pdftotext -layout`) and keep them in the project's knowledge base (defined in the sibling skill,
   `project-structure/references/knowledge-base.md`).
2. **Grep them for rules** and write each binding sentence into `GUARDRAILS.md` (defined in the sibling skill,
   `project-structure/references/governing-documents.md`) with its source. Rules found
   this way in the source work (check yours, they differ): first person singular mandatory and "we" only with
   named collaborators; summaries of the main results in two languages before the main text; which statement
   option applies; where the AI statement sits; data-producer statements in figure legends (met by
   the data-source citation in each legend, with people on the Disclosures page; `figures.md` section 6); the
   delivery deadline; whether the book may be presented as a collection of the papers. Where it may not,
   describe it as "a monograph built from published papers", and reword and flag any sentence, the
   acknowledgements included, that calls it a collection.
3. **Follow the template wording exactly.** Copy institution lines from the author's earlier official documents
   or the template, never from a generic book class. A generic template once replaced the author's own
   institution line and removed the logo, and the author noticed at once.
4. **Drop front-matter sections the guidelines do not require.**
5. **When the author asks "are you sure?", re-check at the source and say why.** Example from the source work: the
   guidelines of a different unit of the institution applied, so the form cited that unit, and this stayed an open
   author decision.
6. **Get the institution lines exactly right.** The author had to correct one of them about six times.

## 2. Copy from two or three real books of the same publisher or series

- **Collect five to ten good books as whole PDFs on disk and open them.** Four of eight rejected openings came
  from working from a summary of an exemplar instead of the exemplar.
- **Pick two or three from the same publisher or series for formalities**: front matter, contribution statements, the
  appendix's level of detail, the citation verb in captions, what bold is used for, whether names and years
  appear in the narrative. "Look if [the local exemplar] had such a thing and only if so include that level of
  detail."
- **Measure, do not guess:** `pdfinfo` for page and text-block size, rendered pages, accent colors sampled from
  pixels, epigraph placement via `pdftotext`, bold spans extracted with PyMuPDF (`span['flags'] & 16`) to learn
  the bold convention. Compare three layout variants (font pt : measure mm : margins) side by side with the
  reference page. Write what was copied into the preamble header, element by element.
- **Exemplars inform; they do not justify.** A two-part grouping copied from an exemplar was rejected, and good
  books ship typos ("uniform finish is itself a machine signal").
- The look itself (classes, fonts, boxes) belongs to the `latex-typesetting` skill.

## 3. The order of the apparatus

The order the source book used, each item verified against a primary record; reorder to the publisher's template:

1. title pages (the publisher's or institution's wording, dates left as macros until set, logo only if the template
   has one)
2. the signed statements, official clauses verbatim, with the AI-use statement inside them where the policy says so
3. front epigraph (optional)
4. Summary, then the second-language summary
5. Acknowledgements, the author's text verbatim and excluded from prose checks
6. Publications and contributions
7. Disclosures (AI use, third-party figures and their licenses, data-use statements)
8. contents, list of figures, list of tables, list of algorithms (each added to the contents)
9. list of abbreviations

Page 2 sits on a recto where the template says so; check blank pages and spill-overs by rendering every front page.

## 4. The AI-use disclosure

- **State the usage only:** the tools, the provider, the main models and their versions, and what each was used
  for, per study where uses differ (for example: implementation help and figure scripting in one study, language
  editing in the book). Name every tool the author names.
- **No sentence about the policy or the guidance.** "Following the guidance of [the publisher], I name these tools
  ..." drew "don't make AI decisions like that :)) don't say such things explicitly :) just state the usage!"
- **No bibliography entry for a chatbot.** AI tools are named as tools, never cited as sources or authors; an
  existing citation of a chatbot was removed.
- **Keep it literally true.** "Every number reported in this book comes from analyses that were executed." Do
  not claim the author personally checked every reference when an agent did.
- **The disclosure, the signed statement and the captions agree.** A readiness check caught the signed statement
  listing
  fewer AI uses than the Disclosures page. An AI-generated figure is disclosed in its caption too.
- Where the guidance asks that AI-generated content be "identified and distinguishable", raise it with the author
  as a decision.

A usage-only statement, as a starting shape (fill from the author's own account, then check it against the
policy's required elements):

```
[Tool] ([provider]; models [model names and versions]) was used for [purpose] in [study or chapter], and
[tool] for [purpose] in [chapter]. All analyses reported in this book were executed, and their results were
checked against the published papers.
```

## 5. Summaries

- **Summary and second-language summary correspond exactly.** Mirror every Summary edit in the translation in the
  same turn; the guidelines required correspondence, and the author's one-phrase edits arrived every few minutes.
- **No figures, no single result numbers, no people's names in running text.** Name the main experiments and
  conclusions, taken from the papers' result section titles. About 700 words, formal first person, spine first.
  "You don't bring a figure in the summary, right? Please don't do it."
- **Every Summary sentence states what an analysis showed.** Find the figure or section each claim comes from and
  write its finding in words (an illustrative ML form: "the pretrained model matched tuned baselines on small tables
  and fell behind on large ones"; in another field: "sensors placed on the north face drifted more than those on
  the south face"). An
  evaluative word such as `plausible` or `promising` in its place drew "what are you talking about?", because a
  reader cannot check it. The finding stays concrete without a number; numbers stay in the chapters.
- **After any edit to either summary, extract the numbers of both files and diff the two sets** (counts of studies,
  years, sample sizes stated in words or digits). Three of four late defects in one book came from tightening the
  summary and its translation in separate passes: one edit, never two.
- The author's pasted Summary wins over earlier edits; list what it reverts.

## 6. Publications and contributions page

Per work: the author list exactly as published with equal-contribution marks, venue, volume(issue), pages, online
date, checked on Crossref or PubMed; the author's own name in bold; no author ranks; one first-person contribution
statement per work, from the paper's contribution section or the author's word. Unpublished work carries its
status in words, and a revised version with more authors is said to be unpublished.

## 7. List of abbreviations

- **Complete and symmetric, or absent.** "Either do all or do none!!" after three complaints.
- Build it from the final printed text: `scripts/acronyms.py chapters/*.tex front/*.tex --defined
  front/abbreviations.tex`, plus the PDF text (`pdftotext`) and the text inside every figure (pdftotext of vector
  figures, OCR of rasters at high resolution). One audit found 129 entries, each confirmed present in the PDF; it
  missed figure-only terms not defined in their captions.
- Define each abbreviation at first use per chapter, never in a heading. Resolve double meanings. Two balanced
  columns, alphabetical. Regenerate after every compaction.

## 8. Epigraphs (optional)

Verify each against an original printing (Project Gutenberg, the Internet Archive, national text archives; grep
with line breaks removed) and record text, author, work, year, page, URL, italics and copyright status in a
`QUOTES.md`. A familiar quote turned out to be a reporter's rewording; one candidate was still in copyright. "A
misquoted epigraph would be worse than none." One quote per chapter at most; the author chooses the tone.

## 9. Register

- First person singular for the author's own work where the publisher mandates it: "the method I developed to ...",
  "I formulated". Results take the method as subject. Collaborators' work keeps their name. Do not write "I" where
  credit is unconfirmed. A dedicated scan agent was needed after two requests for active voice were half applied.
- Formal, not conversational. Banned as conversational: "taught
  me", "where it shines", "I begin with", rhetorical questions.
- **House style the gate does not catch, checked by hand before each hand-over:** no lower-case clause after a
  mid-sentence colon (rewrite as two sentences); every sentence over 45 words read and split unless it is a
  specification (`book_checks.py` lists them); one spelling variety, the author's, throughout chapters, captions
  and front matter. Epigraphs and acknowledgements are exempt from every prose rule.
- **Inline semicolons and mid-sentence colons:** one or two per chapter that carry the sentence may stay ("1-2
  that really make sense you can keep"); see the sibling skill `humanizer`, T16.
- The prose rules themselves (dashes, contrasts, filler) are in the `humanizer` and `paper-writing` skills.
