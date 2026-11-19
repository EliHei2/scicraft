#!/usr/bin/env python3
"""Write a tiny synthetic Claude Code home (prompt history plus two session transcripts) for tests.

Usage: python3 make_fixture.py OUT_DIR

Creates OUT_DIR/claude_home/{history.jsonl, paste-cache/, projects/<encoded project>/<session>.jsonl}.
The content is invented: an ML researcher tuning a tabular classifier and writing a figure. Two fake
credentials are planted (built at run time, so this file itself holds none) to test redaction.
Standard library only.
"""
import argparse
import json
from pathlib import Path

# Built from pieces so that no scanner flags this file. They are not real credentials.
FAKE_KEY = "sk-" + "proj-" + "A1b2C3d4" * 5
FAKE_HF = "hf" + "_" + "Zz9Yy8Xx7Ww6Vv5Uu4Tt3Ss2Rr1Qq0Pp"
PROJECT = "/work/demo-lab/tabular-baselines"
ENC = PROJECT.replace("/", "-")


def ms(day, hh, mm):
    import datetime as dt
    return int(dt.datetime(2026, 3, day, hh, mm, tzinfo=dt.timezone.utc).timestamp() * 1000)


def iso(day, hh, mm):
    return f"2026-03-{day:02d}T{hh:02d}:{mm:02d}:00.000Z"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out")
    a = ap.parse_args()
    home = Path(a.out) / "claude_home"
    (home / "paste-cache").mkdir(parents=True, exist_ok=True)
    proj_dir = home / "projects" / ENC
    proj_dir.mkdir(parents=True, exist_ok=True)

    (home / "paste-cache" / "abc123.txt").write_text(
        "Traceback (most recent call last):\n  File train.py, line 88\nValueError: shapes (512,) and (256,)\n")
    hist = [
        dict(display="run the five baselines on the 30 tables with the same budget, log wall time", project=PROJECT,
             timestamp=ms(2, 9, 0)),
        dict(display=f"use this key for the eval API: {FAKE_KEY}", project=PROJECT, timestamp=ms(2, 9, 5)),
        dict(display="why does it crash here [Pasted text #1]", project=PROJECT, timestamp=ms(2, 9, 20),
             pastedContents={"1": {"contentHash": "abc123"}}),
        dict(display="/clear", project=PROJECT, timestamp=ms(2, 9, 21)),
        dict(display="no gray text in the figure, and the ablation bars start at zero!!", project=PROJECT,
             timestamp=ms(3, 14, 2)),
        dict(display="never retune the baselines after seeing the test split, write that down", project=PROJECT,
             timestamp=ms(3, 14, 30)),
        dict(display="make the slides for group meeting", project="/work/demo-lab/teaching", timestamp=ms(4, 8, 0)),
    ]
    with open(home / "history.jsonl", "w") as fh:
        for h in hist:
            fh.write(json.dumps(h) + "\n")

    s1 = [
        {"type": "ai-title", "aiTitle": "Baseline sweep and ablation figure"},
        {"type": "user", "uuid": "u1", "timestamp": iso(2, 9, 0),
         "message": {"content": "run the five baselines on the 30 tables with the same budget, log wall time"}},
        {"type": "assistant", "uuid": "a1", "timestamp": iso(2, 9, 1), "message": {"content": [
            {"type": "text", "text": "I will run each baseline with a 10 minute budget per table and log wall time."},
            {"type": "tool_use", "name": "Bash", "input": {"command": "python3 sweep.py --budget 600",
                                                           "description": "Run the baseline sweep"}},
            {"type": "tool_use", "name": "Write", "input": {"file_path": "/work/demo-lab/tabular-baselines/NOTES.md",
                                                            "content": "x" * 300}}]}},
        {"type": "user", "uuid": "u2", "timestamp": iso(2, 9, 5),
         "message": {"content": [{"type": "text", "text": f"use this key for the eval API: {FAKE_KEY}"}]}},
        {"type": "user", "uuid": "u3", "timestamp": iso(2, 9, 6), "message": {"content":
            "<task-notification><summary>Background command finished: sweep.py exit 0</summary></task-notification>"}},
        {"type": "user", "uuid": "u4", "timestamp": iso(2, 9, 7), "isSidechain": True,
         "message": {"content": "subagent internal turn that must not appear"}},
        {"type": "assistant", "uuid": "a2", "timestamp": iso(2, 9, 8), "message": {"content": [
            {"type": "tool_use", "name": "Agent", "input": {"description": "Audit the sweep", "model": "opus",
                                                            "prompt": "Read sweep.py and check every baseline got the same budget."}}]}},
        {"type": "user", "uuid": "u5", "timestamp": iso(2, 9, 30), "message": {"content":
            "<agent-message from=\"auditor\">[Subagent hand-back] The report follows:\n  Two baselines got 300 s, not 600 s.</agent-message>"}},
        {"type": "user", "uuid": "u6", "timestamp": iso(2, 9, 40), "isCompactSummary": True,
         "message": {"content": "Summary: sweep re-run with equal budgets; figure pending; token " + FAKE_HF}},
        {"type": "queue-operation", "operation": "enqueue", "timestamp": iso(2, 9, 41),
         "content": "and keep the old results folder, do not overwrite it"},
        {"type": "file-history-snapshot", "snapshot": {"big": "y" * 1000}},
    ]
    s2 = [
        {"type": "ai-title", "aiTitle": "Ablation figure"},
        {"type": "user", "uuid": "v1", "timestamp": iso(3, 14, 2),
         "message": {"content": "no gray text in the figure, and the ablation bars start at zero!!"}},
        {"type": "assistant", "uuid": "b1", "timestamp": iso(3, 14, 3), "message": {"content": [
            {"type": "text", "text": "Fixed: text is near-black and bars start at zero. Rendered to fig_ablation.png."}]}},
    ]
    for name, recs in (("11111111-aaaa-bbbb-cccc-000000000001", s1), ("22222222-aaaa-bbbb-cccc-000000000002", s2)):
        with open(proj_dir / f"{name}.jsonl", "w") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
    print(f"fixture written under {home}")


if __name__ == "__main__":
    main()
