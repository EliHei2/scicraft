# Literature and fact check: [project]

Verified on [YYYY-MM-DD]. Scope: [which questions of `SPEC.md` this file serves].

Tags on every statement:
- **[RUN]** verified by running code or by computing from a downloaded file (the method is stated);
- **[DOC]** read in the paper, the documentation or the source file (URL, version or commit, section or line);
- **[U]** unverified: not checked, or checked and still unclear. Every [U] also appears in "Open uncertainties".

Statements from helper agents keep their tags only after a spot check; the statements that were re-checked are
listed under "Provenance".

## 0. Corrections to the specification

Repeats the claim table of `SPEC.md` for the claims this file settles.

| Claim | Verdict | What is true |
|---|---|---|
| "[claim]" | [verdict] | [tag] [correct statement with source] |

## 1. [Paper or method name, as its authors write it]

### 1.0 Identity
- [DOC] [arXiv id, version and date, or DOI checked against Crossref]. Authors: [names as on the paper].
- [DOC] Code: [repository URL] at commit [sha], license [name, or "none found": port the ideas, copy no code].
- [DOC] Weights: [host, size, gate (open, form, token), license], or [U] if not found.

### 1.1 Exact definitions
The quantity the project will compute or compare against, defined exactly, from the code where it exists.

| item | exact definition | source |
|---|---|---|
| [feature, loss term, metric] | [definition with constants] | [DOC] [file:line or equation number] |

### 1.2 Paper versus code
The released code produced the published numbers or weights, so the project follows the code.

| item | paper | code (released) | project follows |
|---|---|---|---|
| [architecture, sizes, sampling, loss weights] | [paper value, table or equation] | [code value, file:line] | code |

### 1.3 Published results the project can re-analyze
- [DOC] [result files the authors released: CSV, logs, tracking export], where and in what format.
- [RUN] [headline recomputed from those files: matches / does not match the paper, and how].

### 1.4 Pitfalls for a replication
- [DOC] [leakage, ordering, preprocessing or typing choices in the original that change the result]

## 2. [Next paper, benchmark or library]

[same blocks]

## [N]. Recommendations for this project (ranked)
1. [recommendation, with the section that supports it]

## Open uncertainties
- [U] [claim], [what would settle it]

## Provenance
- [Every source with version: arXiv vN, repository@commit, package==version, dataset revision.]
- [Scripts behind every [RUN] statement, stored in the repository (`research/scripts/`), never in a temporary
  folder.]
- [Which helper-agent claims were re-checked by hand.]
