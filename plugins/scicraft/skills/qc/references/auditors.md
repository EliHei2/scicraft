# Narrow auditors that only report

The everyday form of the audit: one or a few agents, each with one persona and one fault class, who read the
rendered deliverable and its sources and return findings. They never edit. One writer (the main session) checks
every finding and applies the fixes. For a large staged audit with lanes, skeptics and synthesis, use
`adversarial-audit`.

## Contents
1. When, and how many
2. Roles that found real defects
3. The brief
4. What comes back
5. Vetting and applying
6. Keeping the author's choices
7. Deadlines, limits and dead agents

## 1. When, and how many

- **Default: work solo, one audit agent at a time.** Fan out only when the author asks in so many words ("fan out
  many adversarial nitpicky subagents"). A fleet on a website cost more than it found.
- **Never under a deadline**, even if agents were asked for minutes before; and never to make up for not looking
  yourself. Hand over what builds now, then iterate.
- **Run the machine checks yourself first** (fonts, raster resolution, log warnings, cited keys against the bib)
  and pass each lead to the lane that owns it, named in its brief. In the source audit this sent the
  low-resolution pages straight to the figure lanes.
- **Disjoint files per agent.** Two waves that edit or audit the same files at once clash ("someone is editing
  this file live", "labels may have changed"). Start the next wave per file group as soon as the previous one
  releases it.

## 2. Roles that found real defects

| Persona | Fault class | What it caught in the source work |
|---|---|---|
| figure editor at a top journal | every data figure against the text and tables; ranks recomputed; every bold mark and font size | a panel plotting one effect estimate while the table gave another |
| art editor | pixel level, measured in mm, each fix naming the code constant or line, with crops | row labels off their rows, a third of a panel empty |
| register editor | every printed title, label and caption string; returns string, location, fault, replacement, character count | coined labels, a word meaning something else in the paper's field |
| terms auditor | undefined, uncited or used-before-definition terms; one thing with two names | 49 undefined or late-defined terms and 17 duplicate-name sets in one paper |
| statistics referee | one language, one correction method, every test defined, family dependence | mixed correction methods, a value marked significant that was not |
| fact checker | every statement against primary material; CONFIRMED, WRONG, IMPRECISE, UNVERIFIABLE counts with replacement wording | four factual errors a talk would have stated |
| hostile reader, one per reviewer | every objection to the reply that an area chair would accept, with the worst follow-up question | a claim true by one metric only |
| citations in context | every factual claim has a citation that supports it; existing keys reused first | an introduction with whole paragraphs uncited |
| delivery readiness | formal requirements: title page fields, signed statements, summaries corresponding, size cap, fonts, links, bookmarks | a signed statement listing fewer AI uses than the disclosures page |
| independent checker of a builder | re-runs the builder to a temporary folder and compares with `cmp`, recomputes every value with its own code, re-renders and compares pixels | three citations lost from a deposited table; a caption still describing a fit the plot no longer used |

Pick the two or three roles whose fault class the deliverable is most exposed to. A table of numbers needs the
fact checker and the statistics referee; a figure set needs the figure and art editors; a reply needs the hostile
reader and the proofreader of `proofread-loop.md`.

## 3. The brief

`assets/auditor_brief.md` is the template. Order:

1. **The job and when it is done.** Persona, fault class, the deliverable, "read-only: do not edit any file".
2. **Places.** The snapshot folder, the sources of truth (records, the earlier version, the verbatim request).
3. **Rules.** One shared rules file for all lanes (paths, build command, the author's house rules, the report
   format), read in full first; then the lane's own constraints ("figures may only be cropped, arranged, resized,
   moved or split, never re-made"; "never propose adding a package").
4. **The author's rule, verbatim**, when the audit exists to enforce it ("THE AUTHOR'S RULE (verbatim): ...").
   Agents then apply the rule as it was meant.
5. **Known corrections**, flagged "do not report this as a finding", so the lane does not spend its time on them.
6. **Out of scope**, and which other lanes cover what ("two other agents are checking X and Y; do not duplicate").
7. **The report contract** (section 4) and a time box ("deliver within about 20 to 25 minutes").
8. **Confidentiality** for unpublished material: local files only, no web search, no external service.

The brief carries facts and the question, never a conclusion. A preamble that asserted a claim three lines above a
table refuting it was "confirmed" by six agents; the author caught it by asking the obvious question. Diff every
assertion in a shared preamble against the raw output before sending it.

## 4. What comes back

```
Counts: 0 critical, 2 major, 8 minor (4 of them QUERY)
Five most important:
F1 | major | results.tex:212 (p. 7) | "significantly above all comparators" | one comparator not separated (Table 2, row 9) | -> "significantly above [n − 1] of [n] comparators"
...
Not determined: the color of the dashed line in Fig. 4 (vector, not extractable)
Confidence: high for F1 to F6; F7 depends on which records are final
```

- Severity: critical, major, minor, or QUERY (the author must decide; no edit proposed).
- Every finding: location, the quoted current text, the problem, the exact fix.
- Proposed edits as data, one list per lane:

```json
[
  {"id": "F1", "file": "sections/results.tex", "old": "significantly above all comparators on every task",
   "new": "significantly above [n − 1] of [n] comparators on every task", "why": "Table 2 row 9 is not separated",
   "severity": "major"},
  {"id": "F7", "file": "sections/results.tex", "old": "...", "proposed": null, "why": "which records are final?"}
]
```

- Each `old` occurs exactly once in the current file, is at least 30 characters long, sits on one line, and does
  not overlap another edit. "Taking out the inserted citations gives back the original wording" is the self-check
  for a citation lane.
- Some harnesses block subagents from writing report files. Ask for the findings in the final message as the
  fallback, and save them yourself.

## 5. Vetting and applying

1. Back up the target files.
2. For each finding: read the cited lines in the file, render the cited page region, check the fact against the
   source. Accept, adjust (wrong panel targeted, wrong line), or decline with a reason. "The unrounded values decide
   the sort, as the caption promises" is the kind of reason to give.
3. Apply accepted edits with the validator; it writes nothing unless every edit passes:

```bash
python3 <skill>/scripts/apply_audit_edits.py lane_figs.json --root paper/                       # check
python3 <skill>/scripts/apply_audit_edits.py lane_figs.json --root paper/ --apply --backup-dir _bak/pre_figs --skip F7 --ban banned.txt
```

4. Rebuild, rerun the gates, look at the changed pages, commit a checkpoint.
5. Prove the scope: `text_drift.py before/ after/ --show` shows that only the named sentences moved.
6. QUERY items and unconfirmed credits go to one file of author decisions ("Only you can settle these"), and into
   the report's "please check".

A finding from another session or a cluster job is a lead, not a fact. Verify it in the records before writing it
in; the cluster audits were "right on substance twice", and every catch was still checked.

## 6. Keeping the author's choices

- The author's taste overrides the panel's aesthetic verdict. Flag a caveat hard, once; then do what the author
  decides and keep a backup for an instant revert.
- Record each deliberate choice as a keep-as-is guard in the shared rules file, so the next round does not undo it.
- Decline audit suggestions that contradict the author's explicit wishes, and say so in one line.
- When a rule is applied literally beyond its intent (an agent removed a software license sentence under a rule
  meant for figure captions), surface it as a question.

## 7. Deadlines, limits and dead agents

- When the author says it is taking too long, tell each running agent to wrap up ("stop new checks and report your
  verified findings within the next few minutes"), commit the verified state, and keep building in parallel.
- Agents killed by a rate limit are resumed with a short message to their ID ("Resume your <lane> from where you
  stopped; the rate limit has reset. Same rules."), not relaunched. Check first which lanes left files; a killed
  agent can still have delivered.
- An agent that reports "completed" with an empty result has not delivered. Check its gates yourself.
- Before reporting done, confirm no agent is still running.
