# Third-party material

No third-party code or text is copied into this skill.

| Component | Use | License |
|---|---|---|
| MathJax (`mathjax-full` 3.2.2, npm) | `scripts/render_math.js` calls its documented node API to turn TeX into SVG. The package is installed by the user and is not shipped here. The SVG it produces is embedded in the user's report. | Apache License 2.0, Copyright (c) The MathJax Consortium |
| Google Chrome, Chromium or Microsoft Edge | `scripts/build_report.py` calls the installed browser's headless print to make the PDF. | each browser's own license; not shipped |
| `markdown` (Python-Markdown) or pandoc | optional converters for Markdown sources; called if installed, not shipped | BSD-3-Clause (Python-Markdown), GPL-2.0-or-later (pandoc) |

`scripts/build_report.py` and `assets/report_template.html` are ported from the author's own report builder and
stylesheet. `scripts/render_math.js` replaces the author's MathJax helper, which did not survive; it was written
for this skill from the MathJax documentation.
