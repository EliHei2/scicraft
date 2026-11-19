# Traps met on the way

Each trap here stopped a real build or shipped a real defect. Most were met in the original
projects; the ones marked "met while building this skill" came up when the shipped assets were
compiled on a basic TeX Live 2025.

## 1. TeX and packages

| Symptom | Cause | Fix |
|---|---|---|
| "Illegal parameter number in definition" at a shim | a stand-in with `#1` defined inside the argument of `\IfFileExists` (needs `##1` there) (met while building this skill) | load conditionally, then define the stand-in after it with `\providecommand`, or inside `\ifdefined ... \fi` |
| "You can't use `\spacefactor` in vertical mode" | a macro containing `@` outside `\makeatletter ... \makeatother` | wrap it |
| "Undefined control sequence" at `\NewEnviron` | `environ` not loaded | load it or define the environment with `\newenvironment` |
| `\crefname` undefined | cleveref missing and a stand-in in use | the stand-in in `shims.tex` provides an empty `\crefname` |
| tcolorbox stops with errors about tagging sockets | a tcolorbox newer than the LaTeX kernel | draw boxes with a savebox plus TikZ or `\colorbox` (the add-on's `insight`), or a shim that provides the socket commands |
| "Missing number, treated as zero" at a table row | a row starting with `[` right after `\\` is read as `\\[<length>]` (met while building this skill) | brace the cell: `{[Baseline 1]}` |
| box shows its body text as a rotated label | text starting with `[` right after `\begin{env}` is read as the optional argument (met while building this skill) | give the optional argument explicitly or start the text differently |
| "Misplaced `\noalign`" at a group row | a row macro with an optional argument cannot expand to `\noalign` first (met while building this skill) | macros used at row start take mandatory arguments only (`\grp{5}{label}`) |
| "auto expansion is only possible with scalable fonts" | `fontenc` T1 with Computer Modern loads bitmap EC fonts on a basic install (met while building this skill) | `\usepackage{lmodern}` |
| "Not a letter" at `\begin{document}` | anything other than letters and hyphens in `\babelhyphenation` (met while building this skill) | letters and hyphens only |
| bibtex "Illegal, another \bibstyle command" | two `\bibliographystyle` calls | one call, chosen by `\IfFileExists{venue.bst}{...}{...}` |
| a narrow table printed with huge text | `\resizebox{\linewidth}{!}` enlarges as well as shrinks (met while building this skill) | `adjustbox` `max width=\linewidth` |
| "10 µmof" | a unit macro swallows the following space | `\um{}` or `\xspace` |
| "Missing $ inserted" at an operator in prose | `\DeclareMathOperator` macro used in text | wrap in `\ensuremath` |
| an extra overfull box from a TikZ label | the label node counts in the bounding box | mark it `overlay` |
| TikZ text-width nodes with wide word spaces on a poster | nodes inherit a 10 pt `\spaceskip` | reset `\spaceskip=0pt\xspaceskip=0pt` inside each text block |
| every citation [?] while the run exits 0 | `main.bbl` not on TEXINPUTS in an out-of-tree build | `TEXINPUTS=build:` (the build script does it); the gate's "missing bbl" check |
| contents and list page numbers wrong after three passes | cross-references not settled | pass until no "Rerun"; fail otherwise |
| about 78 float errors, front matter off center | `\newgeometry` with a margin-note package and asymmetric margins | symmetric geometry without a sidenote column |
| "Misplaced `\noalign`" at an `\input` table fragment | the fragment starts with `\rowcolor`, or `\bottomrule` follows an `\input`-ed row (TeX Live 2025) | make each fragment end its own rows, and mark a highlighted row with a bullet and a bold name in place of `\rowcolor` |
| a decimal-aligned column breaks or misaligns | a cell holds "≤" or another symbol the aligner cannot parse | print plain two-decimal numbers in that column |
| `rsfs10` font not found on a minimal TeX (BasicTeX) | a venue style or `mathrsfs` asks for the script font | `\usepackage{eucal}`, and a local alias of `rsfs10.tfm` to `eusm10.tfm` in `TEXMFHOME` |
| a venue paper built as single-column `article` with `mathptmx` on a minimal install | `microtype` with `mathptmx` was recorded as a combination to avoid there (no cause recorded) | leave `microtype` out of that build and check the page count |
| font substitution error in the bibliography | a `.bbl` sets `\url` in a typewriter font the basic install lacks | `\urlstyle{rm}` in the preamble |
| Greek capitals missing in a Helvetica document | `helvet` has no Greek capitals | declare the math Greek capitals after `\begin{document}`, or take them from the math font |

## 2. Shell and tooling

- A gate that silently passes: `rg` missing in a non-interactive shell plus `|| true` hid 301
  hits; a gate call placed after `exit` never ran. Test every new pattern on a line that must
  match (`bash -c '...'`), and put gates above any `exit`.
- BSD grep (macOS) in a bracket expression needs `]` first, and `[[:blank:]]` in place of
  `[ \t]`.
- zsh: `echo ====` fails (EQUALS expansion; quote it), and `set -- $r` does not split words.
- macOS has no `timeout` and an rsync without `--chmod`; write commands for the machine they run on.
- `argparse` reads a value that starts with `--` as an option: pass gate options as
  `--gate-args="--no-text --max-pages 12"`.
- In JSON edit files every TeX backslash is doubled (`"\\cite"`).
- Disk full from scratch build PDFs during a long session; delete scratch PDFs over 20 MB.
- Do not open, overwrite or rebuild a PDF the author has open; give each delivery its own name.

## 3. Figures inside the document

- Plotting libraries name Helvetica without embedding it: `embed_base14.py` (met while building
  this skill on a PyMuPDF-made placeholder, caught by the gate).
- Cropped published pages keep their headers and DOIs in the text layer; painted-over titles keep
  their text; a superseded method name survived under paint. `scan_figures.py --terms`.
- Text redaction outside a crop with a 1 pt margin deleted visible edge labels; 8 pt was safe.
- A crop that cuts axis or gene labels: keep shared-label panels in one crop; look at every crop.
