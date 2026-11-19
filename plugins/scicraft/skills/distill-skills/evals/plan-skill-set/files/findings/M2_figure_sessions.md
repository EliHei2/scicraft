# Findings M2: two long sessions that built the ablation figure and the group-meeting slides

## 1. Sources read
- digests/sessions/bench/11111111_001.md to _004.md (read fully)

## 2. Taste in his words
**FIG**
- "the legend goes outside, I can't read the bars" (2026-03-05, 11111111_002)
**TALK**
- "one point per slide, my words, not yours" (2026-03-06, 11111111_004)

## 3. Rules
**R1 [FIG] Put the legend outside the plot area, right of the axes.**
- Why: a legend over the bars hid the smallest ablation arm twice.
- How: ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5)).
- Scope: GENERAL   Strength: repeated x2

**R2 [FIG] Text in figures is near-black, never gray.**
- Why: repeated correction.
- How: #111111 for all text.
- Scope: GENERAL   Strength: repeated x3

**R3 [TALK] One point per slide, in the author's own sentences.**
- Why: "my words, not yours".
- How: titles are cut from his paper; no paraphrase.
- Scope: GENERAL   Strength: standing

## 4. Procedures
**P1 Render and look**
1. Save PDF and PNG at 300 dpi.
2. Open the PNG at 100 percent and check legends, labels and zero lines before sending.

## 5. Failure to fix
- **F1** Legend over the bars hid one arm; moved outside. Implies R1.

## 6. Assets to ship
- `figstyle.py`: matplotlib rc settings for the house style; general.

## 7. Vocabulary and naming
- "arm" is one variant in an ablation.

## 8. Candidate skills
1. **figure-style** (trigger: any plot). Must contain R1, R2, P1.
2. **talk-slides** (trigger: any deck). Must contain R3.

## 9. Sensitive items seen
- 11111111_003: the in-house dataset's name and its row count. Not copied.

## 10. Contradictions and changes over time
- Early sessions used a gray legend frame; from 2026-03-05 no frame at all. Latest wins.
