# Third-party material

None. Every script and template in this skill is the author's own work, ported and generalized:

- `scripts/gen_macros.py` generalizes the author's macros generator from a rebuttal build (project paths, record
  names and macro names removed; a JSON spec, `pending` handling and `--strict` added; the number format kept).
- `scripts/check_numbers.py` generalizes the author's prose-number check from the same build (its hardcoded asserts
  became a claims file; the stale-macros comparison and the TeX scan were added).
- `scripts/gen_table.py` follows the author's table generators (self-terminating fragments, sidecar JSON).
- `scripts/verify_contract.py` generalizes the author's contract check from a benchmark repository (the vocabulary
  became a JSON file; sha256 added beside md5).
- `assets/PAPER_MAP.md` and `assets/PARITY_STATUS.md` keep the structure of the author's own documents with the
  content removed.
