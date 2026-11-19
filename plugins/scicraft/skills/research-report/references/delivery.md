# Where the report lives and what goes to co-authors

## 1. The report folder

```
<project>/<topic>_report/
├── report/     <Name>.html, <Name>.pdf
├── figures/    every figure the report uses, PNG and PDF, named as in the source
├── code/       report source, one script per panel, the shared figure config, analysis scripts
├── data/       the tables behind every figure
└── README.md   one table: folder and what it holds; then the rebuild steps
```

- Create it in the project, where the user looks for project files, and confirm it is not inside a git
  repository before creating it (a report folder full of figures should not land in a commit by accident).
- Keep a small sync script that copies the built report, the figures the report actually references, the code
  and the data into this folder after every build, and a copy to wherever the user collects deliverables. Re-run
  it each round.
- Every delivery message names the folder's exact path.
- The README states how to rebuild: run the figure scripts, build with `build_report.py`, print the PDF.

## 2. The delivery message

Short enough to read on a phone, in this order:

1. What is delivered: paths and sizes of the PDF and HTML; whether the HTML opens offline; whether equations are
   rendered or plain text; the private link if one was published, and that only the user can share it.
2. What changed this round, one line each, in the reader's terms.
3. What needs the user's check or decision: every reading you guessed ("I read X as Y"), every number you could not
   verify, every diplomatic risk.
4. What was not done or is still running, with the reason and the time it would take.
5. The main-text word count.

No praise, no list of what is fine, no explanation of the tools.

**A justification asked for "in chat, don't write it in the file yet" stays in chat.** Answer there, including
every follow-up question, and leave the report untouched. End with one line that offers a compressed version for a
named section ("Should I add a three-sentence version to section 2?") and edit the file only after a yes. In the
source work, four follow-ups were answered in chat and the last answer ended with that offer.

## 3. Sharing files with co-authors

The rule: **match the type and count of what the co-authors already use.** It came from one deposit. The request
was "supplementary tables" next to a colleague's example tables. They were read as per-panel plotted values,
and dozens of per-item CSVs went up; the deposit was rebuilt as a handful of reference tables.

Procedure:

1. **Open the existing examples.** List each file with its row count and column headers and one line on what kind
   of thing it is: parameter table, dataset table with identifiers and URLs, feature or gene list, pair list,
   software versions, sweep results.
2. **Inventory what the paper needs**: every supplementary table and source table the manuscript cites. Set the
   target count from the examples ("not more than 10-15 files").
3. **Separate tables from data.** Small reference tables go to one folder from the laptop, checked by checksum.
   Large outputs (predictions, segmentations, checkpoints, references) go to another folder, one combined file per
   dataset plus a manifest, uploaded from the machine that holds them.
4. **Stage through an explicit whitelist script**, never by copying a folder.
5. **Check every value against the paper**: "what we see in paper should be what we see in the csvs". Recompute
   from the tables and compare with the figure.
6. **Check each file is usable alone.** A segmentation output held only row indices, a score and a cell id; it
   shipped together with the input table it indexes.
7. **Dry run before any remote write**: list exactly what will be created or replaced; afterwards compare
   checksums.
8. **Tell the co-authors where each thing is**, in one message, with one sentence per table in the form they use
   ("Supplementary Table 2 lists the reference datasets with their identifiers, provenance, roles and URLs").

Keep heavy per-item data local, ready "if a reviewer asks". No README or prose files inside a table deposit unless
the examples have them.

## 4. Figures and documents co-authors edit

- A figure a co-author will touch goes as PNG and PDF plus an SVG with live text (`figure-development` has the
  conversion), named by its number in the manuscript, with a table of the plotted values beside it.
- A co-authored Word manuscript is edited in place, never regenerated. A rebuild through python-docx and a
  pandoc round trip gave blue headings, visible alt-text captions and a bookmark per heading. Copy the original,
  change only the text runs (`w:t`) inside the zip, keep styles, theme and equation objects byte-identical, and
  write fresh `zipfile.ZipInfo` entries (reusing the reader's entries corrupted the CRCs).
- A question a co-author asks about a caption or a number is answered after checking it against the records, in
  plain words, with the exact sentence to change. When two co-authors disagree about a caption, answer in this
  order: who is right, in the first sentence; the evidence in two or three bullets (which code and which data the
  panel was checked against); any further errors found on the way; a reply of about four sentences ready to paste;
  the corrected text in full. The answer that set this order named the right version first, gave three bullets
  of evidence, listed further small caption errors, and ended with a short reply and the corrected caption.
