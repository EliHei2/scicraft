#!/usr/bin/env python3
"""Count dashes and stock frames per 10,000 words of prose, before and after a humanizer pass.

Usage:
    python3 frame_density.py FILE [FILE ...] [--threshold 15] [--max-dashes 0] [--sample SAMPLE.tex]
                             [--reference REF1.txt [REF2.txt ...]] [--whitelist FACTS.md refs.bib ...]
                             [--max-sentence-words 45] [--format auto|tex|md|txt|html] [--show 20]
                             [--json OUT.json]
    python3 frame_density.py --self-test

What it counts, on prose only (TeX comments, math, cite/ref/label commands, Markdown code and link targets are
removed first; see textprep.py):

  dashes        em dashes, spaced en dashes, TeX '---' and ' -- ' used as punctuation. Unspaced en dashes in
                ranges and compounds (12--18, cell--cell, 12-18) are not counted.
  frames        the stock connective frames of the technical register: 'rather than', 'instead of',
                'so that', 'namely', 'which is why', 'not only', 'in the sense that', 'because ... whereas'
                in one sentence. Each is reported per 10,000 words.
  contrast      staged contrast: 'not X but Y' within one sentence, 'not just/only/merely/simply', ', not'.
  filler        filler openers ('It is worth noting', 'Importantly,', 'Notably,', 'In order to', ...).
  vocabulary    essay-register and stock AI words, hunted by name.
  furniture     spatial verbs used for data ('sits', 'lives in', 'holds', 'carries').
  semicolon, colon   mid-sentence semicolons and colons (counted, never failed: a house rule, see the skill).
  long sentences     sentences over --max-sentence-words words (default 45), listed for splitting, never failed.
  back to back       two 'rather than' in one sentence or in consecutive sentences, listed for cutting.

--sample gives earlier prose by the same writer in the same register. 'rather than' is then limited at the
sample's rate per 10,000 words instead of --threshold, because a writer may use it as a signature form (one
author's published corpus: 24.1 per 10,000 words). The sample's share of sentences over the length limit is
printed beside the text's, so a writer whose specification sentences run long is not split by rule.

Why: a de-punctuation pass welds clauses back together with these frames, and a rewrite that is read line by
line misses rates. One measured manuscript had 69 'namely', 25 'rather than' and 15 'so that' before its pass.
The threshold of about 15 per 10,000 words for any one frame and the zero-dash rule come from that work.

--reference takes one or more files of real writing in the same register (exemplar papers or books, the
author's own published text), one text per file. Three lists come out:
  over-used       three or more times the pooled reference rate, with at least 5 uses;
  under-used      in at least --min-docs reference files (default 6, or all of them when fewer are given),
                  over 40 per million words pooled, and used here at under a quarter of that rate, because
                  de-slop passes have over-banned real connectives before;
  out of lexicon  in no reference file and in no --whitelist file (the facts file and the bibliography, so
                  domain terms pass), at least 4 letters long: imported register, listed for reading.
Run it before and after a pass: if a word's count is unchanged, the pass did not reach it.

Exit status: 1 when dashes exceed --max-dashes or any single frame exceeds --threshold per 10,000 words
and occurs at least --min-count times (default 3; the floor is suggested, not yet tested in real work, and
keeps one use in a 300-word text from failing); 0 otherwise. Contrast, filler and vocabulary hits are listed with line numbers for a person to judge.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textprep import detect_format, prose_lines, words  # noqa: E402

DASH = re.compile(r"—|(?<!-)---(?!-)|\s--\s|\s–\s|\w–\s|\s–\w")
FRAMES = {
    "rather than": r"\brather than\b",
    "instead of": r"\binstead of\b",
    "so that": r"\bso that\b",
    "namely": r"\bnamely\b",
    "which is why": r"\bwhich is why\b",
    "not only": r"\bnot only\b",
    "in the sense that": r"\bin the sense that\b",
    "because ... whereas": r"\bbecause\b[^.;]{0,200}\bwhereas\b",
}
CONTRAST = {
    "not X but Y": r"\bnot\b[^.!?]{0,120}\bbut\b",
    "not just/only/merely": r"\bnot (?:just|only|merely|simply)\b",
    ", not": r",\s*not\b(?! only| just| merely| simply)",
}
FILLER = r"(?:^|[.!?]\s+)(it is worth noting|it's worth noting|importantly|crucially|notably|interestingly|" \
         r"note that|in essence|in summary|in conclusion|moreover|furthermore|additionally)\b|\bin order to\b|" \
         r"\bthis (?:section|chapter|paper|file|document) (?:describes|covers|presents|explains|gives)\b|\bbelow,? we\b"
VOCAB = [
    "load-bearing", "the decisive", "the sharpest form of", "stress test", "pure noise", "headline",
    "the wrong instrument", "is exactly the adjustment", "gains nothing", "essentially every", "the one place",
    "at the heart of", "underscores?", "speaks to", "robust(?:ly)?", "comprehensive", "principled", "elegant",
    "powerful", "seamless(?:ly)?", "novel", "carefully (?:designed|chosen|constructed)", "rich", "crucial",
    "pivotal", "delve[sd]?", "showcas(?:e|es|ed|ing)", "tapestry", "testament", "landscape", "intricate",
    "meticulous(?:ly)?", "leverag(?:e|es|ed|ing)", "unlock(?:s|ed|ing)?", "cutting-edge", "paradigm",
    "state-of-the-art", "symptoms?", "rungs?", "honest(?:ly)?", "currency", "measured rather than asserted",
    "on purpose", "by design", "is stated as one", "auditable",
]
FURNITURE = r"\b(sits?|sitting|sat|lives? in|living in|holds|carries|carry)\b"
SEMI = r"(?<!\\);[\]})]*[ \t]+[a-z]"
COLON = r":[\]})]*[ \t]+[a-z]"


SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\\$(\"'])")
TOKEN = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def tokens(text):
    """Lower-case words, with TeX command names (\\subsection, \\textbf) removed first."""
    return [w.lower() for w in TOKEN.findall(re.sub(r"\\[A-Za-z@]+\*?", " ", text))]


def prose_of(path: Path, fmt: str = "auto") -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return "\n".join(t for _, t in prose_lines(raw, detect_format(path, fmt)))


def sentence_spans(prose: str):
    """Yield (start offset, sentence text) for the prose, splitting at . ! ? before a capital."""
    start = 0
    for m in SENT_END.finditer(prose):
        yield start, prose[start:m.start()]
        start = m.end()
    if prose[start:].strip():
        yield start, prose[start:]


def n_words(sentence: str) -> int:
    return len(sentence.split())


def analyse(path: Path, fmt: str, max_words: int = 45):
    raw = path.read_text(encoding="utf-8", errors="replace")
    fmt = detect_format(path, fmt)
    lines = list(prose_lines(raw, fmt))
    prose = "\n".join(t for _, t in lines)
    n_words_total = max(1, words(prose))
    hits = {}

    def collect(cat, name, rx, flags=re.I, per_sentence=False):
        out = []
        if per_sentence:
            for m in re.finditer(rx, prose, flags):
                ln = prose.count("\n", 0, m.start())
                out.append((lines[ln][0], m.group(0)))
        else:
            for ln, t in lines:
                for m in re.finditer(rx, t, flags):
                    out.append((ln, m.group(0).strip()))
        hits.setdefault(cat, {})[name] = out

    collect("dashes", "dash", DASH, 0)
    for k, rx in FRAMES.items():
        collect("frames", k, rx, per_sentence=(k == "because ... whereas"))
    for k, rx in CONTRAST.items():
        collect("contrast", k, rx, per_sentence=(k == "not X but Y"))
    collect("filler", "filler", FILLER)
    for v in VOCAB:
        collect("vocabulary", re.sub(r"\(\?:([^)]*)\)\??", r"[\1]", v), r"\b%s\b" % v)
    collect("furniture", "spatial verbs", FURNITURE)
    collect("punctuation", "semicolon", SEMI, 0)
    collect("punctuation", "colon", COLON, 0)

    sents = [(prose.count("\n", 0, off), s) for off, s in sentence_spans(prose)]
    long_s, rt_idx = [], []
    for i, (ln, s) in enumerate(sents):
        k = n_words(s)
        if k > max_words:
            long_s.append((lines[ln][0], f"{k} words"))
        c = len(re.findall(r"\brather than\b", s, re.I))
        rt_idx.extend([i] * c)
    b2b = []
    for a, b in zip(rt_idx, rt_idx[1:]):
        if b - a <= 1:
            b2b.append((lines[sents[b][0]][0], "rather than"))
    hits["sentences"] = {"over %d words" % max_words: long_s}
    hits["back to back"] = {"rather than": b2b}
    return {"file": str(path), "format": fmt, "words": n_words_total, "hits": hits,
            "n_sentences": max(1, len(sents)), "tokens": Counter(tokens(prose))}


def per10k(n, total):
    return 10000.0 * n / max(1, total)


def load_reference(paths, fmt):
    """Pooled counts and document frequency over the reference files (one text per file)."""
    pooled, docfreq = Counter(), Counter()
    for p in paths:
        toks = tokens(prose_of(p, fmt if fmt != "auto" else "auto"))
        pooled.update(toks)
        docfreq.update(set(toks))
    return pooled, docfreq


def lexicon_lists(toks, ref, docfreq, n_docs, whitelist, min_docs):
    tot = max(1, sum(toks.values()))
    ref_total = max(1, sum(ref.values()))
    over, under, oov = [], [], []
    for w, c in toks.items():
        rr = ref.get(w, 0) / ref_total
        if c >= 5 and rr > 0 and (c / tot) / rr >= 3:
            over.append((w, c, round(1e6 * c / tot), round(1e6 * rr)))
        if docfreq.get(w, 0) == 0 and w not in whitelist and len(w) > 3:
            oov.append((w, c))
    need = min(min_docs, n_docs)
    for w, c in ref.items():
        rr = 1e6 * c / ref_total
        here = 1e6 * toks.get(w, 0) / tot
        if docfreq[w] >= need and rr > 40 and here < rr / 4 and len(w) > 3:
            under.append((w, round(rr), toks.get(w, 0)))
    over.sort(key=lambda x: -x[1])
    under.sort(key=lambda x: -x[1])
    oov.sort(key=lambda x: (-x[1], x[0]))
    return over, under, oov


def self_test():
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="frame_density_test_"))
    long_s = " ".join(["word"] * 50)
    (d / "draft.txt").write_text(
        "We tune the rate rather than the batch. We fix the seed rather than average it. "
        f"{long_s.capitalize()} ends here. The zorbleflux model runs. " + "However the gradient clips. " * 8 + "\n")
    (d / "sample.txt").write_text("We report medians rather than means. " * 3 + "Plain text follows here. " * 20)
    refs = []
    for k in range(6):
        f = d / f"ref{k}.txt"
        f.write_text("However the model trains. The gradient clips. We tune the rate and fix the seed. " * 5 +
                     "Long sentences run here. " * k)
        refs.append(f)
    (d / "facts.md").write_text("Nothing about it.\n")
    r = analyse(d / "draft.txt", "auto")
    assert len(r["hits"]["back to back"]["rather than"]) == 1, r["hits"]["back to back"]
    assert len(r["hits"]["sentences"]["over 45 words"]) == 1, r["hits"]["sentences"]
    ref, docfreq = load_reference(refs, "auto")
    toks = r["tokens"]
    over, under, oov = lexicon_lists(toks, ref, docfreq, len(refs), set(), 6)
    assert "zorbleflux" in [w for w, _ in oov], oov
    over, under, oov = lexicon_lists(toks, ref, docfreq, len(refs), {"zorbleflux"}, 6)
    assert "zorbleflux" not in [w for w, _ in oov], oov
    assert "trains" in [w for w, _, _ in under], under
    assert "however" not in [w for w, _, _ in under], under
    s = analyse(d / "sample.txt", "auto")
    srate = per10k(len(s["hits"]["frames"]["rather than"]), s["words"])
    assert srate > 15, srate
    print("self-test passed: back-to-back 'rather than', a sentence over 45 words, out-of-lexicon with and "
          "without a whitelist, under-use by document frequency, sample rate for 'rather than'")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Count dashes and stock frames per 10,000 words of prose.")
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--threshold", type=float, default=15.0,
                    help="fail when any one frame exceeds this rate per 10,000 words (default 15)")
    ap.add_argument("--max-dashes", type=int, default=0,
                    help="fail when more dashes than this are used as punctuation (default 0; raise it to the "
                         "rate of a voice sample that uses dashes)")
    ap.add_argument("--min-count", type=int, default=3,
                    help="a frame fails only when it also occurs at least this often (default 3), so one use in "
                         "a short text does not fail it")
    ap.add_argument("--sample", type=Path,
                    help="earlier prose by the same writer in the same register; 'rather than' is then limited "
                         "at the sample's rate, and the sample's share of long sentences is printed")
    ap.add_argument("--reference", type=Path, nargs="+",
                    help="one or more files of real writing in the same register, one text per file")
    ap.add_argument("--whitelist", type=Path, nargs="+", default=[],
                    help="files whose words are domain terms (facts file, bibliography): never out of lexicon")
    ap.add_argument("--min-docs", type=int, default=6,
                    help="under-use needs the word in at least this many reference files (default 6, capped at "
                         "the number given)")
    ap.add_argument("--max-sentence-words", type=int, default=45,
                    help="list sentences longer than this many words (default 45)")
    ap.add_argument("--format", default="auto", choices=["auto", "tex", "md", "txt", "html"])
    ap.add_argument("--show", type=int, default=20, help="locations to print per pattern (default 20)")
    ap.add_argument("--json", type=Path, help="also write the counts to this file")
    ap.add_argument("--self-test", action="store_true", help="run the built-in checks on synthetic text and exit")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.files:
        ap.error("give at least one FILE (or --self-test)")

    ref = docfreq = None
    if a.reference:
        ref, docfreq = load_reference(a.reference, a.format)
    whitelist = set()
    for w in a.whitelist:
        whitelist |= set(tokens(w.read_text(encoding="utf-8", errors="replace")))

    rt_limit, sample_long = None, None
    if a.sample:
        s = analyse(a.sample, a.format, a.max_sentence_words)
        rt_limit = per10k(len(s["hits"]["frames"]["rather than"]), s["words"])
        sample_long = 100.0 * len(s["hits"]["sentences"]["over %d words" % a.max_sentence_words]) / s["n_sentences"]
        print(f"== sample {a.sample}: 'rather than' {rt_limit:.1f} per 10,000 words (the limit for that frame); "
              f"{sample_long:.0f} percent of sentences over {a.max_sentence_words} words")

    failed, report = False, []
    for f in a.files:
        r = analyse(f, a.format, a.max_sentence_words)
        n = r["words"]
        print(f"== {f}  ({r['format']}, {n} words of prose)")
        dashes = len(r["hits"]["dashes"]["dash"])
        status = "FAIL" if dashes > a.max_dashes else "ok"
        failed |= dashes > a.max_dashes
        print(f"  dashes as punctuation: {dashes} (allowed {a.max_dashes})  {status}")
        for ln, s in r["hits"]["dashes"]["dash"][:a.show]:
            print(f"    line {ln}: {s!r}")
        print(f"  frames per 10,000 words (threshold {a.threshold:g}):")
        for k, hs in r["hits"]["frames"].items():
            rate = per10k(len(hs), n)
            by_sample = k == "rather than" and rt_limit is not None
            limit = rt_limit if by_sample else a.threshold
            over = rate > limit and len(hs) >= a.min_count
            failed |= over
            flag = "  FAIL" if over else ""
            note = f"  (sample limit {limit:.1f})" if by_sample else ""
            print(f"    {k:<22} {len(hs):>4}  {rate:6.1f}{note}{flag}")
        for cat in ("contrast", "filler", "vocabulary", "furniture", "punctuation", "back to back", "sentences"):
            total = sum(len(v) for v in r["hits"][cat].values())
            print(f"  {cat}: {total} ({per10k(total, n):.1f} per 10,000 words)")
            for k, hs in r["hits"][cat].items():
                if hs and cat != "punctuation":
                    locs = ", ".join(str(ln) for ln, _ in hs[:a.show])
                    print(f"    {k}: {len(hs)} at line {locs}")
                elif hs:
                    print(f"    {k}: {len(hs)}")
        long_share = 100.0 * len(r["hits"]["sentences"]["over %d words" % a.max_sentence_words]) / r["n_sentences"]
        line = f"  share of sentences over {a.max_sentence_words} words: {long_share:.0f} percent"
        if sample_long is not None:
            line += f" (sample {sample_long:.0f} percent)"
        print(line)
        lex = None
        if ref is not None:
            over, under, oov = lexicon_lists(r["tokens"], ref, docfreq, len(a.reference), whitelist, a.min_docs)
            lex = {"over_used": over, "under_used": under, "out_of_lexicon": oov}
            print("  over-used against the reference (word, count, per million here, per million in reference):")
            for o in over[:a.show]:
                print(f"    {o[0]}: {o[1]}, {o[2]} vs {o[3]}")
            print(f"  under-used (in at least {min(a.min_docs, len(a.reference))} reference files, over 40 per "
                  "million, under a quarter of that here; check that a pass did not over-ban them):")
            print("    " + ", ".join(f"{w} ({rr}/M, {c} here)" for w, rr, c in under[:a.show]))
            print("  out of lexicon (in no reference file and no whitelist file; read each as possible "
                  "imported register):")
            print("    " + ", ".join(f"{w} ({c})" for w, c in oov[:a.show]))
        entry = {"file": r["file"], "words": n,
                 "counts": {cat: {k: len(v) for k, v in d.items()} for cat, d in r["hits"].items()}}
        if lex is not None:
            entry["lexicon"] = lex
        report.append(entry)
    if a.json:
        a.json.write_text(json.dumps(report, indent=2))
    print("\nresult:", "FAIL (dashes or a frame over its limit)" if failed else "pass (limits held; read the listed hits)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
