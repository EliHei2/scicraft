# Findings M3: memory notes of the benchmark project

## 1. Sources read
- memory/*.md of the benchmark project (read fully)

## 3. Rules
**R1 [REPRO] Write a manifest (config hash, code commit, seed) beside every results folder.**
- Why: a table could not be traced to its run a month later.
- How: manifest.json written by the runner before the first metric.
- Scope: GENERAL   Strength: standing

**R2 [ORG] Never overwrite a results folder the author has seen; write a new dated one.**
- Why: "keep the old results folder, do not overwrite it".
- How: results/YYYY-MM-DD_tag/.
- Scope: GENERAL   Strength: repeated x2

## 8. Candidate skills
1. **project-structure** (trigger: new project). Must contain R1, R2.
