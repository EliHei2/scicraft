#!/usr/bin/env python3
"""Build the eval fixtures of paper-website from the skill's own starter and the fictional paper in evals/files/paper.

    python3 evals/make_fixture.py

Writes, for each case, files/paper/ (a copy of the shared paper and records) and, where the case needs a site,
files/kestrel-site/ built from assets/starter:
  notes-on-site        a filled site with three things the author's notes ask to change (a tagline over the name,
                       author names that can break from their marks, a full table with no weight on first place)
  audit-before-deploy  the same site with ten planted defects (listed in DEFECTS below and in the graders)
  paper-to-site        only the paper
Run it again whenever the starter changes (refresh_fixtures.sh does).
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

EV = Path(__file__).resolve().parent
SKILL = EV.parent
STARTER = SKILL / 'assets/starter'
PAPER = EV / 'files/paper'

FILL = {
    '[Name]: [the paper\'s title]': 'Kestrel: a pretrained encoder for multivariate sensor streams',
    '[One sentence from the abstract.]': 'Kestrel turns any multivariate stream into one embedding per time step.',
    '[Name]': 'Kestrel',
    '[The rest of the paper\'s title]': 'A pretrained encoder for multivariate sensor streams',
    '[First Author]': 'Ana Example', '[Second Author]': 'Ben Sample', '[Third Author]': 'Chen Placeholder', '[Last Author]': 'Dora Fictive',
    '[Institute one]': 'Institute of Example Studies', '[Institute two]': 'Sample University',
    '[What the left side shows]': 'Operator labels on one server log stream', '[What the right side shows]': 'Kestrel embeddings of the same stream',
    '[left]': 'operator labels', '[right]': 'Kestrel embeddings', '[reference]': 'operator labels', '[the model\'s output]': 'Kestrel',
    '[One or two sentences on what the first screen shows, with any caveat the paper makes about it.]':
        'One server log stream, with the minutes operators marked as incidents on the left and Kestrel embeddings on the right.',
    '[First statement of the problem.]': 'Every new sensor deployment starts without labels.',
    '[Second statement.]': 'A model trained on one stream breaks when the sampling rate, the channel count or the noise changes.',
    '[Third statement.]': 'Labelled anomalies are rare, so supervised models see a few dozen positives at most.',
    '[The paper\'s main claim, one sentence.]': 'Kestrel turns any multivariate stream into one embedding per time step, so a linear probe can read any downstream label from it.',
    '[what the figures cover]': 'patches, channels, masking',
    '[What this figure shows]': 'Patches, channels and masked prediction',
    '[A method figure goes here: a canvas that plays once in view, rests on a finished frame, and takes its captions from the paper.]':
        'Kestrel cuts each channel into patches of 24 steps and embeds each patch with a shared tokenizer.',
    '[One plain statement about the data, e.g. "Trained on four public&nbsp;benchmarks."]': 'Pretrained on 137 public&nbsp;datasets.',
    '[unit one]': 'datasets', '[unit two]': 'time steps', '[unit three]': 'parameters', '[unit four]': 'domains', '[unit five]': 'layers',
    '[One sentence the author wants said about this version, e.g. that it is the first checkpoint.]':
        'This is the first checkpoint; larger models trained on more domains will&nbsp;follow.',
    '[00 methods on 00&nbsp;tasks]': '5 methods on 5&nbsp;tasks',
    '[The paper\'s sentence that says what was evaluated.]': 'Every method is read with the same linear probe on frozen embeddings, and scored by macro&nbsp;F1.',
    '[1st]': '1st', '[what that number counts, with the comparison in numbers]': 'on 4 of 5 tasks, and 2nd on&nbsp;gait',
    '[top&nbsp;3]': '1125', '[what that number counts]': 'rating, against 1025 for Method&nbsp;B',
    '[The paper\'s claim for this figure. Read aloud only: the two numbers above say it.]': 'Kestrel ranks first on four of the five tasks and second on gait.',
    '[What the chart shows]': 'Rating across tasks',
    '[The chart in one sentence, with its main numbers.]': 'Kestrel 1125, Method B 1025, Method C 1023, Baseline 1000, Method D 981.',
    '[One or two sentences from the paper.]': 'Kestrel is rated above every other method in a two-sided sign test over all task and seed pairs (p&nbsp;=&nbsp;0.002).',
    '[The paper\'s caption.]': 'Across tasks, Kestrel has a rating of 1125 against 1025 for the strongest comparator, Method B, where the baseline is&nbsp;fixed&nbsp;at&nbsp;1000.',
    '[A second finding, as the paper states it.]': 'Kestrel ranks first on four of the five tasks and second on&nbsp;gait.',
    '[The heat map in one sentence.]': 'Rank of each method on each of the five tasks.',
    '[One sentence from the paper.]': 'Every method is read with the same linear probe on frozen embeddings, and scored by macro&nbsp;F1.',
    '[What an entry is, as the paper\'s table caption says.]': 'Macro F1 per task on held-out streams; mean rank over the five&nbsp;tasks.',
    '[Cohorts and what is held out.]': 'Five public benchmarks; held-out streams only.',
    '[How each method is read.]': 'Frozen embeddings.',
    '[The same probe for every method.]': 'The same linear probe for every&nbsp;method.',
    '[The paper\'s one definition of a significant difference.]': 'A two-sided sign test over all task and seed&nbsp;pairs.',
    '[how they were run]': 'two model sizes',
    '[The paper\'s sentence that sums up the ablations.]': 'Removing any part of Kestrel lowers macro F1 on at least one task at one of the two model&nbsp;sizes.',
    '[Each part matters, as the paper states it.]': 'Removing any part lowers macro F1 on at least one&nbsp;task.',
    '[The heat map in one sentence, with every value.]': 'Without pretraining .157 and .145; without the cross-channel attention .056; without the masking curriculum .094.',
    '[The paper\'s sentences, naming rows as the heat map names them.]': 'Without pretraining, F1 falls by up to .157; without the masking curriculum, by up to&nbsp;.094.',
    '[00 samples]': '12 streams',
    '[One sentence about what the tiles are.]': 'Twelve held-out streams, operator labels against Kestrel embeddings.',
    '[One sentence from the paper about what the model takes in and gives back.]': 'Kestrel turns any multivariate stream into one embedding per time&nbsp;step.',
    '[Five lines that show how it will be used.]': 'import kestrel\nmodel = kestrel.load("first-checkpoint")\nz = model.embed(stream)          # one embedding per time step',
    '[what goes in]': 'a multivariate stream, any number of channels', '[what comes out]': 'one embedding per time step',
    '[parameters]': '31.6 M', '[license]': 'to be confirmed',
    '[The paper\'s limitations paragraph, verbatim.]': 'Kestrel saw only public datasets in pretraining, and seven domains do not cover every sensor. Streams sampled faster than 2 kHz were not part of pretraining. The five tasks use linear probes; fine-tuning was not&nbsp;evaluated.',
    '[The paper\'s last sentence.]': 'One pretrained encoder can read many kinds of sensor streams without being trained&nbsp;again.',
}
COUNTS = [('data-count="000">000', 'data-count="137">137'), ('data-count="00.0" data-dec="1" data-unit=" B">00.0 B', 'data-count="2.4" data-dec="1" data-unit=" B">2.4 B'),
          ('data-count="00.0" data-dec="1" data-unit=" M">00.0 M', 'data-count="31.6" data-dec="1" data-unit=" M">31.6 M'),
          ('data-count="00">00</dt><dd>domains', 'data-count="7">7</dt><dd>domains'), ('data-count="00">00</dt><dd>layers', 'data-count="10">10</dt><dd>layers')]

DEPLOY = """# Kestrel site

Builders: none yet (results.json was filled by hand from paper/records; to be replaced by pipeline/build_results.py).
Deploy: not deployed. The author decides when a preview goes up.

## The author's rules
- 2026-10-02: the paper is under review; nothing goes public, and a preview only behind the gate.
- 2026-10-02: no p value above .01 on the page, no confidence intervals, no error bars.
- 2026-10-02: no citation block until the preprint is out; Cite says "coming soon".
- 2026-10-04: no dots or bullets between phrases.
"""


def fill_site(dst: Path):
    shutil.copytree(STARTER, dst)
    (dst / 'pipeline/build_results.template.py').unlink()
    p = dst / 'public/index.html'
    s = p.read_text()
    for k in sorted(FILL, key=len, reverse=True):
        s = s.replace(k, FILL[k])
    for a, b in COUNTS:
        assert a in s, a
        s = s.replace(a, b, 1)
    left = re.findall(r'\[[^\]\n]{2,90}\]', s)
    assert not left, left
    p.write_text(s)
    d = json.loads((dst / 'public/data/results.json').read_text())
    d.pop('note')
    names = {'task one': 'grid load', 'task two': 'server logs', 'task three': 'gait', 'task four': 'traffic', 'task five': 'bearing wear'}
    about = {'grid load': 'Forecast the next hour of load from the previous day, scored as a three-class trend.',
             'server logs': 'Flag the minutes that operators marked as incidents.',
             'gait': 'Label each step phase from a wrist sensor.', 'traffic': 'Detect incidents from loop detector counts.',
             'bearing wear': 'Grade the wear of a bearing from its vibration, in three classes.'}
    d['ours'] = 'Kestrel'
    for t in d['tasks']:
        t['name'] = names[t['name']]
        t['short'] = t['name'].split()[0]
        t['about'], t['metric'] = about[t['name']], 'macro F1'
    txt = json.dumps(d).replace('"Ours"', '"Kestrel"').replace('[the rating]', 'rating')
    for a, b in names.items():
        txt = txt.replace(f'"{a}"', f'"{b}"')
    d = json.loads(txt)
    parts = ['pretraining', 'the cross-channel attention', 'the masking curriculum']
    for r, part in zip(d['ablate']['rows'], parts):
        r['label'], r['text'] = f'without {part}', f'Kestrel trained without {part}.'
    (dst / 'public/data/results.json').write_text(json.dumps(d, indent=1))
    m = json.loads((dst / 'public/data/gallery/manifest.json').read_text())
    m.pop('note')
    m['left'], m['right'] = 'operator labels', 'Kestrel'
    for k, smp in enumerate(m['samples'], 1):
        smp['label'], smp['meta'] = f'stream {k}', f'{4 + k % 3} channels, held out'
    for k, lg in enumerate(m['legend']):
        lg['name'] = ['normal', 'incident', 'maintenance', 'missing'][k]
    (dst / 'public/data/gallery/manifest.json').write_text(json.dumps(m, indent=1))
    (dst / 'DEPLOY.md').write_text(DEPLOY)
    for d_ in ('retired',):
        (dst / d_).mkdir(exist_ok=True)


def sub(path: Path, old: str, new: str):
    s = path.read_text()
    assert old in s, (path.name, old[:60])
    path.write_text(s.replace(old, new, 1))


def notes_site(dst: Path):
    """The three things the notes of the notes-on-site case ask to change."""
    fill_site(dst)
    h = dst / 'public/index.html'
    sub(h, '<div class="mast-title">', '<div class="mast-title">\n      <p class="eyebrow">One encoder for every sensor stream</p>')
    s = h.read_text()
    s = re.sub(r'<span class="au">(.*?)</span>', r'\1', s)
    h.write_text(s)


def bad_site(dst: Path):
    """Ten planted defects for the audit-before-deploy case."""
    notes_site(dst)
    h = dst / 'public/index.html'
    sub(h, '<p class="meta">5 methods on 5&nbsp;tasks</p>', '<p class="meta">grid load · server logs · gait · traffic · bearing wear</p>')   # 2 separators
    sub(h, '<dt>1st</dt><dd>on 4 of 5 tasks, and 2nd on&nbsp;gait</dd>', '<dt>1st</dt><dd>on 5 of 5 tasks</dd>')                                # 3 a number the records do not have
    sub(h, '(p&nbsp;=&nbsp;0.002).', '(p&nbsp;=&nbsp;0.002). On traffic alone the difference to Method B is weaker (p&nbsp;=&nbsp;0.04).')      # 4 p above the author's .01
    sub(h, '<p>Across tasks, Kestrel has a rating', '<p>Error bars show the 95% confidence interval. Across tasks, Kestrel has a rating')         # 5 intervals in words
    sub(h, '<details class="fold" id="table">', '<details class="fold" id="table" open>')                                                        # 6 a row open by default
    sub(h, '<li id="cite"><b>Cite</b><span>BibTeX</span><em>coming soon</em></li>\n  </ul>',
        '<li id="cite"><b>Cite</b><span>BibTeX</span><em>below</em></li>\n  </ul>\n  <pre class="code"><code>@article{example2026kestrel,\n  title={Kestrel: a pretrained encoder for multivariate sensor streams},\n  year={2026}\n}</code></pre>')  # 7 citation block
    sub(h, '<footer class="foot">', '<footer class="foot">\n  <p>1 Institute of Example Studies, 2 Sample University</p>')                   # 8 affiliations again in the footer
    d = json.loads((dst / 'public/data/results.json').read_text())
    d['pvalues'] = {'sign_test': 0.002, 'traffic_vs_b': 0.04}                                                                                        # 9 a value no chart draws
    (dst / 'public/data/results.json').write_text(json.dumps(d, indent=1))
    sub(dst / 'public/charts.js', '// ---------------------------------------------------------------------------------------- the full table',
        '// ---------------------------------------------------------------------------------------- the full table\n// values copied from /home/user/kestrel/records/benchmark.csv')  # 10 a local path in a shipped file
    # 1 is the tagline over the name, planted by notes_site


def main():
    cases = {'paper-to-site': None, 'notes-on-site': notes_site, 'audit-before-deploy': bad_site}
    for case, build in cases.items():
        files = EV / case / 'files'
        if files.exists():
            shutil.rmtree(files)
        files.mkdir(parents=True)
        shutil.copytree(PAPER, files / 'paper')
        if build:
            build(files / 'kestrel-site')
        print(f'{case}: {sum(1 for p in files.rglob("*") if p.is_file())} files')


if __name__ == '__main__':
    main()
