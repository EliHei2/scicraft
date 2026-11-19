# Third-party material

| Item | Where | Source | License |
|---|---|---|---|
| Inter (variable, Latin subset, woff2) | `assets/starter/public/fonts/inter-latin-wght-normal.woff2` | The Inter Project Authors, packaged by Fontsource | SIL Open Font License 1.1; full text in `assets/starter/public/fonts/Inter-OFL.txt` |
| IBM Plex Mono 400 and 500 (Latin subset, woff2) | `assets/starter/public/fonts/ibm-plex-mono-latin-*-normal.woff2` | IBM Corp., packaged by Fontsource | SIL Open Font License 1.1; full text in `assets/starter/public/fonts/IBMPlexMono-OFL.txt` |
| Helvetica Neue | named in `site.css` and the docs | Linotype | commercial; never shipped, used only where the visitor has it installed |
| OKLab conversion constants | `scripts/darken_figure.py` | Björn Ottosson, "A perceptual color space for image processing" (2020) | published formulas; the reference code is public domain or MIT |
| puppeteer-core | required by the node scripts, not bundled | Google | Apache License 2.0; installed by the user |
| PyMuPDF | required by `darken_figure.py` and `tex_labels.py`, not bundled | Artifex | GNU AGPL 3.0 or a commercial license; installed by the user |
| cryptography | required by `gate.py`, not bundled | the Python Cryptographic Authority | Apache License 2.0 or BSD; installed by the user |
| numpy, shapely (2.1 or later) | required by `pack_points.py` (numpy) and `build_masks.py` (both), not bundled | NumPy and Shapely developers | BSD 3-Clause; installed by the user |

The fonts ship with the starter so a private preview makes no request to a font service. Keep the license files next
to the fonts wherever the fonts are copied; `gate.py` deploys them with the site.

All other code, text and example data are the author's own, ported from the author's projects.
