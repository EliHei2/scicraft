# Third-party material

| Item | Where | Source | License or status |
|---|---|---|---|
| `\FloatBarrier` stand-in in `assets/shims.tex` | written out from the logic of the `placeins` package | placeins, Donald Arseneau | placeins is distributed as public domain on CTAN; the stand-in is a short reimplementation |
| Bibliography entries in `assets/*/refs.bib` and the eval fixtures | three published papers (He et al. 2016; Kingma and Ba 2015; LeCun et al. 1998) | bibliographic metadata, checked against Crossref where a DOI exists | facts, not copyrightable |
| URW Nimbus Sans (`uhvr8a`, `uhvb8a`) | read at run time by `scripts/embed_base14.py` from the local TeX installation; not shipped | URW++ base-35 fonts in TeX Live | GPL with font exception / AGPL depending on release; embedding a font in a PDF is permitted |

Not shipped: no venue style file (`.sty`, `.cls`, `.bst`) is included. The venue profile was
compiled once against a conference style kept outside this folder; users place their
venue's files beside `assets/venue/main.tex` themselves.

Everything else (preambles, house add-on, scripts) is derived from the author's own projects and
ships under the package license.
