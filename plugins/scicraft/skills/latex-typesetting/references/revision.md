# The revised paper: one color, one switch

Read this for a revision after review (conference rebuttal, journal resubmission, camera-ready
with marked changes). The reply letter itself belongs to the `rebuttal` skill.

## 1. Prove you hold the submitted source

**Apply revisions to the exact source of the submitted PDF, and prove it before the first edit.**
In the original project the working folder held an older draft: "Only 15.6 % of its sentences
occur in this folder's sources", so a revised PDF built from it "would show reviewers a different
text from the one they reviewed". Hours went into revising the wrong file.

- Export the submitted version from the editor's history (Overleaf history, the git tag, the
  upload archive).
- Rebuild it and compare with the submitted PDF: page count equal, and sentence overlap high.
  A 6-gram sentence match of the `.tex` against `pdftotext` of the submitted PDF scores about
  70 % for a source against its own PDF (macros and math lower it); an unrelated draft scores far
  less.
- Same fonts and text block as the venue build, or the page count lies.
- If the edits were made on the wrong draft, transplant them: list every changed passage with
  `python3 scripts/extract_rev_passages.py *.tex -o REV_PASSAGES.md` (section, the unchanged text
  before it, the passage) and place each one after the matching anchor in the submitted source.

## 2. Mark changes with one light color behind one switch

Load `assets/revision.tex` at the end of the preamble.

```latex
\definecolor{revised}{RGB}{70,130,180}
\newif\ifrevisedcolor \revisedcolortrue
\newcommand{\rev}[1]{\ifrevisedcolor{\ifvmode\leavevmode\fi\color{revised}#1}\else#1\fi}
```

`\leavevmode` keeps a marked paragraph attached to its heading.

| What changed | How it is marked |
|---|---|
| words, sentences, paragraphs | `\rev{...}` |
| a new figure or table | `\revfloat` inside the float (its label "Table 2" in blue) and the **whole caption** in `\rev{}`; the tabular body too when the table has no shading of its own |
| an old float with edits | only the changed words in `\rev{}`; table cell rank colors stay as they are |
| a new term in an equation | `\mathbin{\rev{+}}\rev{\lambda\mathcal{L}_{\mathrm{new}}}` |
| new bibliography entries | `\revbibkeys{key1,key2}` (patches `\@lbibitem`) |
| deletions | cannot be colored: list them in the edit list and the reply |

- **One color in every delivered build.** Per-round colors (orange, then magenta) were thrown
  out: "not different colors bro, just light blue whatever is different from the inital
  submission!! ... don't confuse me and my collegues!" A private second color for your own
  reading of the latest round exists in `revision.tex` as `\latest{}` behind `\showlatestfalse`;
  keep it false in anything sent.
- Decide what is new by comparing with the **submitted PDF**, never with the markup of earlier
  rounds.
- Citations and cross-references inside `\rev{}` keep the link color; the sentence around them
  turns blue.
- The delivered revision is the `\rev{}` build, not a latexdiff output; deletions, which "cannot
  be coloured", are listed in the edit list. A latexdiff per chapter can still be offered to a
  co-author who wants one.
- An earlier round colored only the float label of a new float; the latest instruction colors
  the whole caption of a new float. The latest wins.

## 3. The revised paper reads as the final paper

- It never mentions reviewers or the review, and it contains no submitted-versus-revised tables
  or sentences. Seven such sentences were removed in one round ("compared with ... for the earlier
  checkpoint", "values of the submitted run"). Before-and-after comparisons go to the reply, at a
  high level.
- Check new text with `grep -n -i "submitted\|earlier\|previous\|original\|reviewer"`.
- Integrity: a change that weakens a claim is marked like any other change. A result that
  contradicts a claim changes the claim; a weak result moves to the appendix with its number.

## 4. Build the variants

```bash
python3 scripts/build_latex.py main.tex                                   # marked (blue)
python3 scripts/build_latex.py main.tex --variant revision_clean.tex      # clean copy, same line breaks
```

In the test runs the clean copy's `pdftotext -layout` matched the marked build's line for line
(one run differed by a single blank line in the dump, no word moved). Check
the page limit, undefined references and size on both (`latex_gate.py`).

## 5. The edit list

Keep `REVISION_EDITS.md`: numbered edits (E1, E2 for the main text; A1, A2 for the appendix),
each anchored by the first words and the line of the submitted sentence (from
`pdftotext -layout`), with the action (replace, insert after, delete), the exact `\rev{}` text,
and the page arithmetic (words before and after, lines gained). Every hunk of the final diff
maps to one edit, and every edit to a reviewer point or a note.

For tables and figures to paste into the reply, render each float with its caption to a trimmed
PNG, with a manifest of label, number, page, caption text and a revised flag.
`scripts/render_floats.py` in this skill does it; the `rebuttal` skill calls it:

```bash
python3 scripts/render_floats.py main.tex --check-pdf build/main.pdf            # renders/ + manifest.json
python3 scripts/render_floats.py main.tex --revised-only --out reply/renders     # new floats only
```

It finds floats by label in a marker build, so the reply embeds them by label and stays right
after renumbering. `--check-pdf` refuses to crop when the marker build's text differs from the
delivered PDF. Look at every PNG before a reply cites it. Co-authors who read in Word get the
paper through `latex_to_docx.py` (see `word-export.md`).

Before hand-over, a fresh, adversarial reader checks the package: every reviewer point answered,
every number and line range quoted in the reply true at the cited place, the paper consistent with
itself on the revised pages. Repeat with a new reader until nothing is found (`adversarial-audit`).
