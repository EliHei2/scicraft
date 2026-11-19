"""The spoken script of the talk as one file, with the running time, from the notes the builder writes (build/notes).

    python3 talk_script.py DECK.pptx NOTES_DIR OUT.md [--limit-min 8] [--title "Talk, Event"]

Each note starts with its time in brackets, '[40 s]', then what is said (the author's sentences); cues for the
speaker stand in [brackets] in a second paragraph; backup slides start with '[Backup]'. The script shows whether the
talk fits its slot: about 140 words a minute is a calm pace for a mixed audience. Each slide's own rate is printed
too, and slides spoken faster than 140 words a minute are listed: a calm total can hide one rushed slide (a final
check once found 95 words in 30 s, about 190 a minute, inside a total of about 130).
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import re
import sys
from pathlib import Path

from pptx import Presentation

args = [a for a in sys.argv[1:] if not a.startswith('--')]
if len(args) < 3:
    sys.exit(__doc__)


def opt(name, default):
    if name in sys.argv:
        v = sys.argv[sys.argv.index(name) + 1]
        args.remove(v) if v in args else None
        return v
    return default


limit, head = float(opt('--limit-min', '0')), opt('--title', 'What to say')
prs = Presentation(args[0])
notes = sorted(Path(args[1]).glob('*.txt'))
out, total, words, fast = [f'# {head}', ''], 0, 0, []
for i, (s, nf) in enumerate(zip(prs.slides, notes), 1):
    txt = nf.read_text()
    title = ''
    for sh in s.shapes:                                # the title: the lines of the title box in its first size
        if sh.name == 'title' and sh.has_text_frame:
            ps = [p for p in sh.text_frame.paragraphs if p.runs]
            title = ' '.join(p.text.strip() for p in ps if p.runs[0].font.size == ps[0].runs[0].font.size)
    m = re.match(r'\[(\d+) s\]\s*', txt)
    if not m:
        out += [f'## Backup, slide {i}: {title}', '', re.sub(r'^\[(Backup|\d+ s)\]\s*', '', txt), '']
        continue
    sec = int(m.group(1))
    total += sec
    spoken, _, aside = txt[m.end():].partition('\n\n')
    nw = len(re.sub(r'\[[^\]]*\]', '', spoken).split())
    words += nw
    wpm = nw / sec * 60 if sec else 0
    if wpm > 140:
        fast.append(f'{i} ({wpm:.0f})')
    out += [f'## Slide {i}: {title}', f'{sec} seconds, running total {total // 60}:{total % 60:02d}, {nw} words, '
            f'{wpm:.0f} a minute', '', spoken, '']
    if aside:
        out += [aside, '']
need = int(round(words / 140 * 60))
line = (f'The slides are timed at {total // 60}:{total % 60:02d} in all. The script has {words} words, which take about '
        f'{need // 60}:{need % 60:02d} at a calm 140 words a minute' + ('.' if need <= total else ': MORE than the slides allow, cut words.'))
if limit:
    line += f' The slot is {limit:g} minutes' + ('.' if total <= limit * 60 else f': {total - limit * 60:.0f} seconds over.')
if fast:
    line += ' Slides faster than 140 words a minute: ' + ', '.join(fast) + '.'
out[2:2] = [line, '']
Path(args[2]).write_text('\n'.join(out))
print(args[2], line)
