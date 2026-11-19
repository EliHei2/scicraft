# Third-party material

None. Every file in this skill is original to this package or the author's own code.

- `references/audit-protocol.md` is original to this package. It is written from the author's own audit rounds
  (a Methods fact-check against code, a merged-supplement review, a manuscript section fact-check, a defense-report
  review, a bibliography audit, a figure audit). Its splits, kinds of finding, verdict words, hand-back format and
  briefs come from those records or were chosen for this package. It shares with common auditing practice these
  general ideas: reviewers who see only the sources, an independent second check that tries to refute each
  finding, a quote and a location for every finding, marking which findings rest on a script and which on
  judgment, and a fresh round after fixes.
- The reference-audit verdicts (`OK`, `FIX`, `REPLACE_IN_TEXT`, `QUERY`; `FIT`, `WEAK`, `WRONG`, `SELF`), the
  figure verdicts (`OK`, `FIX`, `DECIDE`) and the claim verdicts (`TRUE`, `NARROWER`, `FALSE`) are the author's own,
  from the author's audit briefs. The weights (`blocker`, `fix`, `polish`), round verdicts and re-audit words were chosen
  for this package.
- `scripts/remote_zip.py` is the author's own code, ported with an argument parser, digests, a byte comparison, a
  CRC check and a guard against servers that ignore range requests.
- `scripts/extract_numbers.py` was written for this package. Its `--diff` mode uses the numeric-token regex of the
  author's own merge safety net.
