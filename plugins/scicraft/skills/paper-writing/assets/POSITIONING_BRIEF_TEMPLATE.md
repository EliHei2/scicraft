# Positioning brief: common instructions (read-only research, one file out)

Shared by every positioning agent; each agent's task adds only the work it covers and its output path.

You are preparing the related-work position of one work, [work name], inside [document: a paper, a
book chapter]. The editors will use your file to write the introduction and related work. You do
not edit any manuscript file.

## What to produce

One Markdown file at [output path], 2,000 to 3,500 words, with these sections in this order:

1. **Landscape.** The closest prior work in 4 to 7 groups by method family. Per work: one plain
   sentence on what it does and which unit or assumption it fixes, and its citation key. Find keys in
   [bibliography key list] by title and author, never by guessing a key. A missing essential work gets
   a complete entry in [new references file], with metadata verified on Crossref, Europe PMC, arXiv or
   the publisher page.
2. **Three gaps.** The three largest limitations of that work that this work addresses. Per gap: the
   gap in one sentence, the evidence that it is real (a cited benchmark, review or measurement), and
   this work's answer in one sentence.
3. **Claims, pressure-tested.** 5 to 8 claims. Per claim: the claim with the number that carries it;
   the evidence (source file and line, or a quote of at most 25 words); the strongest counterargument
   a hostile reviewer would make; the wording that survives it; where in the document it belongs.
   No `first`, `novel` or `state-of-the-art` unless the source paper makes that exact claim and you
   quote it.
4. **The author's own wording.** For each claim, the closest sentence the author already wrote,
   quoted verbatim, from [sources in order of preference]. Editors reuse these sentences, so this
   section matters most.
5. **Handoff.** The sentence that carries the reader from this work to the next unit of the document.
6. **Bibliography defects.** Wrong venues, preprint titles on published records, missing fields, and
   any place where the paper and its code disagree.

## Rules

- Numbers come only from [the facts file] and the sources named in your task. Never invent a number,
  a citation or a role.
- A citation must say what its sentence attributes to it: check the abstract or the text.
- Mark preprints as preprints.
- Search the web with titles, author names and short technical phrases only. Never paste manuscript
  text into a web tool.
- Use the document's terms: [terms file].
- End your final message with one paragraph: the three gaps and the three strongest claims.
