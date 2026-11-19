#!/usr/bin/env python3
"""Windowed medians of a training log: the trailing window beside the window before it.

Per-step training metrics are noisy enough that the last logged row says almost nothing. In the run this
was ported from, an effective-rank metric swung by a factor of two between adjacent logged steps, and two
false collapse alarms came from reading the last row. This script prints, for each metric, the median
over the trailing WINDOW steps next to the median over the WINDOW steps before it, the change, the spread
(IQR) of the trailing window, and the last row only for contrast. Never reintroduce a last-row reading.

Input: one or more JSONL logs (one JSON object per line) or CSV logs with a header. Rows are keyed by the
step column; when a resumed run replays steps, the LAST occurrence of a step wins. Use --where to select
one kind of row (for example training rows without an "event" field, or rows with event=val).

Dependencies: Python 3.9 or later, standard library only.

Exit codes: 0 when every requested key was found with enough points; 1 when a requested key is absent
or a window holds fewer than --min-points values; 2 when a file cannot be read or holds no usable rows.

Examples:
  python3 windowed_medians.py runs/a/train.jsonl --where event=none --keys loss pred_loss effrank
  python3 windowed_medians.py runs/a/train.jsonl --where event=val --keys val_loss --best-min val_loss
  python3 windowed_medians.py runs/a/train.jsonl runs/b/train.jsonl --window 1000 --json out.json
  python3 windowed_medians.py --selftest
"""
import argparse
import csv
import json
import math
import os
import random
import statistics
import sys
import tempfile


def parse_where(items):
    """--where KEY=VALUE pairs. VALUE 'none' matches a key that is absent or null."""
    out = []
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"--where expects KEY=VALUE, got {it!r}")
        k, v = it.split("=", 1)
        out.append((k, v))
    return out


def row_matches(row, where):
    for k, v in where:
        val = row.get(k)
        if v.lower() == "none":
            if val not in (None, ""):
                return False
        elif str(val) != v:
            return False
    return True


def to_float(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x) if math.isfinite(float(x)) else None
    if isinstance(x, str):
        try:
            f = float(x)
        except ValueError:
            return None
        return f if math.isfinite(f) else None
    return None


def load_rows(path, step_key, where):
    """Return rows sorted by step, one per step (the last occurrence wins, as after a resume)."""
    by_step = {}
    n_bad = 0
    if path.endswith(".csv"):
        with open(path, newline="") as fh:
            rows = list(csv.DictReader(fh))
    else:
        rows = []
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    n_bad += 1
                    continue
                if isinstance(d, dict):
                    rows.append(d)
    for d in rows:
        if not row_matches(d, where):
            continue
        s = to_float(d.get(step_key))
        if s is None:
            continue
        by_step[s] = d
    return [by_step[s] for s in sorted(by_step)], n_bad


def numeric_keys(rows, step_key):
    keys = set()
    for r in rows:
        for k, v in r.items():
            if k != step_key and to_float(v) is not None:
                keys.add(k)
    return sorted(keys)


def window_values(rows, key, step_key, lo, hi):
    vals = []
    for r in rows:
        s = to_float(r.get(step_key))
        v = to_float(r.get(key))
        if s is not None and v is not None and lo <= s < hi:
            vals.append(v)
    return vals


def iqr(vals):
    if len(vals) < 4:
        return float("nan")
    q = statistics.quantiles(vals, n=4)
    return q[2] - q[0]


def summarize(rows, keys, step_key, window, best_min, best_max):
    hi = to_float(rows[-1].get(step_key))
    out = {"last_step": hi, "window": window, "metrics": {}}
    for key in keys:
        cur = window_values(rows, key, step_key, hi - window, hi + 1)
        prev = window_values(rows, key, step_key, hi - 2 * window, hi - window)
        allv = [(to_float(r.get(step_key)), to_float(r.get(key))) for r in rows]
        allv = [(s, v) for s, v in allv if v is not None]
        rec = {"present": bool(allv), "n_trailing": len(cur), "n_previous": len(prev)}
        if allv:
            m_cur = statistics.median(cur) if cur else float("nan")
            m_prev = statistics.median(prev) if prev else float("nan")
            spread = iqr(cur)
            rec.update({
                "median_trailing": m_cur,
                "median_previous": m_prev,
                "change": m_cur - m_prev,
                "iqr_trailing": spread,
                "change_over_iqr": (m_cur - m_prev) / spread if spread and math.isfinite(spread) else float("nan"),
                "last_row": allv[-1][1],
            })
            if key in best_min or key in best_max:
                pick = min if key in best_min else max
                s_best, v_best = pick(allv, key=lambda t: t[1])
                rec.update({"best_ever": v_best, "best_step": s_best, "gap_to_best": allv[-1][1] - v_best})
        out["metrics"][key] = rec
    return out


def fmt(x, w=10):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return f"{'nan':>{w}}"
    return f"{x:>{w}.4g}"


def print_report(path, summ, min_points):
    problems = []
    print(f"{path}")
    print(f"  last step {summ['last_step']:g}; medians over the trailing {summ['window']:g} steps, "
          f"previous {summ['window']:g} in the second column")
    print(f"  {'metric':<22}{'trailing':>10}{'previous':>10}{'change':>10}{'IQR':>10}"
          f"{'chg/IQR':>10}{'n':>6}   last row (do not read)")
    for key, r in summ["metrics"].items():
        if not r["present"]:
            print(f"  {key:<22}{'absent':>10}")
            problems.append(f"{key}: absent from the log")
            continue
        print(f"  {key:<22}{fmt(r['median_trailing'])}{fmt(r['median_previous'])}{fmt(r['change'])}"
              f"{fmt(r['iqr_trailing'])}{fmt(r['change_over_iqr'])}{r['n_trailing']:>6}   "
              f"{fmt(r['last_row']).strip()}")
        if "best_ever" in r:
            print(f"  {'':<22}best ever {r['best_ever']:.4g} at step {r['best_step']:g}, "
                  f"current minus best {r['gap_to_best']:+.4g}")
        for which in ("n_trailing", "n_previous"):
            if r[which] < min_points:
                problems.append(f"{key}: {which.replace('n_', '')} window holds {r[which]} values "
                                f"(< {min_points}); widen --window or log more often")
    return problems


def selftest():
    """Build a noisy synthetic log whose median is flat while the last rows dip, and check the report."""
    rng = random.Random(0)
    tmp = tempfile.mkdtemp(prefix="wm_selftest_")
    path = os.path.join(tmp, "train.jsonl")
    with open(path, "w") as fh:
        for step in range(0, 6000, 10):
            loss = 2.0 + rng.gauss(0, 0.4)
            rank = 160 + rng.gauss(0, 30)
            if step >= 5970:                       # three spurious low rows at the end
                rank = 90.0
            fh.write(json.dumps({"step": step, "loss": loss, "effrank": rank}) + "\n")
            if step % 500 == 0:
                fh.write(json.dumps({"step": step, "event": "val", "val_loss": 2.5 - step / 1e4}) + "\n")
        # a resume that replays steps 5000-5090: the later rows must win
        for step in range(5000, 5100, 10):
            fh.write(json.dumps({"step": step, "loss": 2.0, "effrank": 160.0}) + "\n")
    rows, _ = load_rows(path, "step", parse_where(["event=none"]))
    assert len(rows) == 600, len(rows)
    s = summarize(rows, ["loss", "effrank"], "step", 2000, set(), set())
    er = s["metrics"]["effrank"]
    assert er["last_row"] == 90.0
    assert abs(er["change"]) < 10, er                   # medians flat despite the last-row dip
    assert er["n_trailing"] == 201 and er["n_previous"] == 200
    vrows, _ = load_rows(path, "step", parse_where(["event=val"]))
    v = summarize(vrows, ["val_loss"], "step", 2000, {"val_loss"}, set())["metrics"]["val_loss"]
    assert v["best_step"] == 5500 and v["n_trailing"] == 5
    print(f"selftest passed: effrank last row {er['last_row']:.0f}, trailing median "
          f"{er['median_trailing']:.1f} vs previous {er['median_previous']:.1f}; resume replay deduplicated; "
          f"val rows selected by --where ({tmp})")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    ap.add_argument("logs", nargs="*", help="JSONL or CSV training logs")
    ap.add_argument("--keys", nargs="+", help="metrics to report (default: every numeric column)")
    ap.add_argument("--step-key", default="step", help="column holding the step (default: step)")
    ap.add_argument("--window", type=float, default=2000, help="window length in steps (default: 2000)")
    ap.add_argument("--where", action="append", metavar="KEY=VALUE",
                    help="keep rows where KEY equals VALUE; VALUE 'none' keeps rows where KEY is absent")
    ap.add_argument("--min-points", type=int, default=20,
                    help="fail when a window holds fewer logged values than this (default: 20)")
    ap.add_argument("--best-min", nargs="+", default=[], help="keys for which lower is better: print best ever (meant for evaluation rows; a noisy training metric's best row is noise)")
    ap.add_argument("--best-max", nargs="+", default=[], help="keys for which higher is better: print best ever (evaluation rows)")
    ap.add_argument("--json", help="also write the summary to this JSON file")
    ap.add_argument("--selftest", action="store_true", help="run on a synthetic log and exit")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.logs:
        ap.error("give at least one log file, or --selftest")
    where = parse_where(a.where)
    problems, dump = [], {}
    for path in a.logs:
        try:
            rows, n_bad = load_rows(path, a.step_key, where)
        except OSError as e:
            print(f"cannot read {path}: {e}", file=sys.stderr)
            return 2
        if not rows:
            print(f"{path}: no rows with a numeric '{a.step_key}' match the --where filter", file=sys.stderr)
            return 2
        if n_bad:
            print(f"{path}: skipped {n_bad} lines that are not JSON")
        keys = a.keys or numeric_keys(rows, a.step_key)
        summ = summarize(rows, keys, a.step_key, a.window, set(a.best_min), set(a.best_max))
        problems += [f"{path}: {p}" for p in print_report(path, summ, a.min_points)]
        dump[path] = summ
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dump, fh, indent=2)
        print(f"wrote {a.json}")
    print(f"checked {len(a.logs)} log(s): rows keyed by '{a.step_key}', last occurrence of a step kept, "
          f"window {a.window:g} steps, at least {a.min_points} values per window")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"  {p}")
        return 1
    print("no problems")
    return 0


if __name__ == "__main__":
    sys.exit(main())
