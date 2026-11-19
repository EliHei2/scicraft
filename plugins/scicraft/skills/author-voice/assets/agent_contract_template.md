# CONTRACT: [task] on [file]

Read this whole file before touching anything. It overrides any general style guidance you carry.

## Baseline

- The text you edit is [author]'s. Their latest version is [path]. It was copied to the snapshot [snapshot path],
  which is the restore point. Back up your own input file before your first edit.
- Their rules are in [rules file]. They are binding. When anything you believe conflicts with them, the rules win
  and the item is dropped.

## Scope

- You edit only [file]. Everything else is read-only.
- Your deliverable is [exactly what]. Nothing else: an idea for something extra goes in your report in one line.
- Allowed changes: [errors of fact, number, pointer; cuts to meet the limit of N words; the updates listed below].
- Not allowed: rewording to improve, new headings, re-titling, moving paragraphs, new sections, a new style.
- Updates the author asked for (old value to new value): [list].

## How to edit

- Each change is one old to new pair that matches exactly once, appended to [edits.json] with its reason and, for a
  fact, the source quote. Apply it to the snapshot with
  `python3 [skill]/scripts/apply_layer.py [snapshot file] [edits.json] [file]`; do not edit by hand around it.
- A trim moves whole floats and procedural paragraphs verbatim to [appendix file] and deletes whole sentences. It
  adds no sentence and no number, except a connective of at most 8 words, logged with its line.

## Gates (all must pass before you report)

```bash
python3 [skill]/scripts/drift_gate.py [snapshot] [current] --min-kept 0.80 --max-lost 0.10 --allow-numbers [values]
```

- Same or near at least 80 %, lost at most 10 %, each lost sentence listed with its reason.
- Numbers unchanged except the listed updates; label and citation sets unchanged; headings unchanged.
- Word count: [target or cap], together with the drift floor above.
- [build command] with zero undefined references.

## Report (at most [N] words)

- Words before and after; gate output; files touched; path of the edit log.
- Numbered questions for the author, where you would otherwise have guessed.

## If you are stopped or limited

Your partial edits are in [edits.json]. On resume, continue exactly where you stopped; do not re-run steps that are
already logged.
