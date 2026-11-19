# Verifier brief: [finding id(s)]

You verify findings raised by another auditor of [target]. Read-only on [repository or folder]. Write ONLY into
[OUT folder].

**Your default verdict is REFUTED.** Change it only if you can show the defect yourself: the line of code, the
output of a run you made, or the sentence in the cited source with its page. Reading the finder's explanation is
not evidence. Re-run what can be run.

## The findings

[Paste each finding: id, where, problem, severity, the evidence it cites, the proposed fix. Leave out the finder's
wider reasoning.]

## Sources

- Snapshot: [path], sha256 [hash].
- [Logs, tables, papers, the author's RULES.md.]

## For each finding, decide

1. Does the defect exist as described? Quote what you checked.
2. Verdict: CONFIRMED, CONFIRMED-WEAKENED (real but narrower, rarer or less severe; say how) or REFUTED (say why).
3. Corrected severity.
4. Is the proposed fix the smallest one that restores correctness? Does it loosen a check, change behavior or
   change a claim (then it is semantic and goes to the author)? Could it break something else? Name it.
5. Does the finding contradict a rule in RULES.md? Then say so; the rule wins.

## Output

[OUT]/verify_[id].json: a list of {"id", "verdict", "evidence", "severity", "fix_ok", "fix_note", "type"}. Write
the file skeleton first, then fill it. If you cannot write files, put the JSON in your final message.

Final message: counts per verdict and one line per finding.

---

# Completeness critic brief

You read an audit's coverage, not the artifact's details. Inputs: the lens table [path], the findings so far
[paths], earlier audit records [paths], the artifact's file list or table of contents [path].

Answer, each with a list:

1. Which files, modules, sections, figures or claims did no lens read in full?
2. Which fault classes from the catalog were not run on this target?
3. Which finders returned empty lists without saying what they read?
4. Which known traps from earlier records were not re-checked after the latest changes?

Write [OUT]/completeness.md. Its gap list is the next round's target.
