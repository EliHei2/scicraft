#!/usr/bin/env python3
"""The numbers behind the page's figures, as one JSON file the page draws from. Never deployed.

    python3 pipeline/build_results.py

Copy this to build_results.py and fill the three marked places. The shape matters more than the code:
  1. read the paper's records (through the paper's own figure code where that is possible);
  2. keep only what the page draws;
  3. check that every number and every quoted sentence in public/index.html is the records' and the paper's;
  4. check the author's rules, so a thing they threw out cannot come back.
If the paper moves to a new revision, change PAPER, run this, and fix what the checks report.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
PAPER = SITE.parent / 'paper/tex'                       # <-- the TeX of the revision of record
RECORDS = SITE.parent / 'paper/records'                 # <-- the files the paper's figures and tables are made from
PAGE = SITE / 'public/index.html'
OUT = SITE / 'public/data/results.json'

OURS, RIVAL = 'Ours', 'Method B'                        # <-- the paper's method and the strongest comparator, as the records name them

# What each task is, in the paper's own words (shown when a task name is pointed at), with the passage of the paper
# each line is checked against and the score the paper's table of tasks gives for it.
TASK_ABOUT = {
    # 'task one': ('One sentence on what the task is.', 'the passage of the TeX that says so', 'the score'),
}

# The author's rules. Each entry is (what must not be in the page's visible text, why). Grow it with every round.
FORBIDDEN = [
    (r'·|•', 'no dot or bullet between phrases'),
    (r'\bconfidence interval|\berror bars?\b|95%', 'one statistics language: no intervals in words'),
    (r'@(?:inproceedings|article|misc)\{', 'no citation block before the paper can be cited'),
]
MAX_P = 0.01                                            # no p value above this is printed in front; None to switch off


def plain(tex: str) -> str:
    """The paper's text without revision marks, emphasis commands and braces, on one line."""
    return ' '.join(re.sub(r'\\(?:newer|new|rev|textbf|textit|emph)\{|[{}]', '', tex).split())


def check_page(out: dict) -> int:
    page = PAGE.read_text().replace('&nbsp;', ' ')
    paper = plain(' '.join(p.read_text() for p in sorted(PAPER.glob('*.tex'))))
    text = re.sub(r'<[^>]+>', '', page)

    # numbers and sentences the page prints, built from the records where they are numbers
    want = [
        # f"{by[OURS]['mean']:.2f} versus {by[RIVAL]['mean']:.2f}",
        # 'the sentence under the main figure, as pasted',
    ]
    missing = [w for w in want if w not in page]
    assert not missing, f'on the page but not as the records have it: {missing}'

    # every sentence pasted from the paper is still in the paper
    for sentence in (
        # 'a sentence of the paper that the page quotes',
    ):
        assert sentence in paper, f'no longer in the paper: {sentence}'
    for about, passage, _ in TASK_ABOUT.values():
        assert passage in paper, f'no longer in the paper: {passage}'

    # the author's rules
    for pattern, why in FORBIDDEN:
        hit = re.search(pattern, text)
        assert not hit, f'{why}: "{hit.group(0)}"'
    if MAX_P is not None:
        weak = [m.group(0) for m in re.finditer(r'p\s*(?:=|≤|≥)\s*(\.\d+|\d\.\d+)', text) if float(m.group(1)) > MAX_P]
        assert not weak, f'p values above {MAX_P} on the page: {weak}'
    assert not re.search(r'\[[^\]\n]{3,60}\]', text), 'a bracketed placeholder is still on the page'
    return len(want)


def main():
    # 1. read the records ---------------------------------------------------------------------------------------
    # records = json.loads((RECORDS / 'benchmark.json').read_text())
    out = {'ours': OURS, 'rival': RIVAL, 'tasks': [], 'bars': {}, 'heat': {}, 'ablate': {}, 'table': {}}

    # 2. only what the page draws, with six decimals (rounding twice can differ from the paper in the last place) --
    out['tasks'] = [{'name': n, 'about': a, 'metric': m} for n, (a, _, m) in TASK_ABOUT.items()]

    # 3. and 4. --------------------------------------------------------------------------------------------------
    checked = check_page(out)
    for key in ():                                      # keys that were needed for the checks but that no chart reads
        del out[key]
    OUT.write_text(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
    print(f'{OUT.name}: {OUT.stat().st_size / 1e3:.1f} kB; {checked} page statements checked against the records and the paper')


if __name__ == '__main__':
    main()
