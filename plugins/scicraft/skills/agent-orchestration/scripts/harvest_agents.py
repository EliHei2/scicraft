#!/usr/bin/env python3
"""List what finished and dead background agents left on disk, so partial work can be harvested.

Read-only. Point it at one Claude Code session folder (the folder named after the session id, beside the
session's .jsonl transcript). It reports:

  session    the death point of the main transcript: tool calls that never got a result, the last
             record, trailing queue operations (the app died) and usage-limit messages (a limit hit)
  workflows  per workflow run: agents started, returned, failed and dead (started minus returned),
             retries that share a journal key, whether the run state file exists, and whether every
             path named in the run's result exists (the orphan audit)
  agents     per agent transcript (workflow agents and standalone background agents): its label, whether
             it was marked finished, its last record time, a tool call left hanging, and every file it
             wrote or edited, with size and modification time, or MISSING
  tasks      background task outputs (*.output) with their times; an output newer than the transcript's
             last record was delivered after the session ended

The layout it reads (Claude Code internals as of late 2026; check them again if the harness changed):

  <projects>/<slug>/<session>.jsonl                          main transcript
  <projects>/<slug>/<session>/workflows/wf_*.json            run state, written only when a run finishes
  <projects>/<slug>/<session>/subagents/workflows/wf_*/journal.jsonl   started / result / failed records
  <projects>/<slug>/<session>/subagents/workflows/wf_*/agent-*.jsonl   workflow agent transcripts
  <projects>/<slug>/<session>/subagents/agent-*.jsonl (+ .meta.json)   standalone agents
  <tmp>/claude-<uid>/<slug>/<session>/tasks/*.output         background task outputs (lost on reboot)

Usage:
  harvest_agents.py SESSION_DIR
  harvest_agents.py SESSION_DIR --tasks TMP_SESSION_DIR/tasks
  harvest_agents.py SESSION_DIR --json > harvest.json

Exit code 0 when the folder was read, 2 when it does not exist. Standard library only, Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
from collections import OrderedDict

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
LIMIT_RE = re.compile(r"hit your (?:session|weekly|usage|monthly) limit|reached your usage limit", re.I)
ABS_PATH_RE = re.compile(r"(/(?:[\w.@+-]+/)+[\w.@+-]+\.[A-Za-z0-9]{1,8})")
REL_PATH_RE = re.compile(r"^(?:\./)?(?:[\w.@+-]+/)+[\w.@+-]+\.[A-Za-z0-9]{1,8}$")


def read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def blocks(rec):
    m = rec.get("message")
    if not isinstance(m, dict):
        return []
    c = m.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def first_user_line(recs):
    for r in recs:
        if r.get("type") != "user":
            continue
        for b in blocks(r):
            if b.get("type") == "text" and b.get("text", "").strip():
                return b["text"].strip().splitlines()[0][:120]
    return ""


def last_ts(recs):
    ts = [r.get("timestamp") for r in recs if r.get("timestamp")]
    return ts[-1] if ts else None


def parse_ts(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def file_info(path):
    try:
        st = os.stat(path)
        return {"path": path, "exists": True, "bytes": st.st_size,
                "mtime": dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    except OSError:
        return {"path": path, "exists": False}


def dangling(recs):
    """Tool calls with no matching result, in order."""
    used, done = OrderedDict(), set()
    for r in recs:
        for b in blocks(r):
            if b.get("type") == "tool_use" and b.get("id"):
                used[b["id"]] = b.get("name", "?")
            elif b.get("type") == "tool_result" and b.get("tool_use_id"):
                done.add(b["tool_use_id"])
    return [(i, n) for i, n in used.items() if i not in done]


def result_paths(obj):
    """Paths a run's result names: absolute paths anywhere in it, and string values that look like a
    relative path to a file (checked against the current folder)."""
    found = set(ABS_PATH_RE.findall(json.dumps(obj, ensure_ascii=False)))
    stack = [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
        elif isinstance(o, str) and REL_PATH_RE.match(o):
            found.add(o)
    return found


def agent_summary(path, label=None):
    recs = read_jsonl(path)
    meta_path = path[:-len(".jsonl")] + ".meta.json"
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            meta = {}
    written = OrderedDict()
    n_tools = 0
    for r in recs:
        for b in blocks(r):
            if b.get("type") != "tool_use":
                continue
            n_tools += 1
            inp = b.get("input") or {}
            if b.get("name") in WRITE_TOOLS:
                p = inp.get("file_path") or inp.get("notebook_path")
                if p:
                    written[p] = written.get(p, 0) + 1
    hang = dangling(recs)
    return {
        "agent_id": os.path.basename(path)[len("agent-"):-len(".jsonl")],
        "label": label or meta.get("description") or first_user_line(recs),
        "finished": meta.get("finished") is True,
        "model": meta.get("model", ""),
        "records": len(recs),
        "tool_calls": n_tools,
        "last_record": last_ts(recs),
        "hanging_tool": hang[-1][1] if hang else None,
        "files": [dict(file_info(p), writes=n) for p, n in written.items()],
    }


def workflow_summary(wf_dir, session_dir, transcript_recs):
    wf = os.path.basename(wf_dir)
    journal = read_jsonl(os.path.join(wf_dir, "journal.jsonl"))
    started, returned, failed, keys = OrderedDict(), set(), set(), {}
    for r in journal:
        t, aid = r.get("type"), r.get("agentId")
        if t == "started" and aid:
            started[aid] = {"label": r.get("label", ""), "phase": r.get("phase", ""), "key": r.get("key", "")}
            keys.setdefault(r.get("key", aid), []).append(aid)
        elif t == "result" and aid:
            returned.add(aid)
        elif t == "failed" and aid:
            failed.add(aid)
    state_path = os.path.join(session_dir, "workflows", wf + ".json")
    state = None
    if os.path.exists(state_path):
        try:
            with open(state_path, encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, ValueError):
            state = None
    named = []
    limit_logs = 0
    if isinstance(state, dict):
        named = [file_info(p) for p in sorted(result_paths(state.get("result")))]
        limit_logs = sum(1 for l in (state.get("logs") or []) if LIMIT_RE.search(str(l)))
    script_in_transcript = 0
    if state is None:
        # A run killed mid-way leaves no state file and no script; the script survives in the transcript.
        for r in transcript_recs:
            for b in blocks(r):
                if b.get("type") == "tool_use" and b.get("name") == "Workflow":
                    s = (b.get("input") or {}).get("script") or ""
                    script_in_transcript = max(script_in_transcript, len(s))
    agents = []
    seen = set()
    for aid, info in started.items():
        p = os.path.join(wf_dir, "agent-%s.jsonl" % aid)
        a = agent_summary(p, label=info["label"]) if os.path.exists(p) else {
            "agent_id": aid, "label": info["label"], "files": [], "records": 0}
        a["status"] = "returned" if aid in returned else "failed" if aid in failed else "dead"
        a["phase"] = info["phase"]
        agents.append(a)
        seen.add(aid)
    for p in sorted(glob.glob(os.path.join(wf_dir, "agent-*.jsonl"))):
        aid = os.path.basename(p)[len("agent-"):-len(".jsonl")]
        if aid not in seen:
            a = agent_summary(p)
            a["status"] = "not in journal"
            agents.append(a)
    return {
        "workflow": wf,
        "state_file": state_path if state is not None else None,
        "status": state.get("status") if isinstance(state, dict) else None,
        "limit_log_lines": limit_logs,
        "script_chars_in_transcript": script_in_transcript,
        "started": len(started),
        "returned": len(started.keys() & returned),
        "failed": len(started.keys() & failed),
        "dead": [a["agent_id"] for a in agents if a.get("status") == "dead"],
        "retries": {k: v for k, v in keys.items() if len(v) > 1},
        "result_paths": named,
        "agents": agents,
    }


def session_summary(transcript):
    recs = read_jsonl(transcript)
    main = [r for r in recs if not r.get("isSidechain")]
    hang = dangling(main)
    tail_q = 0
    for r in reversed(main):
        if r.get("type") == "queue-operation":
            tail_q += 1
        else:
            break
    limit_hits = 0
    for r in main:
        for b in blocks(r):
            txt = b.get("text") if b.get("type") == "text" else b.get("content")
            if isinstance(txt, str) and LIMIT_RE.search(txt):
                limit_hits += 1
    msgs = [r for r in main if r.get("type") in ("user", "assistant")]
    last = msgs[-1] if msgs else {}
    if hang:
        verdict = "died inside a tool call (%s)" % hang[-1][1]
    elif tail_q:
        verdict = "app died between turns (no hanging call, trailing queue operations)"
    else:
        verdict = "no hanging call; ended between turns"
    return {
        "transcript": transcript,
        "records": len(recs),
        "last_record": last.get("timestamp") or last_ts(main),
        "last_type": last.get("type"),
        "hanging_tool_calls": [n for _, n in hang],
        "trailing_queue_operations": tail_q,
        "limit_messages": limit_hits,
        "verdict": verdict + ("; usage-limit text present" if limit_hits else ""),
    }


def tasks_summary(tasks_dir, after):
    out = []
    for p in sorted(glob.glob(os.path.join(tasks_dir, "*.output"))):
        info = file_info(p)
        st = os.stat(p).st_mtime
        info["after_session_end"] = bool(after and st > after)
        out.append(info)
    return out


def print_report(rep):
    s = rep.get("session")
    if s:
        print("SESSION  %s" % s["transcript"])
        print("  last record %s (%s); %s" % (s["last_record"], s["last_type"], s["verdict"]))
    for w in rep["workflows"]:
        print("\nWORKFLOW %s  state file: %s%s" % (
            w["workflow"], "present (status %s)" % w["status"] if w["state_file"] else "ABSENT",
            "; script recoverable from transcript (%d chars)" % w["script_chars_in_transcript"]
            if w["script_chars_in_transcript"] else ""))
        print("  agents started %d, returned %d, failed %d, dead %d; limit lines in logs %d" % (
            w["started"], w["returned"], w["failed"], len(w["dead"]), w["limit_log_lines"]))
        for k, ids in w["retries"].items():
            print("  retry: %d attempts share one key (%s); read them oldest first" % (len(ids), ", ".join(ids)))
        for p in w["result_paths"]:
            print("  result names %s: %s" % (p["path"], "exists" if p["exists"] else "MISSING (orphan)"))
        for a in w["agents"]:
            print_agent(a, prefix="  ")
    if rep["standalone"]:
        print("\nSTANDALONE AGENTS")
        for a in rep["standalone"]:
            print_agent(a, prefix="  ")
    if rep.get("tasks") is not None:
        print("\nTASK OUTPUTS (%d)" % len(rep["tasks"]))
        for t in rep["tasks"]:
            print("  %s  %s bytes  %s%s" % (os.path.basename(t["path"]), t.get("bytes"), t.get("mtime"),
                                           "  AFTER SESSION END" if t["after_session_end"] else ""))
    n_files = sum(len(a["files"]) for w in rep["workflows"] for a in w["agents"]) + \
        sum(len(a["files"]) for a in rep["standalone"])
    n_dead = sum(len(w["dead"]) for w in rep["workflows"]) + \
        sum(1 for a in rep["standalone"] if not a.get("finished"))
    print("\nchecked %d workflow(s), %d standalone agent(s); %d written file(s) listed; "
          "%d agent(s) dead or not marked finished" % (len(rep["workflows"]), len(rep["standalone"]), n_files, n_dead))


def print_agent(a, prefix=""):
    status = a.get("status") or ("finished" if a.get("finished") else "NOT MARKED FINISHED")
    hang = "; hanging %s" % a["hanging_tool"] if a.get("hanging_tool") else ""
    print("%s[%s] %s  %s  last %s%s" % (prefix, status, a["agent_id"], a.get("label", "")[:70],
                                       a.get("last_record"), hang))
    for f in a["files"]:
        if f["exists"]:
            print("%s    wrote %s  %d bytes  %s" % (prefix, f["path"], f["bytes"], f["mtime"]))
        else:
            print("%s    wrote %s  MISSING" % (prefix, f["path"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    ap.add_argument("session_dir", help="the session folder (named after the session id)")
    ap.add_argument("--transcript", help="the session .jsonl (default: SESSION_DIR.jsonl beside the folder)")
    ap.add_argument("--tasks", help="folder of background task outputs (*.output), usually in the temp tree")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    a = ap.parse_args()

    sd = os.path.abspath(a.session_dir.rstrip("/"))
    if not os.path.isdir(sd):
        print("not a folder: %s" % sd, file=sys.stderr)
        return 2
    transcript = a.transcript or sd + ".jsonl"
    trecs = read_jsonl(transcript) if os.path.exists(transcript) else []
    rep = {"session": session_summary(transcript) if trecs else None, "workflows": [], "standalone": []}
    for wf_dir in sorted(glob.glob(os.path.join(sd, "subagents", "workflows", "wf_*"))):
        if os.path.isdir(wf_dir):
            rep["workflows"].append(workflow_summary(wf_dir, sd, trecs))
    for p in sorted(glob.glob(os.path.join(sd, "subagents", "agent-*.jsonl"))):
        rep["standalone"].append(agent_summary(p))
    if a.tasks:
        end = parse_ts(rep["session"]["last_record"]) if rep["session"] else None
        rep["tasks"] = tasks_summary(a.tasks, end) if os.path.isdir(a.tasks) else []
    if a.json:
        json.dump(rep, sys.stdout, indent=1)
        print()
    else:
        print_report(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
