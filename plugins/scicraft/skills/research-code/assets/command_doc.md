<!--
One file per command, numbered in the order a new user needs them (01_[main command].md first).
Most important first, specific details last. Guidance may be drawn from benchmarks; benchmark results
may not appear, except expected time and memory. Delete these comments before use.
-->
# `[command]`

[One sentence: what the command computes, in the user's terms.]

## Idea

[Two to four sentences: what goes in, what is computed and why it is computed that way. Exact
definitions where a number is produced (the formula or the rule), no code identifiers beyond the
command's own flags.]

## Minimal input

[The smallest data that runs: required files, required columns with types and units, what may be
missing. One line per item.]

```bash
[command] -i [input folder] -o [output folder]
```

## Steps

1. [What the command does first, and what it checks or filters, with the count it logs.]
2. [Next step.]
3. [Where the output is written.]

## Output

| File | Columns or keys | Meaning |
|---|---|---|
| `[file]` | `[col]` ([type]) | [meaning, units, what a null means] |

## Parameters, most important first

| Flag | Default | Effect of raising it | Effect of lowering it | When to change it |
|---|---|---|---|---|
| `[--flag]` | `[value]` | [effect] | [effect] | [situation, from benchmark guidance] |

## Time and memory

| Input size | Hardware | Wall time | Peak memory |
|---|---|---|---|
| [rows or items] | [CPU cores or GPU model] | [measured] | [measured RAM or VRAM] |

## Common errors

| Message | Cause | Fix |
|---|---|---|
| `[error text]` | [cause] | [fix] |
