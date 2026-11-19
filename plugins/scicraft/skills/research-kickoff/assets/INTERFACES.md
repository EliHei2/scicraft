# Interface notes: [project]

Every fact below was read from the installed source or measured by running code on [machine], on [YYYY-MM-DD],
**before** the main experiment started. Tags: [RUN] measured, [DOC] read in source or documentation, [U] not
checked. Re-verify every line after any upgrade: these libraries change between minor releases.

## 0. Contradictions with the specification (read this first)

| Specification claim | Verdict | What the installed code does |
|---|---|---|
| "[claim]" | [verdict] | [tag] [behavior, with file:line or the command that showed it] |

## Environment

[Paste the output of `scripts/env_pins.py <packages> --repo .` here.]

Install notes:
- [packages installed with `--no-deps`, and why]
- [packages that must not be installed into this environment, and what they would change]
- [core packages of a hosted runtime that are pinned with a constraints file and never upgraded]

## [library] [version]

- **Signature.** [RUN] `[function or class with every argument and default, copied from the installed source]`
- **Returns.** [RUN] [shapes, dtypes, padding, what is in which position]
- **Defaults that matter.** [DOC] [defaults that differ from the published recipe or from the previous version;
  the version where they changed and the changelog entry, or "not in the changelog"]
- **Determinism.** [RUN] [seed arguments; what must be seeded by hand; behavior across processes and hash seeds
  (`scripts/hashseed_check.py`); worker settings that crash or deadlock]
- **Invariances measured.** [RUN] [what the analysis relies on (row order, column order, labels, device,
  precision) and the measured relative change for each, with the tolerance the tests will use]
- **Traps.** [RUN] [each surprise with its fix, one line each]
- **Timing.** [RUN] [input size, device, seconds]

## [next library] [version]

[same blocks]
