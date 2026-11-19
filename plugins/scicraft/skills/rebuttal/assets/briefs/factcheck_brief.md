# Fact check of [file]

You are the independent fact checker. A single wrong number or misquotation would be fatal, so verify everything
from primary material and trust nothing you are told, including the authors' notes.

The material is confidential: work only from local files, do not use web search or web fetch, and do not send any
of it to any external service.

Audited file: `[path]`, sha256 [hash]. Primary material: `[paper.txt]`, `[reviews.md]`, `[results/]`,
`[guideline.txt]`.

For every factual statement in the audited file (each number, rank, count, comparison, quotation, line range,
table or figure pointer, venue or journal name, date):
1. Find it in the primary material. Recompute ranks and counts from the printed table values with a script, and
   keep the script.
2. Mark it CONFIRMED, WRONG, IMPRECISE or UNVERIFIABLE.
3. For WRONG and IMPRECISE, give the true replacement wording.

Report: the four counts first, then one row per statement that is not CONFIRMED (location, quoted text, verdict,
evidence with file and line, replacement). Do not edit any file.
