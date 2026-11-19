#!/usr/bin/env python3
"""Condense Claude Code session transcripts and prompt history into readable digests.

Raw session files hold base64 images, tool output and request blobs, so a single
session can weigh hundreds of MB. A digest keeps what carries the working pattern:
every prompt the user typed, the assistant's prose replies (capped), and a one-line
trace of each tool call. Output is chunked so one chunk fits one Read call.

Every block passes through redact() before it is written: API keys, tokens, private
keys and credentials in URLs become [REDACTED:<kind>]. The index counts redactions by
kind and never prints a secret. A redacted secret is still a leaked secret: rotate it.

Usage:
    python3 extract_sessions.py --out DIGEST_DIR [--projects-dir ~/.claude/projects]
                                [--history ~/.claude/history.jsonl] [--chunk-kb 60]
                                [--skip-sessions] [--skip-history] [--project-filter TEXT]

Output: DIGEST_DIR/history/history__<project>_NNN.md, DIGEST_DIR/sessions/<project>/
<session8>_NNN.md and DIGEST_DIR/INDEX.md. Exit code 1 when no input was found.
Standard library only, Python 3.9 or later. The transcript format is Claude Code's
internal format as of late 2026; record types it does not know are skipped.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import textwrap
from pathlib import Path

SKIP_PREFIXES = (
    '{"type":"api-request', '{"type": "api-request',
    '{"type":"file-history', '{"type": "file-history',
    '{"type":"mode"', '{"type": "mode"',
    '{"type":"permission-mode"', '{"type": "permission-mode"',
    '{"type":"session-owner"', '{"type": "session-owner"',
    '{"type":"atis-latch"', '{"type": "atis-latch"',
    '{"type":"tools-used"', '{"type": "tools-used"',
    '{"type":"last-prompt"', '{"type": "last-prompt"',
    '{"type":"cost-state"', '{"type": "cost-state"',
)

USER_CAP = 7000        # chars kept per user message
SUBAGENT_CAP = 1000    # chars kept per subagent hand-back report
ASSIST_CAP = 2600      # chars kept per assistant text block
SUMMARY_CAP = 9000     # chars kept per compaction summary
PASTE_CAP = 2500       # chars kept per pasted block in history
WRAP = 320

# Secrets get pasted into prompts. Nothing that looks like a credential may reach a digest.
SECRET_PATTERNS = {
    "anthropic_key": r"sk-ant-[A-Za-z0-9_\-]{20,}",
    "api_key": r"sk-(?:proj-)?[A-Za-z0-9_\-]{32,}",
    "github_token": r"(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}",
    "hf_token": r"hf_[A-Za-z0-9]{30,}",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "slack_token": r"xox[baprs]-[A-Za-z0-9\-]{10,}",
    "google_key": r"AIza[0-9A-Za-z_\-]{35}",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    "url_credentials": r"(https?://)[^/\s:@]+:[^@\s/]{3,}@",
    "wandb_key": r"(?i)(wandb[^\n]{0,40}?)\b[0-9a-f]{40}\b",
}
SECRET_RES = {k: re.compile(v) for k, v in SECRET_PATTERNS.items()}
REDACTIONS: dict[str, int] = {}


def redact(t: str) -> str:
    for name, rx in SECRET_RES.items():
        def sub(m, name=name):
            REDACTIONS[name] = REDACTIONS.get(name, 0) + 1
            lead = m.group(1) if m.groups() else ""
            return f"{lead}[REDACTED:{name}]"
        t = rx.sub(sub, t)
    return t


TAG_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
CMD_RE = re.compile(r"<command-name>(.*?)</command-name>", re.S)
ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)
STDOUT_RE = re.compile(r"<local-command-stdout>.*?</local-command-stdout>", re.S)
CAVEAT_RE = re.compile(r"<local-command-caveat>.*?</local-command-caveat>", re.S)
MSG_RE = re.compile(r"<command-message>.*?</command-message>", re.S)


def clean_user_text(t: str) -> str:
    t = TAG_RE.sub("", t)
    t = CAVEAT_RE.sub("", t)
    t = STDOUT_RE.sub("", t)
    t = MSG_RE.sub("", t)
    cmd = CMD_RE.search(t)
    if cmd:
        args = ARGS_RE.search(t)
        rest = CMD_RE.sub("", ARGS_RE.sub("", t)).strip()
        a = (args.group(1).strip() if args else "")
        head = f"[slash command {cmd.group(1).strip()} {a}]".replace(" ]", "]")
        t = (head + ("\n" + rest if rest else "")).strip()
    return t.strip()


SCRATCH_RE = re.compile(r"/private/tmp/claude-\d+/[^/\s]+/[0-9a-f-]{36}/scratchpad")
TASKS_RE = re.compile(r"/private/tmp/claude-\d+/[^/\s]+/[0-9a-f-]{36}/tasks")
HOME = os.path.expanduser("~")
NOTIF_SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.S)
AGENT_FRAME_RE = re.compile(r"\[Subagent hand-back\].*?The report follows:\s*", re.S)


HOME_ENC = HOME.replace("/", "-")


def short_paths(t: str) -> str:
    t = SCRATCH_RE.sub("$SCRATCH", t)
    t = TASKS_RE.sub("$TASKS", t)
    return t.replace(HOME, "~")


def slugify(path_text: str) -> str:
    """A file-name-safe project slug without the home folder (which names the user)."""
    s = short_paths(path_text)
    s = s[2:] if s.startswith("~/") else s
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-") or "root"


def classify(txt: str):
    """Return (kind, text). kind: user | notification | subagent."""
    s0 = txt.lstrip()
    if s0.startswith("<task-notification>"):
        m = NOTIF_SUMMARY_RE.search(s0)
        return "notification", (m.group(1).strip() if m else "task finished")
    if s0.startswith("<agent-message"):
        body = AGENT_FRAME_RE.sub("", s0)
        body = re.sub(r"</?agent-message[^>]*>", "", body).strip()
        body = "\n".join(l[2:] if l.startswith("  ") else l for l in body.splitlines())
        return "subagent", body
    return "user", txt


def cap(t: str, n: int) -> str:
    if len(t) <= n:
        return t
    keep_head = int(n * 0.75)
    keep_tail = n - keep_head
    return t[:keep_head] + f"\n[... {len(t) - n} chars cut ...]\n" + t[-keep_tail:]


def wrap(t: str) -> str:
    out = []
    for line in t.splitlines():
        if len(line) <= WRAP:
            out.append(line)
        else:
            out.extend(textwrap.wrap(line, WRAP, break_long_words=True,
                                     replace_whitespace=False, drop_whitespace=False) or [""])
    return "\n".join(out)


def ts_short(ts) -> str:
    if not ts:
        return "?"
    if isinstance(ts, (int, float)):
        return dt.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
    # Session records carry UTC ISO strings, history carries epoch ms read as local time.
    # Convert both to local time so the same prompt shows the same clock in both digests.
    try:
        d = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if d.tzinfo is not None:
            d = d.astimezone()
        return d.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return str(ts)[:16].replace("T", " ")


def tool_line(b: dict) -> str:
    name = b.get("name", "?")
    inp = b.get("input") or {}
    def s(k, n=170):
        v = inp.get(k)
        if v is None:
            return ""
        v = v if isinstance(v, str) else json.dumps(v)
        v = short_paths(v).replace("\n", " ⏎ ")
        return v[:n] + ("…" if len(v) > n else "")
    if name == "Bash":
        d = s("description", 110)
        c = s("command", 110)
        return f"Bash: {d} :: {c}" if d else f"Bash: {c}"
    if name in ("Read", "Write", "Edit", "NotebookEdit"):
        extra = ""
        if name == "Write":
            extra = f" ({len(inp.get('content', '') or '')} chars)"
        return f"{name}: {s('file_path', 150)}{extra}"
    if name in ("Agent", "Task"):
        return (f"Agent[{inp.get('subagent_type', 'general')}"
                f"{'/' + inp['model'] if inp.get('model') else ''}]: {s('description', 100)}"
                f" :: {s('prompt', 300)}")
    if name == "Skill":
        return f"Skill: {s('skill')} {s('args', 100)}"
    if name == "Workflow":
        return f"Workflow: {s('name', 80)} {s('script', 300)}"
    if name in ("Grep", "Glob"):
        return f"{name}: {s('pattern', 120)} in {s('path', 120)}"
    if name == "AskUserQuestion":
        return f"AskUserQuestion: {s('questions', 500)}"
    if name in ("WebSearch", "WebFetch"):
        return f"{name}: {s('query', 160)}{s('url', 160)}"
    return f"{name}: {json.dumps(inp)[:200]}"


class Chunker:
    def __init__(self, out_dir: Path, stem: str, chunk_bytes: int, header: str):
        self.out_dir, self.stem, self.limit, self.header = out_dir, stem, chunk_bytes, header
        self.buf: list[str] = []
        self.size = 0
        self.idx = 0
        self.files: list[tuple[str, int]] = []
        out_dir.mkdir(parents=True, exist_ok=True)

    def add(self, block: str):
        block = wrap(redact(block)).rstrip() + "\n\n"
        b = len(block.encode("utf-8", "replace"))
        if self.size + b > self.limit and self.buf:
            self.flush()
        self.buf.append(block)
        self.size += b

    def flush(self):
        if not self.buf:
            return
        self.idx += 1
        name = f"{self.stem}_{self.idx:03d}.md"
        text = f"{self.header} — part {self.idx}\n\n" + "".join(self.buf)
        (self.out_dir / name).write_text(text, encoding="utf-8", errors="replace")
        self.files.append((name, len(text.encode("utf-8", "replace"))))
        self.buf, self.size = [], 0


def digest_session(path: Path, out_dir: Path, chunk_bytes: int, seen_uuids: set) -> dict:
    sid = path.stem
    title = ""
    first_ts = last_ts = None
    n_user = n_asst = n_tools = 0
    ch = Chunker(out_dir, sid[:8], chunk_bytes, f"# session {sid[:8]} ({path.parent.name})")
    pending_tools: list[str] = []
    seen_user_heads: set[str] = set()

    def flush_tools():
        nonlocal pending_tools
        if pending_tools:
            ch.add("TOOLS:\n" + "\n".join(f"  - {t}" for t in pending_tools))
            pending_tools = []

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith(SKIP_PREFIXES):
                continue
            if len(line) > 40_000_000:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            if t == "ai-title":
                title = o.get("aiTitle") or title
                continue
            if t == "queue-operation":
                if o.get("operation") == "enqueue" and o.get("content"):
                    kind, txt = classify(clean_user_text(str(o["content"])))
                    head = txt[:160]
                    if not txt or head in seen_user_heads:
                        continue
                    seen_user_heads.add(head)
                    if kind == "notification":
                        pending_tools.append(f"[background task done: {txt[:140]}]")
                    elif kind == "subagent":
                        flush_tools()
                        ch.add(f"#### SUBAGENT REPORT [{ts_short(o.get('timestamp'))}]\n{cap(short_paths(txt), SUBAGENT_CAP)}")
                    else:
                        flush_tools()
                        ch.add(f"## USER (typed mid-turn) [{ts_short(o.get('timestamp'))}]\n{cap(txt, USER_CAP)}")
                        n_user += 1
                continue
            if t not in ("user", "assistant"):
                continue
            if o.get("isSidechain"):
                continue
            uid = o.get("uuid")
            if uid:
                if uid in seen_uuids:
                    continue
                seen_uuids.add(uid)
            ts = o.get("timestamp")
            if ts:
                first_ts = first_ts or ts
                last_ts = ts
            msg = o.get("message") or {}
            content = msg.get("content")
            if t == "user":
                texts, n_img = [], 0
                if isinstance(content, str):
                    texts.append(content)
                elif isinstance(content, list):
                    for b in content:
                        bt = b.get("type")
                        if bt == "text":
                            texts.append(b.get("text", ""))
                        elif bt == "image":
                            n_img += 1
                raw = "\n".join(texts)
                if o.get("isCompactSummary"):
                    flush_tools()
                    ch.add(f"## [CONTEXT COMPACTION SUMMARY] [{ts_short(ts)}]\n{cap(raw, SUMMARY_CAP)}")
                    continue
                if o.get("isMeta"):
                    m = re.search(r"Base directory for this skill: (\S+)", raw)
                    if m:
                        pending_tools.append(f"[skill loaded: {Path(m.group(1)).name}]")
                    continue
                kind, txt = classify(clean_user_text(raw))
                if not txt and not n_img:
                    continue
                if kind == "notification":
                    if txt[:160] not in seen_user_heads:
                        seen_user_heads.add(txt[:160])
                        pending_tools.append(f"[background task done: {txt[:140]}]")
                    continue
                if kind == "subagent":
                    if txt[:160] not in seen_user_heads:
                        seen_user_heads.add(txt[:160])
                        flush_tools()
                        ch.add(f"#### SUBAGENT REPORT [{ts_short(ts)}]\n{cap(short_paths(txt), SUBAGENT_CAP)}")
                    continue
                if txt.startswith("[slash command /") and "\n" not in txt and len(txt) < 60:
                    continue
                head = txt[:160]
                if head in seen_user_heads and len(txt) < 400:
                    continue
                seen_user_heads.add(head)
                flush_tools()
                img = f" (+{n_img} image{'s' if n_img > 1 else ''})" if n_img else ""
                ch.add(f"## USER [{ts_short(ts)}]{img}\n{cap(txt, USER_CAP)}")
                n_user += 1
            else:
                if not isinstance(content, list):
                    continue
                for b in content:
                    bt = b.get("type")
                    if bt == "text":
                        txt = (b.get("text") or "").strip()
                        if txt:
                            flush_tools()
                            ch.add(f"### ASSISTANT [{ts_short(ts)}]\n{cap(short_paths(txt), ASSIST_CAP)}")
                            n_asst += 1
                    elif bt == "tool_use":
                        pending_tools.append(tool_line(b))
                        n_tools += 1
                        if len(pending_tools) >= 40:
                            flush_tools()
    flush_tools()
    ch.flush()
    return dict(session=sid, title=title, first=ts_short(first_ts), last=ts_short(last_ts),
                users=n_user, assistant=n_asst, tools=n_tools, files=ch.files,
                raw_mb=round(path.stat().st_size / 1e6, 1))


def digest_history(history: Path, out_root: Path, chunk_bytes: int, paste_dir: Path,
                   project_filter: str = "") -> list[dict]:
    by_proj: dict[str, list[dict]] = {}
    with open(history, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except Exception:
                continue
            proj = o.get("project", "?")
            if project_filter and project_filter not in proj:
                continue
            by_proj.setdefault(proj, []).append(o)
    rows = []
    for proj, items in sorted(by_proj.items(), key=lambda kv: -len(kv[1])):
        slug = slugify(proj)
        ch = Chunker(out_root / "history", f"history__{slug}", chunk_bytes,
                     f"# every prompt typed in {short_paths(proj)}")
        kept = 0
        for o in items:
            d = (o.get("display") or "").strip()
            if not d:
                continue
            if d.startswith("/") and len(d) < 40 and " " not in d.strip():
                continue
            if re.fullmatch(r"/(model|cost|status|login|clear|compact|effort|resume|exit|agents|config|fast|usage|context|memory|help|doctor|mcp|plugin|permissions|rewind|export|init|ide|theme|vim|voice|tasks|workflows|skills|stats|upgrade|logout|bug|review|plan)\b.*", d) and len(d) < 60:
                continue
            pastes = []
            for k, v in (o.get("pastedContents") or {}).items():
                c = v.get("content")
                if not c and v.get("contentHash"):
                    f = paste_dir / f"{v['contentHash']}.txt"
                    if f.exists():
                        c = f.read_text(errors="replace")
                if c:
                    pastes.append(f"  [pasted #{k}, {len(c)} chars]: " + cap(c, PASTE_CAP).replace("\n", "\n  "))
            block = f"[{ts_short(o.get('timestamp'))}] {cap(d, USER_CAP)}"
            if pastes:
                block += "\n" + "\n".join(pastes)
            ch.add(block)
            kept += 1
        ch.flush()
        rows.append(dict(project=short_paths(proj), slug=slug, prompts=kept, files=ch.files,
                         first=ts_short(items[0].get("timestamp")), last=ts_short(items[-1].get("timestamp"))))
    return rows


def main():
    ap = argparse.ArgumentParser(description="Condense Claude Code transcripts and prompt history into "
                                             "chunked, secret-redacted Markdown digests.")
    ap.add_argument("--out", required=True, help="digest folder to write (created if missing)")
    ap.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"),
                    help="folder of per-project session transcripts (default ~/.claude/projects)")
    ap.add_argument("--history", default=os.path.expanduser("~/.claude/history.jsonl"),
                    help="prompt history file (default ~/.claude/history.jsonl)")
    ap.add_argument("--paste-cache", default=os.path.expanduser("~/.claude/paste-cache"),
                    help="folder of pasted blocks referenced by hash from the history")
    ap.add_argument("--chunk-kb", type=int, default=60, help="chunk size in KB; 60 fits one Read call")
    ap.add_argument("--skip-sessions", action="store_true", help="digest the prompt history only")
    ap.add_argument("--skip-history", action="store_true", help="digest the session transcripts only")
    ap.add_argument("--project-filter", default="", help="keep only projects whose path contains this text")
    a = ap.parse_args()
    out = Path(a.out)
    chunk = a.chunk_kb * 1024
    index = ["# Digest index", ""]
    hist_path, proj_dir = Path(a.history), Path(a.projects_dir)
    use_hist = not a.skip_history and hist_path.is_file()
    use_sess = not a.skip_sessions and proj_dir.is_dir()
    if not use_hist and not use_sess:
        print(f"no input found: history {hist_path} ({'skipped' if a.skip_history else 'missing'}), "
              f"projects {proj_dir} ({'skipped' if a.skip_sessions else 'missing'})", file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)

    if use_hist:
        hist = digest_history(hist_path, out, chunk, Path(a.paste_cache), a.project_filter)
        index += ["## Prompt history (every prompt typed, by project)", ""]
        for r in hist:
            kb = sum(s for _, s in r["files"]) / 1024
            index.append(f"- **{r['project']}**: {r['prompts']} prompts, {r['first']} to {r['last']}, "
                         f"{len(r['files'])} file(s), {kb:.0f} KB: `history/history__{r['slug']}_NNN.md`")
        index.append("")

    if use_sess:
        index += ["## Session digests (prompts, assistant prose, tool trace)", ""]
        for proj in sorted(proj_dir.iterdir()):
            if not proj.is_dir():
                continue
            if a.project_filter and slugify(a.project_filter) not in proj.name:
                continue
            sessions = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
            if not sessions:
                continue
            slug = proj.name[len(HOME_ENC):] if proj.name.startswith(HOME_ENC) else proj.name
            slug = slug.strip("-") or "root"
            seen: set = set()
            index.append(f"### {slug}")
            for s in sessions:
                print(f"  digesting {slug}/{s.name} ({s.stat().st_size / 1e6:.0f} MB)", file=sys.stderr, flush=True)
                r = digest_session(s, out / "sessions" / slug, chunk, seen)
                kb = sum(sz for _, sz in r["files"]) / 1024
                index.append(f"- `{r['session'][:8]}` **{r['title'] or 'untitled'}**: {r['first']} to {r['last']}; "
                             f"{r['users']} user msgs, {r['assistant']} assistant msgs, {r['tools']} tool calls; "
                             f"raw {r['raw_mb']} MB to {len(r['files'])} chunk(s), {kb:.0f} KB "
                             f"(`sessions/{slug}/{r['session'][:8]}_NNN.md`)")
            index.append("")
    index = [redact(short_paths(line)) for line in index]  # session titles can carry pasted text too
    if REDACTIONS:
        index += ["## Secrets redacted", ""] + [f"- {k}: {v}" for k, v in sorted(REDACTIONS.items())] + [
            "", "These were found in the source history. Rotate them: a digest hides a secret, it does not revoke it.", ""]
    (out / "INDEX.md").write_text("\n".join(index) + "\n")
    print("\n".join(index))
    if REDACTIONS:
        print(f"\n{sum(REDACTIONS.values())} secret(s) redacted. Tell the owner to rotate every one of them.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
