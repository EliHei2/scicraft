# Report gate

For a report that leaves the session: a benchmark summary for a supervisor, an experiment report, an audit, a
status for collaborators. The question that sets the bar: "is it standalone? if I send it to my prof can [they] open
with no problem?"

## Scripted

- **Opens offline with a double click.** One `.html` with figures embedded as base64 and math pre-rendered to SVG,
  no CDN and no scripts; or a PDF printed by headless Chrome with every `<details>` open. Test by opening the file
  from a folder with the network off.
- **Every number traced** to the record it came from (a results file, a log line); the regenerating command is
  named in the report so it can be rebuilt.
- **No metric read from the last row of a noisy log.** Compare trailing windows (medians over about 2,000 steps
  against the previous window); a "collapse" reported twice from last-row readings cost the author's trust.
  Detail in `training-diagnostics`.

## Read

- **Three sentences of summary first**: what was asked, what was found, what it means for the decision at hand.
- **Per item: kept, killed or inconclusive**, with the run that would settle an inconclusive one. "Do not
  synthesize a conclusion the numbers do not support. If it does not move the probe, say so plainly. That is a real
  and publishable finding."
- **Outcomes reported faithfully**: if a guard fired, which one and what the log showed; if a check was skipped,
  say so.
- **No glossary or limits box at the top** ("unnecessary and total AI slop"), no walls of bold, no large bold type
  for long text ("LESS IS MORE").
- **Figures look like the manuscript's figures**, in the same style, so they can move into the paper unchanged.
- **Missing data is a fetch list**, paste-ready, never an estimate or a new glyph standing in for it.
- **An audit report**: counts by severity, then the five most important findings with location and exact fix,
  then where the rest is.

## Hand over

The file, its size, how to open it, and the one sentence on what it does not cover.
