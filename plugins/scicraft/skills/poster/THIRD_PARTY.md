# Third-party material

| Item | Where | Source | License or status |
|---|---|---|---|
| URW Nimbus Sans (`uhvr8a`, `uhvb8a`) | read at run time by `scripts/embed_base14.py` from the local TeX installation; not shipped | URW++ base-35 fonts in TeX Live | GPL with font exception or AGPL depending on release; embedding a font in a PDF is permitted |
| Latin Modern Math, Latin Modern Sans, TeX Gyre Heros | loaded by `assets/poster/poster_design.tex` from the TeX installation; not shipped | GUST e-foundry | GUST Font License (LPPL-based); embedding in a PDF is permitted |
| Helvetica Neue | loaded from the operating system when installed; not shipped | the system's font | used under the system's license; the template falls back to the free faces above |
| No-photos sign layout | `assets/poster/no_photos.tex` | drawn in TikZ after the layout of the ISO 7010 P029 safety sign (camera under a prohibition ring) | the drawing is original; the sign's layout is a public standard pictogram convention |
| Eval paper and figures | `evals/*/files/` | invented for the evals (fictional method, numbers and authors) | ships under the package license |

`scripts/embed_base14.py` is the same file as in the latex-typesetting skill, copied so this folder works alone.
Everything else (template, layout checks, Makefile) is derived from the author's own poster project and ships
under the package license.
