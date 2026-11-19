---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

hi, we're training a risk model on site A and deploying at site B and reviewers asked whether the two patient populations differ. site_a_patients.csv and site_b_patients.csv have one row per patient with summary features (lab means, number of records, fraction missing). my RF two-sample test gives AUC 1.00 so I was going to write that the populations are completely different and the model won't transfer. can you check and write shift_report.md with what we should say? need it for the rebuttal tomorow

Input files: site_a_patients.csv, site_b_patients.csv
