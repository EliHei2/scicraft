# Results ledger: [paper short name], round [N]
Updated: [YYYY-MM-DD HH:MM]

Integrity rule: a held-back result stays in the records and, where it bears on a claim the paper makes, in the
appendix with its number. "Held back" means left out of a reply, never out of the record.

One row per result. Line positions are tokens that `resolve_lines.py` fills from the build, never typed numbers.

| # | Result in one line | In the paper (section, table, line token) | In the replies (comment, point) | Record file and key | Held back from (and why) |
|---|---|---|---|---|---|
| 1 | [ranks first on [k] of [n] tasks against [N] compared methods] | [Sec. 4, Table 1, `[[BENCH]]`] | [general bullet 1; reply R1, W1] | [results/bench.json : methods.ours.rank_counts] | [none] |
| 2 | [ablation: each component lowers the combined score] | [Sec. 4.3, Table 3, `[[ABL]]`] | [reply R2, Q1] | [results/ablations.csv : delta] | [general response, too detailed] |
| 3 | [side analysis not asked for] | [Appendix C, Table 9, `[[APP_C]]`] | [none] | [results/side.json : summary] | [all replies; answers no point, kept in the appendix] |

## Pending

| # | Result expected | Job or owner | Lands by | Slot in the paper | Slot in the replies | Sentence for either outcome |
|---|---|---|---|---|---|---|
| P1 | [rerun at the matched step count] | [job id or name] | [YYYY-MM-DD] | [Table 2, new row] | [reply R3, W2] | [if it holds: "..."; if not: "..."] |

When a pending result lands, move its row up, add its claim to `claims.json`, and rerun `check_numbers.py`.
