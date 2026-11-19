# Building the report

`scripts/build_report.py` turns one source into an offline HTML page, a print page and a PDF.
`scripts/check_report.py` checks the result against the report shape. Both run on Python 3.9 or later with the
standard library alone; the optional parts are listed below.

## 1. Setup

| Part | Needed for | Install | Without it |
|---|---|---|---|
| node 18+ | math to SVG | system package manager | math stays plain TeX text, with a warning |
| mathjax-full@3.2.2 | math to SVG | `npm install --prefix ~/.cache/report-mathjax mathjax-full@3.2.2` | same |
| Chrome, Chromium or Edge | the PDF | system install | no PDF; print `_print.html` by hand |
| `markdown` package or pandoc | Markdown sources | `pip install markdown` in a virtual environment | write the source as HTML |
| PyMuPDF, Pillow | page previews and contact sheet | `pip install pymupdf pillow` in a virtual environment | read the PDF in a viewer |

The builder finds mathjax-full through `--mathjax-dir DIR` (the folder given to `npm --prefix`), then the
environment variable `MATHJAX_DIR`, then a `node_modules` folder next to the scripts.

## 2. Sources

- **The filled template** (`assets/report_template.html`): a `<title>`, a `<style>` and a `<main>`. Copy it to
  `code/report.html` and replace every [bracketed] placeholder.
- **A split source**, as in the original project: `_head.html` holds the title and style, `_main.html` the content.
  Build with `build_report.py _main.html --head _head.html ...`. A page that loads MathJax from a CDN for live
  preview can keep its `<script>` tags in the head file: the builder takes only the head's `<title>` and `<style>`.
- **Markdown** (`assets/report_template.md`): optional `title:` and `meta:` lines at the top, then Markdown.
  Raw HTML blocks pass through, which is how the bold section lead (`<p class="msg">`), the TL;DR box and figures
  with captions are written. Math spans are protected from the Markdown converter. The template's style is used.

Math is written as `\( inline \)` and `\[ display \]`. Dollar signs are left alone, so prices and shell
variables in the text are safe.

## 3. What the builder does

1. Reads title, style and `<main>`; for Markdown, converts it with math protected.
2. Removes `@import` and `@font-face` rules and web-font names from the style; system fonts remain.
3. Sends every math span to `render_math.js` (MathJax 3, TeX input, SVG output, a glyph cache per formula so each
   SVG stands alone). A TeX error stops the build and prints the failing snippet.
4. Replaces each local `<img src>` with base64 data and, for PNG and JPEG, a width of `calc(<mm> * var(--mm))`.
   A remote image stops the build: download it next to the source first.
5. Adds print CSS: A4, margins 15/14/16 mm, body 9.8 pt, figures and boxes kept unsplit, wide equations scaled
   to the column, light colors forced.
6. Refuses to write a page that still has `<script>`, `<link>`, `@import`, an `<iframe>`, an image not inlined,
   or a `src`, `href` or `url()` that loads from another host. Ordinary links (`<a href="https://...">`) are
   allowed because nothing is fetched when the page opens.
7. Writes `<Name>.html`, `<Name>_print.html` (every `<details>` open), optionally `<Name>_artifact.html` (title,
   style and content only, for a host that adds its own skeleton) and, with `--pdf`, `<Name>.pdf`.

The PDF command. The first four flags are the ones used in the original project; `--disable-gpu` and the
throwaway profile were added for this skill so the print never shares a profile with an open browser window
(Suggested, not yet tested in real work):

```bash
"<chrome>" --headless=new --no-pdf-header-footer --virtual-time-budget=15000 --disable-gpu \
  --user-data-dir=<tmp> --print-to-pdf=<Name>.pdf file:///.../<Name>_print.html
```

## 4. The round loop

The loop that was run about 22 times on one report:

1. Back up the source before editing: `cp report.html report_v07_pre_<change>.html`.
2. Edit with exact replacements. In a script: a list of (old, new) pairs, assert each old occurs exactly once,
   replace, write.
3. Render each changed figure and look at it; tile several into a contact sheet.
4. Build, then check:
   ```bash
   python3 build_report.py code/report.html --out-dir report --name <Name> --pdf --mathjax-dir ~/.cache/report-mathjax
   python3 check_report.py report/<Name>.html --banned <skill>/assets/banned_words.txt --list-bare \
       --pdf report/<Name>.pdf --previews code/pages_r07
   ```
5. Read the contact sheet, then the changed pages at full size. A fresh preview folder each round keeps stale
   pages out of review.
6. Grep for phrases and numbers left from earlier versions (`grep -n "<old phrase>\|<old number>" code/report.html`)
   and for references to figures that moved.
7. Copy to the report folder; send the PDF with the HTML beside it; give the path.
8. Append the round's facts to the project notes; write down any new standing preference the reader stated.

## 5. Replies as posted

When an internal report records a rebuttal or a reply to co-authors, it holds the replies exactly as they were
posted, as one appendix section generated from the paste-ready files. A hand copy drifts the moment a reply is
edited again. In the source work, a small script turned the posted answers into a section of the
internal report on every build.

```bash
python3 <skill>/scripts/posted_section.py "General response=replies/general.md" "Reviewer R1=replies/R1.md" \
    --insert code/report.html
```

- The inputs are the files that were pasted, in the order the section shows them (for example the `<key>.md` files
  that the sibling skill `rebuttal` writes with its `preview_replies.py`).
- `--insert` rewrites only what lies between `<!-- posted-replies:start -->` and `<!-- posted-replies:end -->`,
  which the HTML template holds just above the last appendix block, "Code and data". Re-run it before every build.
- Each reply sits in a `<blockquote>` inside a collapsed `<details id="posted">`, so the checker's banned-word scan
  skips text that must stay as posted, and the print version opens it.
- `--format tex` writes a `\section` for a LaTeX report, between `% posted-replies:start` and
  `% posted-replies:end`; bullets and table rows become paragraphs so a docx converter can still read it.
- `--self-test` runs the built-in checks.

## 6. Checker options

| Option | Does |
|---|---|
| `--banned FILE` | whole-word check of visible text against a list (repeatable). Add the project's internal labels to a copy of `assets/banned_words.txt`. |
| `--max-main-words N` | fail when the main text is longer than N words |
| `--max-main-figures N` | warn above N main figures (default 10) |
| `--list-bare` | print main-text sentences without a digit |
| `--pdf FILE --previews DIR` | page count, one PNG per page at 110 dpi and `contact.png` |

## 7. Traps met on the way

- A substring banned-word check flagged "assigned" for "signed" and an appendix title holding "published". The
  checker matches whole words in visible text only.
- MathJax from a CDN worked on the author's screen and showed raw TeX to a reader offline. Pre-render.
- A report with a `figs/` folder lost every image when mailed. Inline.
- Institute mail filters block `.html` attachments. Send the PDF; the HTML goes beside it or by link.
- In zsh, `$B:s` inside a path is read as a substitution modifier, `$P` holding "python3 -X" is not split into
  words, and `echo =====` fails. Use `${B}`, a plain interpreter path, and quoted separators.
- In pandas, `d.mode` is the method `DataFrame.mode`, not a column called `mode`; the same holds for `count`,
  `size`, `rank` and `sum`. One analysis script read the method in place of the column. Index columns by name
  (`d['mode']`) in every analysis script.
- An agent applying edits one second after another agent wrote a draft: write drafts to a temporary name and
  rename when final, and make the edit applier skip pairs already applied.
