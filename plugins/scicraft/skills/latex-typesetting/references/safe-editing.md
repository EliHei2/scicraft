# Editing a heavily worked TeX file safely

Read this before changing a manuscript, book chapter or reply that its author has already
worked over many times. The request that set the rule: "make sure nothing else changes... it's
been worked so much."

## The procedure

1. **Back up.** `cp main.tex main.tex.pre-YYYYMMDD-label` (or a scratch copy named
   `main.ORIGINAL.tex`). One backup before each transformation: page cut, de-slop, humanize,
   review fixes. `apply_tex_edits.py` writes this backup itself.
2. **Compile a baseline of the untouched file** into its own folder
   (`build_latex.py main.tex --outdir build_orig --no-gate`), and keep its log. When the machine
   lacks a package the file uses, put one-line stub `.sty` files (`\ProvidesPackage{x}`) in a
   scratch folder on TEXINPUTS (`--texinputs stubs`); the `.tex` itself stays unchanged.
3. **Map each requested change to evidence** (the code, the logs, the record) before writing it.
   Settle small items yourself; for many items, use read-only fact-finding helpers.
4. **Apply edits in themed batches of exact-string replacements with count checks.** Write the
   batch as JSON (`id`, `file`, `old`, `new`) and run
   `python3 scripts/apply_tex_edits.py batch1.json --dry-run`, then without `--dry-run`. Every `old`
   must occur exactly once; otherwise the whole batch for that file is refused and nothing is
   written. Renumbering also goes through count checks.
5. **After each batch**, read the changed lines (`apply_tex_edits.py` prints their numbers; `sed -n`
   them) and grep for dangling references to anything you trimmed. `apply_tex_edits.py` also compares
   the multisets of cite keys, ref targets, labels and numbers before and after; any change it
   lists must be one you meant.
6. **Compile into a new folder and compare with the baseline**: errors, undefined references,
   overfull boxes, page count. A typical catch: a verbatim command (`\path`, a custom code macro)
   inside a macro argument, which compiles alone and fails there. In a caption write
   `\protect\path{...}`; where the identifier holds `%` or `#` inside another macro's argument,
   use `\texttt` with `\allowbreak` at the break points.
7. **Diff and tie every hunk to a request:** `diff -u main.tex.pre-... main.tex > changes.diff`.
   "Every hunk in the diff maps to a requested fix." A hunk with no request is reverted or asked
   about.
8. **Report** in this order: decisions first; then resolved, narrowed, still open (one line
   each); "Found but not changed (outside your list)"; the paths of the edited file, the backup,
   the diff and the preview PDF.

## Rules around the procedure

- **Polish the edges; do not rebuild.** After a three-hour multi-agent restyle: "you made it sooo
  werid ... just try to polish the edges ... what you did is super overwhelming." Change only what
  was asked, and list the changes in a few lines.
- **Preserve contract**: every `\cite`, `\ref`, `\eqref`, equation, macro, defined term and number
  stays byte for byte unless the request names it. Check with
  `grep -oE '\\(citep|citet|cite|ref|eqref|cref|Cref)\{[^}]*\}' main.tex | sort | uniq -c` before
  and after.
- **The author's own text gets error fixes only.** When a compaction created an ambiguity, restore
  the author's original sentence.
- **When the wording asked for contradicts the records, write the true version, say why, and offer
  the edit that would make the requested version true.** Asked to describe a run as [N] splits
  where the logs showed a different number of subsets, the true sentence named what the logs show,
  the reply explained what the requested wording would wrongly imply, and it offered the rerun that
  would make the short version a one-line edit.
- **Open-item markers stay few and one line each.** Twenty orange author actions became two after
  closing what the sources could answer: "so many open stuff ... it looks so undone".
- **Triage each open item three ways.** Close it from the sources when they answer it (a recount,
  the logs, a release date on the package index, a co-author's protocol file). Delete it when it
  is harmless, keeping the description of the method. Otherwise compress it to one line naming
  who can answer it. Fixes to files the author edits personally (a co-authored Word file) go into
  one Markdown checklist, each item quoting the current wording so it can be found by search.
- When the author pastes a new version of a passage, it wins; list exactly what it reverts of
  earlier edits.
- To prove a pass did not rewrite the author, measure sentence drift between versions (share of
  sentences same, near, edited, lost); a target used was same plus near at least 80 % and lost at
  most 10 %, each lost sentence logged with its reason.
- Parallel helpers propose edits as JSON with the exact `old` text; one writer vets and applies
  them (`apply_tex_edits.py` refuses an `old` that is not unique). Helpers never build in the shared
  build folder.
