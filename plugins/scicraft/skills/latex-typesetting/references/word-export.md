# A Word copy for co-authors, built from the LaTeX source

Read this when co-authors read and comment in Word or a shared online document while the paper,
reply or report is written in LaTeX.

## 1. What they get

**One Word file, built from the same source in the same session as the PDF.** In the original
project a reply document went to co-authors as a Word file for a shared online document. The
author asked to "put the figure or screenshot of the latex-made table in the docs for my
collegues to see it right there. also with text from figure." What held:

| Part of the document | In the Word file |
|---|---|
| text, headings, lists | Word text in the template's styles; references, citations and section numbers as the PDF prints them |
| display equations | LaTeX-rendered PNG at print size, the TeX source as alt text, the equation number beside it |
| inline math | italic letters with sub- and superscripts |
| tables and figures | the rendered float without its caption (table tints, rank fills and merged cells exactly as printed), the caption as text beneath, so it takes comments |
| bibliography | the `.bbl` entries as text |
| page size, margins, styles | the co-authors' reference document (`--template`) |

Equations as images with their TeX as alt text is the form the co-authors' own Word manuscript
already used; a later round kept that file's equations byte for byte.

## 2. The commands

```bash
python3 scripts/build_latex.py main.tex                                # PDF first: .aux and .bbl give the numbers
python3 scripts/render_floats.py main.tex --check-pdf build/main.pdf   # every float as an image + manifest.json
python3 scripts/latex_to_docx.py main.tex --template reference.docx -o main.docx
```

Put the three lines in the project's build script, so the Word copy can never lag behind the PDF.

`latex_to_docx.py` reports every equation that did not compile (its TeX is then kept as
typewriter text), every float without a render and every float macro call without a rendered float, and exits 1
when there is one. Macro definitions from the preamble are passed to the equation renderer; a
macro that needs a package the renderer lacks shows up in that report.

## 3. Rules around it

- **This builds a new file. An existing co-authored Word file is never rebuilt.** A python-docx
  rebuild and a pandoc round trip of a co-authored manuscript gave blue headings, visible
  "LaTeX: ..." captions and a bookmark per heading, and the author was furious. Edit such a file
  in place at the XML level, and keep its equations as they are, byte for byte.
- **Fixes to a Word file the author edits personally go into one Markdown checklist**, each item
  quoting the current wording so it can be found by search (`safe-editing.md`).
- **Ask the author to open the file once in Word.** The Word copy was checked only through macOS
  Quick Look, which ignores column widths and rotation, so every hand-over said "please open it
  once in Word".
- Scan the Word text for retired names and internal terms the same way as the PDF text: extract
  it (`python3 -c "import docx; ..."` or `textutil -convert txt` on macOS) and grep it.
- Before hand-over, check that no caption appears twice and that no style token (a color name
  such as `warn`, a macro name) leaked into the text.

## 4. What the builder does not handle

Tested on the three profiles of `assets/` and a probe document (`--self-test`); the output was
checked by its text and a Quick Look preview, not in Word itself.

- Custom environments become a bold title plus their body; custom macros with arguments print
  their arguments as words. Look at the Word text once for leftovers.
- `\housefigure`-style float macros are placed when the macro is defined in the preamble with a
  `figure` or `table` inside and its label is in the manifest.
- Tables are images. A co-author who must edit a table's numbers edits the record that generates
  it (`make_table.py`), never the Word file.
- Footnotes become a parenthesis in the text. Inline drawings and other boxes in the text are not
  converted; check the Word text where the PDF has them.
