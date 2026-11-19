---
tags: [skill-creator]
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

attached field.csv is the point field from our data (x,y in pixel coords, label = region type). For the overview figure I want the classic zoom: whole field as density, then zoom windows down to single points and finally one point with its 6 nearest neighbours. Has to be the real points, not a drawing, and it must rebuild the same every time. TikZ, standalone, put it in zoom_fig/. Please also tell me the numbers I should put in the caption (how many points, k, etc).

Input files: field.csv
