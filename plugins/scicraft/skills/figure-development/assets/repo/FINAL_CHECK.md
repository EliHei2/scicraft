# Final check: Figure [N]

Work through this list before the figure is shared with a co-author, a journal or a reviewer.
Copy it into `figures/figure_[N]/` and tick each line; a line that cannot be ticked says why.

1. [ ] Rerun every panel script and the composer from a clean shell. The outputs reproduce
   exactly: `render_all.py` then `compare.py` report zero regressions and no unlisted change.
2. [ ] Remove dead and redundant code. Each panel script stays short, with a comment wherever a
   choice is not obvious (a filter, a threshold, an excluded item).
3. [ ] Read every caption and Methods sentence against the code at the commit that made the
   numbers: filters, floors, caps, subsample sizes, n per arm, error-bar type, settings that
   differ from the default.
4. [ ] Every printed number passes `number_parity.py claims` against the canonical table.
5. [ ] The caption, NARRATIVE.md and TECHNICAL_NOTES.md match the current render (letters,
   terms, color key, data sources).
6. [ ] PNG, PDF and, once a submission set exists, the live-text SVG are regenerated.

Checked on [YYYY-MM-DD] at commit [hash] by [who].

Not checked, and why: [list, or "nothing"].
