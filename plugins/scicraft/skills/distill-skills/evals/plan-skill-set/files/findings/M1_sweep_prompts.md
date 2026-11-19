# Findings M1: every prompt typed in a tabular-classifier benchmark project

## 1. Sources read
- digests/history/history__bench_001.md and _002.md (read fully)

## 2. Taste in his words
**ML**
- "same budget for every baseline or the table is worthless" (2026-03-02, history_001)
- "never retune the baselines after seeing the test split, write that down" (2026-03-03, history_001)
**FIG**
- "no gray text in the figure, and the ablation bars start at zero!!" (2026-03-03, history_001)

## 3. Rules
**R1 [ML] Give every baseline the same tuning budget in wall time and trials.**
- Why: two baselines got half the budget in a sweep and looked weak; caught by an audit agent.
- How: one budget constant (600 s per table, 50 trials) read by every runner; log it per run.
- Scope: ML   Strength: repeated x3

**R2 [ML] Freeze hyperparameters before the test split is opened.**
- Why: "never retune the baselines after seeing the test split".
- How: write the config hash to the results manifest before evaluation; refuse to evaluate if it changed.
- Scope: ML   Strength: standing

**R3 [FIG] Bars start at zero; text is near-black (#111111), never gray.**
- Why: his correction on 2026-03-03.
- How: ax.set_ylim(bottom=0); text color #111111.
- Scope: GENERAL   Strength: repeated x2

**R4 [AGENT] Ask an audit agent to check equal budgets before the table is written.**
- Why: the audit found the 300 s versus 600 s mismatch.
- How: one read-only agent, brief names the budget constant and the log field.
- Scope: GENERAL   Strength: once

## 4. Procedures
**P1 Baseline sweep**
1. Set BUDGET_S = 600 and TRIALS = 50 in config.py.
2. Run `python3 sweep.py --budget 600` for each of the five baselines on all 30 tables.
3. Check the per-run log for equal budgets before writing the table.

## 5. Failure to fix
- **F1** Two baselines ran with 300 s after a config copy; their scores looked weak. Fixed by one budget constant and an audit. Implies R1 and R4.

## 6. Assets to ship
- `sweep.py`: runs any baseline under a budget; general; strip the project's dataset paths.

## 7. Vocabulary and naming
- "budget" means wall time plus trial count, always both.

## 8. Candidate skills
1. **ml-baselines** (trigger: a benchmark table with baselines). Must contain R1, R2, P1.
2. **figure-style** (trigger: any plot). Must contain R3.

## 9. Sensitive items seen
- history_002 line 40: a collaborator's name and an unpublished accuracy for the in-house model. Not copied.
- history_001 line 12: a pasted API key (redacted in the digest). Owner must rotate it.

## 10. Contradictions and changes over time
- On 2026-03-20 he asked to "drop the two tables where the baseline beats us from the main table, nobody will check". Earlier (R2) he insisted on frozen, fair comparisons.
