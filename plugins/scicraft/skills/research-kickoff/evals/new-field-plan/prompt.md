---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, WebSearch, WebFetch]
---

I'm an NLP person and I start next week on ML weather forecasting, which I know nothing about. My idea in one go: "pretrained ML weather models (the graph net ones trained on reanalysis) should have internal embeddings that already know about extreme events like heatwaves, so a linear probe on frozen embeddings should detect them days ahead better than the raw fields do". Can you set me up with a plan, the research questions and what I should do first? Put it in weather_kickoff/. No code yet, I just want to know where to start and what's wrong with my idea if anything.
