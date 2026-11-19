---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I need figure 1 for our self-supervised learning paper, in TikZ please, the paper body is Helvetica-ish sans so the figure should match. The model: a context encoder f_theta sees only the visible patches of the input, a predictor g_phi takes the context embeddings plus learnable mask tokens and predicts the embeddings of the masked patches, the targets come from a target encoder f_xi that sees the full input and is an EMA of the context encoder, with stop-gradient on the target branch, and the loss is an L1 distance in latent space. Keep it minimal, no slide look, the last version a student made had overlapping boxes. Camera ready is friday so just give me the tex and pdf in a folder called fig1/.
