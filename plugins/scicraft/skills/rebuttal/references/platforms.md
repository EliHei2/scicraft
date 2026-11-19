# Platform limits and posting

Everything here was observed on one OpenReview conference in late 2026, unless marked otherwise. Platforms change
their limits and renderers between venues and years. **Verify each item on the venue's current pages** (the author
guide, the reviewer guide, the comment form itself) and record the verified value, the address and the date in
`RULES_AND_FACTS.md`. When an official guide address returns an error, find the current one; one guide path was a
404.

## Length

- **5,000 characters per comment**, one comment per reviewer. Final lengths were 4,900 to 4,990 characters per
  reply and 1,900 to 2,700 for the general response; margins of 9 to 15 characters held.
- Count as the platform does: the text as pasted, lines joined with newlines, outer blank lines removed.
  `check_replies.py` does this, resolves line-number tokens first (an unresolved token counts as nine characters),
  and with `--bytes` counts UTF-8 bytes. If the platform may count bytes, give the cuts to make in that case.
- A link of about 60 characters counts; count with and without it.
- **Write complete first, then cut.** The author's order: "don't prune under 5000 yet, make it clear and complete",
  then cut to the limit. Cut your own additions before the author's text, prose before quotes or tables, words
  before numbers. Never cut the qualifier that keeps a comparison fair: one trim dropped "zero-shot" on a comparator
  and it had to go back.
- No "part 1/2" splits. If a reply cannot fit, cut content.

## Markdown and math

- Markdown rendered as CommonMark with tables (the platform used the marked library with GitHub tables). Raw HTML
  and images show as literal text, so a figure can only be a link or a page of the PDF.
- A single line break is ignored. Put a blank line between "Best regards," and "The authors".
- Math through MathJax: inline `$...$`, display `$$...$$`. Inside the Markdown, a backslash that MathJax needs may
  have to be doubled; test one formula in the preview. After one round the author moved to "no TeX at all" except a
  single displayed equation where necessary.
- Color only through MathJax: `$\color{red}{\textsf{short phrase}}$`. The box does not wrap, so color a short
  phrase only (`check_replies.py` lists every colored phrase with its length). Check after posting that
  `darkgreen` renders; fall back to `green`.

## Fields and readers

| Field | What worked |
|---|---|
| title of the general response | "General response to all reviewers: main changes and new results" |
| title of a reply | "Response to Reviewer X" |
| title of a note to the chair | a fact in the reviewer's own words, with no adjective of ours ("unfair" and "inconsistent reviewer" were struck) |
| readers of replies | everyone |
| readers of the note to the chair | Area Chairs and Program Chairs only |
| abstract field | plain text; `*` and `**` only, `*` for the one coined term |

## Posting

- **Order:** the public reply to the reviewer the note concerns, then the private note to the chair within minutes,
  then any other reply. Check the posting order against the live state of the form.
- Before posting: ratings as shown on the platform, the capitalization of reviewer IDs, dates. These cannot be
  checked locally.
- A sentence that promises a later action ("we will repeat this sentence in the caption ... before the end of the
  discussion period") commits the author to upload a revised PDF in time. Flag it when written: upload it, or
  remove the sentence.

## The revised PDF

Observed requirements for one venue's revision: at most 10 main-text pages, under 50 MB, a required statement on the
use of language models. The revised PDF is the only thing reviewers are asked to read besides the replies ("It is
up to you to clearly communicate what's been changed"; "We highly encourage brevity"), so replies point into it.

## Previews and paste-ready files

- `preview_replies.py` draws each block as a card (title, readers, character count, a copy button) with the
  reviewer's message folded above the reply to it. One clean page with the follow-up hidden behind a click, the
  reply and the note was what the author asked for; a 24 KB preview builder with extra panels was not.
- To look at it without a browser window: `"<Chrome>" --headless=new --disable-gpu --screenshot=shot.png
  --window-size=1000,2400 file://<out>/preview.html`, then read the image.
- Give co-authors a Word file holding the Markdown source as plain text (`--docx`): "people will edit that and
  we're gonna submit that directly". A Word file that renders the Markdown copies its typesetting into their Docs.
- For co-authors who review in a shared document, the tables and figures each answer relies on can be embedded as
  images beside the answer, with display equations as images and the TeX beneath. That document is internal; the
  posted text has no figures. The builder for it belongs to the sibling `latex-typesetting` skill (its Word export
  and float renderer). Check the file before sending: no caption printed twice, no style token leaked into the text
  (a color class name), the same number of co-author comments out as came in (5 in, 5 out in the source work), and
  one highlight color per kind of change with the legend at the top (new words, refreshed line numbers, next round).
- **Render and look at the output of every converter** (Markdown to Word, TeX to Markdown) at about 70 dpi before
  sending it. One converter escaped its own bullet macro, and the literal command showed in the co-authors' file.

## Base rates of score changes

OpenReview's public search needs no login (`curl -sL "https://api2.openreview.net/notes/search?term=<phrase>"`).
Reviewer comments that announce a raised score can be collected, joined to their papers, and counted by whether a
reviewer first kept a score and then raised it. Query generic phrases only, never the paper's title or number. Run
it only when the author asks, and never on the day a reply is due: in the source work it took 20 minutes just
before a deadline, and its only visible product was a borrowed format the author rejected.

## Journals

The journal campaign behind `references/journal-revision.md` submitted four things: the tracked-changes manuscript,
a clean manuscript, the response letter and a cover letter. Page and line numbers in the letter refer to the
tracked-changes version, and the letter says so. There is no character limit; the letter quoted every comment in
full. Co-authors received Word exports of the Markdown sources. Which editorial system takes which file type, and
whether line numbers must refer to the marked or the clean copy, is set by each journal's instructions: verify them
for the venue at hand and record them in `RULES_AND_FACTS.md`.
