# Knowledge base

Owns one question: what {{NAME}} knows about its field, its data, its methods and its own measurements, and how it knows it. Entries are evidence. What the project does about a fact is a row in `DECISIONS.md` that cites the entry.

## How to use it

1. Read `INDEX.md`: one line per entry.
2. Open only the two or three entries the task needs. Each stands alone.
3. Verify a claim tagged `[U]` before building on it. Before reimplementing a method, read its authors' code or paper.

## Conventions

- One topic per file. The line under the title is a one-sentence summary.
- Header fields: Status, Updated, Sources, Used by.
- Every claim carries a tag: `[RUN]` ran it here (the command or script is named), `[DOC]` read in a source (with its link and the date it was opened), `[U]` unverified.
- A number names the command or the file that reproduces it.
- Code is pointed to as `path/to/file.py:line`. Long snippets are not pasted.
- A link to an entry that is not written yet is allowed only when `INDEX.md` lists it as planned.
- An entry runs to about 100 to 400 lines. Split a longer one.

## Nothing here is stale

A superseded entry moves to `archive/` with a banner naming its successor. An entry you remember and cannot find is archived.

## Layout

```text
INDEX.md      one line per entry; read first
NN_topic.md   the entries, numbered in order of creation
sources/      whole texts that must be read in full (ignored by git when large)
archive/      superseded entries, each with a banner naming its successor
```
