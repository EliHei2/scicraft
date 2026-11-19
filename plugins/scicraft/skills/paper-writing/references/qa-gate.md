# The prose QA gate

`scripts/prose_qa.py` is a Python port of a book gate that was a bash script of grep checks. Run it
before calling any unit done. It reads `.tex` and `.md` (change with `--ext`), drops whole-line `%`
comments and fenced code, and exits 1 on any blocking hit.

```bash
python3 scripts/prose_qa.py --self-test                     # once per machine and after every edit to the gate
python3 scripts/prose_qa.py sections/ --draft               # while drafting: markers are warnings
python3 scripts/prose_qa.py sections/ --facts GUARDRAILS.md --terms TERMS.txt \
        --frozen FROZEN.txt --budget 9000 --wpp 463 --exclude acknowledgements.tex
```

## What it checks

| Check | Blocking | Source of the rule |
|---|---|---|
| em dash, spaced en dash, `---` | yes | the loudest machine tell; unspaced en dash in ranges and compounds (`cell--cell`, `12--18`) is allowed |
| `not X but Y`, `X, not Y`, `not just/only/merely` | yes | state Y directly; a real contrast gets a second short sentence |
| filler openers (`Importantly`, `Crucially`, `Notably`, `Note that`, `It is worth noting`, `Interestingly`, `In essence`) | yes | delete |
| `in order to` | yes | "to" |
| self-praise (`principled`, `elegant`, `powerful`, `seamless`, `robustly`, `carefully designed`, `state-of-the-art`) | yes | describe what it does |
| slogan sentences ("is the point.", "is exactly right.") | yes | state the fact |
| hedge stacks ("may potentially") | yes | one hedge, attached to the number |
| unquantified speed ("orders of magnitude faster") | yes | give the measured ratio |
| sentences about the document, forward pointers | yes | delete, or a pointer that carries the finding |
| inline semicolon, mid-sentence colon | yes, unless `--allow-colons` | a colon that ends a line before a display, table or list is not matched; math lines, URLs and times are exempt |
| Markdown in a `.tex` file (a bold pair, a `#` heading, a code span) | yes | pasted from a chat or a brief, it builds without error and prints literally; LaTeX quotes are not matched |
| meta openers ("This distinction", "This is why", "This matters") | warning | |
| sales words (`novel`, `comprehensive`, `leverage`, `a wide range of`, "strong result") | warning | allowed only as a technical term |
| evaluative rank words (`strongest`, `wins`, `falls behind`, `dominates`) | warning | measured relations: "ranks below", "the highest-ranked" |
| three or more keys in one citation | warning | one fundamental source per claim |
| heading: colon, question mark, question-word opener, invented count ("Three symptoms"), fourth level | yes (fourth level a warning with `--allow-deep-headings`) | `references/headings-and-terms.md` |
| `NEEDS_CITATION`, `[AUTHOR ACTION`, `[CONFLICT]`, `[DECISION NEEDED]`, `TODO`, `FIXME`, `\tbd` | yes, warning with `--draft` | must be empty before submission |
| retired values and names (`--facts`) | yes | bullets under any heading containing "Retired"; the first code span of a bullet is the literal searched; in `GUARDRAILS.md`, mark retired guardrail rules inline (`RETIRED <date>`), never under such a heading, or the gate bans their text |
| banned terms (`--terms`) | yes | one per line, `term => replacement`, whole word, case-insensitive; with `--terms-only` and `--ext .py,.js,.html` it scans figure scripts and site copy without the prose checks |
| frozen sentences (`--frozen`) | yes | sentences the author fixed verbatim, compared on collapsed whitespace, so rewrapping passes and rewording fails |
| word budget (`--budget`, `--wpp`) | yes when over | prose words, LaTeX commands and inline math removed; page estimate ceil(w/wpp) + 1.5 per chapter opener + 0.7 per figure |

**Colons and semicolons are an author decision.** The author's measured published corpus uses
semicolons at 80.7 and colons at 38.9 per 10,000 words, yet the same author banned both mid-sentence
in later work and named them as machine patterns. The latest rule (no inline semicolon and no
mid-sentence colon in new or edited prose) is the default; one or two per chapter that carry the
sentence may stay ("1-2 that really make sense you can keep"), each named in the report with its
reason. A colon before a display, table or list stays. The owner of this rule is the sibling skill
`humanizer` (`humanizer/references/register-technical.md`, T16). A voice sample, a venue or a
co-author's style overrides: a lab adopting this gate decides per author and passes `--allow-colons`
if that author's own published text uses them. Old text the author wrote may keep them.

**`rather than`** is not checked. In the author's papers and long documents, `X rather than Y` with the
positive half first and a real rejected option Y is allowed, with no cap per section
(`recorded rather than imputed`); the author's own papers use it often. Cut it when Y was never a
candidate, or when two sit back to back. In rebuttal replies it stays banned (sibling skill
`rebuttal`). The owner of this rule is the sibling skill `humanizer`.

The question-word, invented-count and sales-word checks, and `--terms-only`, were added in the port
from rules the source project enforced by reading; they are suggested, not yet tested in real work.

## What it cannot check

Read for these yourself, in the paragraph audit:

- a heading that is a metaphor or a riddle without a colon or question;
- a subject that does not exist (T2), a sentence with no fact (T1), a chain with a gap (T7);
- tricolons built for rhythm, and slogan sentences outside the listed phrases;
- a number with no comparator;
- a claim stronger than its status tag;
- words from a neighboring field used for a different object.

## A gate is code and rots like code

Plant the defect after every change to the gate and confirm it fails. `--self-test` does this for
every built-in check, and also confirms a clean paragraph passes. The bash original failed silently
four times, each discovered only after real violations shipped:

1. `rg` was absent in the non-interactive shell; `rg ... 2>/dev/null || true` reported ok while 301
   mid-sentence colons and 179 semicolons sat in the chapters.
2. BSD grep read `[^\]};[]})]*` as a different set; the check showed 14 hits and hid 170.
3. A renamed figure macro disarmed the missing-figure check, and the frozen-sentence gate pointed at
   a moved file and sat below `exit`, so it never ran.
4. A PCRE lookahead `(?! )` that BSD ERE rejects made the retired-names check print ok forever.

Rules for extending it: every check names a path that exists; every failure reaches the exit code;
add a planted example to `PLANTS` in the script for every new check and rerun `--self-test`; when
you add a figure macro or rename a file a check depends on, change the check in the same commit.

## Before calling a LaTeX unit done

The gate reads source. A build can still print "(?)" for a missing key with a successful exit, "??"
for a dangling reference, skip a missing figure under nonstopmode, or drop the rest of a line on an
undefined macro. Build with `build_latex.py` from the sibling `latex-typesetting` skill (out of
tree, passes until no "Rerun", fails if it never settles), or loop pdflatex until the log has no
"Rerun to get"; then read the log. A clean build with a fixed three passes once left 64 of 76
contents, figure-list and table-list page numbers wrong.

```bash
pdflatex -interaction=nonstopmode -file-line-error main.tex >/dev/null; bibtex main >/dev/null
for i in 2 3 4 5; do
  pdflatex -interaction=nonstopmode -file-line-error main.tex >/dev/null
  grep -q "Rerun to get" main.log || break
done
grep -q "Rerun to get" main.log && echo "FAIL: references did not settle in 5 passes"
grep -E 'Error|Undefined|Missing' main.log | sort -u
grep -o "Citation \`[^']*' on page" main.log | sort -u
grep -o "Reference \`[^']*' on page" main.log | sort -u
pdftotext main.pdf - | grep -nE '\?\?|\(\?\)|NEEDS_CITATION'
```

Done means: no errors, no undefined citations or references, the gate clean, and the report says
which failures are new and which pre-existed. A figure can carry a retired name in its own PDF text
layer under a white box: `pdftotext figure.pdf - | grep -i '<retired name>'` for every placed
figure. Typesetting rules and shims are `latex-typesetting`'s job.

## Two-reader review

When there is time before hand-over, two fresh readers attack the draft, each with one lens, and
neither edits.

- **Reader A, a journal editor**, hunts sentences whose only content is that something matters,
  slogans, triads and decorative figures.
- **Reader B, the referee**, hunts unsourced claims, unlicensed figures and numbers absent from the
  facts file.

Output: a table of defects (number, where, defect, reader, fix), then every conflict between A and B
with a written ruling and its reason. A ruling may split: "A on the principle, B on the action".
Then answer the brief's checks with counts: words against budget, keys that exist, keys that print
a false attribution. Stage drafts in separate files with merge instructions keyed to anchor text as
well as line numbers, and touch no manuscript file. One writer applies the rulings afterwards.

When the brief asks for a verdict per unit (a section, a chapter, a figure), the referee gives each
unit one: reject or needs work, with the measured quantities it audited and how many it would
delete, then a table of Cut and Why (what comes out, and the reason). The verdict is a reading and
changes no file; the writer applies it afterwards.
