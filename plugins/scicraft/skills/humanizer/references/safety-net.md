# The safety net

A style edit is read for style, so a dropped number, a lost citation or a sentence that now says something
slightly different slips past the eye. Verify mechanically after every pass, then read.

## Before the pass

```bash
cp draft.tex draft.before.tex                                   # the snapshot every check compares against
python3 <skill>/scripts/frame_density.py draft.tex > counts.before.txt
```

For pasted text, save the pasted version to a file first; the same checks then run on it. For a file someone
else may be editing, record its checksum (`md5 -q draft.tex` on macOS, `md5sum` elsewhere) and confirm it is
unchanged right before you write, so a concurrent edit is not overwritten.

## After the pass

```bash
S=<skill>/scripts
python3 $S/preserve_diff.py draft.before.tex draft.tex      # numbers, keys, labels, equations, code: exit 1 on any loss
python3 $S/frame_density.py draft.tex                       # dashes and frames: compare with counts.before.txt
```

For LaTeX, build and read the log. The build has zero undefined references and no new errors:

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
grep -E 'Citation .* undefined|Reference .* undefined|^! ' main.log      # must print nothing
```

## What preserve_diff checks, and why

| Check | Passes when | What a failure usually means |
|---|---|---|
| numeric tokens (`\d+(?:\.\d+)?`, as a multiset) | identical | a number was rounded, merged ("two and three" became "both") or dropped with its sentence |
| citation keys | identical in both directions | a sentence with a citation was cut, or two citations were merged into one |
| `\label` and reference targets | identical | a figure or equation reference went with a cut clause |
| numbered equations, display math | same counts | a display was turned into inline prose or lost |
| brace balance (TeX) | unchanged | an edit split a command |
| inline code, code blocks, link targets (Markdown, text) | byte-identical | prose editing reached into a command, a path or a URL |
| duplicate sentences | no new ones | a sentence was moved and not removed from its old place |
| word count | reported, warned when shorter | see below |

**Read the length change.** In the technical register a careful pass lengthens the text by about 3 to 5 percent,
because a sentence with three clauses becomes two or three sentences. One measured run went from 35,000 to 36,274
words with zero labels or citations lost and 18 of 18 equations intact. A shorter result usually means facts
were deleted: go through the cuts one by one. In the general register, cutting closers, filler and
re-explanations shortens the text legitimately; read the cuts anyway.

## When a check fails

- **Restore from the snapshot; do not re-type from memory.** Copy the original sentence back and redo the edit.
- **A number that looks wrong is not fixed by the humanizer on its own judgement.** Check it against the record
  (the table, the figure, the run log, the script). If the record shows a different value, report both and fix
  only with the evidence named; if there is no record at hand, mark `[AUTHOR ACTION: ...]` and leave the number.
- **A fact the rewrite needs and the source lacks is never supplied.** Write a simpler sentence or ask.

## What scripts cannot check

Meaning. A sentence can keep every number and change what the number refers to, the direction of a comparison,
the scope of a claim ("all" for "most") or a hedge. After the scripts pass, read the old and new versions of
every changed sentence side by side (`diff` or `git diff --word-diff`) and confirm each says the same thing.
Say in the report which checks ran and which did not (for example, "the LaTeX build was not run").
