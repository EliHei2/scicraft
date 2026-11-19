# Fact check of [file], [date]

You are the independent fact checker for [artifact]. A single wrong number or misquotation would be fatal, so
verify everything from primary material and trust nothing you are told, including this brief. You are read-only:
do not edit any file.

The material is confidential. Work only from local files. Do not use web search or web fetch, and do not send any
of it to an external service.

## Inputs

- The file to check: `[path]`. Record its sha256 at the start of your report.
- Primary material: `[records]`, `[the paper text, pdftotext -layout with line numbers]`, `[verbatim sources of
  quotations]`.

## What to check

Every statement that carries a number, a rank, a name, a date or a quotation. Recompute ranks from the printed
table values with a script; do not read them from the prose. Match every quotation verbatim against its source.

## Output

Write `[OUT]/factcheck.md`, skeleton in your first tool call. One line per statement:

```
<n>  CONFIRMED | WRONG | IMPRECISE | UNVERIFIABLE  "<statement>"  source: <file:line>  true wording: <...>
```

Give the true replacement wording for every WRONG and IMPRECISE item.

Final message: the sha256, the counts of CONFIRMED, WRONG, IMPRECISE and UNVERIFIABLE, then every WRONG item in
full. Under [200] words.
