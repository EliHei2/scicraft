"""Count the downloads of this repository and draw the badge in the README.

    downloads = git clones, minus the runs of this repository's own workflows, plus downloads of release files

GitHub reports clones for the last 14 days only, so the workflow `traffic` archives them once a day. A clone is
what `claude plugin marketplace add`, `git clone` and `./install.sh` do. Each run of another workflow of this
repository checks the code out once, which GitHub counts as a clone, so it is taken off, per day and never below
zero. This script reads and writes through the API and makes no clone of its own.

It keeps three files on the branch `traffic`: downloads.json (every day and the totals), badge.svg (the README
shows it, also while the repository is private) and badge.json (the same number for a shields.io endpoint badge).

Environment: GITHUB_REPOSITORY (owner/name), GITHUB_TOKEN (contents: write, actions: read) and, for the clone
counts, TRAFFIC_TOKEN (a fine-grained token for this repository with "Administration: read-only"). Without
TRAFFIC_TOKEN the stored clone counts stay as they are. DRY_RUN=1 prints the files and writes nothing.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
TRAFFIC_TOKEN = os.environ.get("TRAFFIC_TOKEN", "")
BRANCH = "traffic"
OWN_WORKFLOW = ".github/workflows/traffic.yml"          # makes no clone, so its runs are not taken off
NOTE = "downloads = clones - own_workflow_runs (per day, never below 0) + release_downloads"
# Advance widths of Verdana at 11 px, the font of shields.io badges, so that this badge has their proportions.
WIDTHS = {**{c: 6.99 for c in "0123456789"}, ",": 4.0, ".": 4.0, " ": 3.87, "a": 6.61, "b": 6.85, "c": 5.73, "d": 6.85,
          "e": 6.55, "f": 3.87, "g": 6.85, "h": 6.96, "i": 3.02, "j": 3.79, "k": 6.51, "l": 3.02, "m": 10.7, "n": 6.96,
          "o": 6.68, "p": 6.85, "q": 6.85, "r": 4.69, "s": 5.73, "t": 4.33, "u": 6.96, "v": 6.51, "w": 9.0, "x": 6.51,
          "y": 6.51, "z": 5.78}


def api(path: str, token: str = TOKEN, method: str = "GET", body: dict | None = None):
    """One API call. A missing object (404, or 409 for an empty repository) comes back as None."""
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "downloads-badge"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if method == "GET" and e.code in (404, 409):
            return None
        raise SystemExit(f"{method} {path.split('?')[0]}: HTTP {e.code} {e.reason}")


def stored(name: str) -> str | None:
    got = api(f"/repos/{REPO}/contents/{name}?ref={BRANCH}")
    return base64.b64decode(got["content"]).decode() if got else None


def own_runs_by_day(first_day: str) -> dict[str, int]:
    runs, page = {}, 1
    while page <= 20:
        got = api(f"/repos/{REPO}/actions/runs?per_page=100&page={page}&created=%3E%3D{first_day}") or {}
        batch = got.get("workflow_runs", [])
        for run in batch:
            if run.get("path", "").split("@")[0] != OWN_WORKFLOW:
                runs[run["created_at"][:10]] = runs.get(run["created_at"][:10], 0) + 1
        if len(batch) < 100:
            break
        page += 1
    return runs


def badge_svg(label: str, value: str, color: str = "#007ec6") -> str:
    def width(text: str) -> int:
        return round(sum(WIDTHS.get(c, 7.0) for c in text))

    lt, vt = width(label), width(value)
    lw, vw = lt + 10, vt + 10
    w = lw + vw

    def text(s: str, x: float, length: int) -> str:
        x10, l10 = round(x * 10), length * 10
        return (f'<text aria-hidden="true" x="{x10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{l10}">{s}</text>'
                f'<text x="{x10}" y="140" transform="scale(.1)" fill="#fff" textLength="{l10}">{s}</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{label}: {value}">'
            f'<title>{label}: {value}</title>'
            '<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>'
            f'<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>'
            f'<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#555"/><rect x="{lw}" width="{vw}" height="20" fill="{color}"/>'
            f'<rect width="{w}" height="20" fill="url(#s)"/></g>'
            '<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">'
            f'{text(label, lw / 2 + 0.5, lt)}{text(value, lw + vw / 2 - 0.5, vt)}</g></svg>\n')


def main() -> None:
    old = stored("downloads.json")
    data = json.loads(old) if old else {}
    days: dict[str, dict] = data.get("days", {})
    counted_from, counted_to = data.get("counted_from"), data.get("counted_to")

    if TRAFFIC_TOKEN:
        clones = (api(f"/repos/{REPO}/traffic/clones?per=day", TRAFFIC_TOKEN) or {}).get("clones", [])
        if clones:
            created = (api(f"/repos/{REPO}") or {}).get("created_at", "")[:10]      # no count is older than the repository
            window = [d for d in (c["timestamp"][:10] for c in clones) if d >= created]
            clones = [c for c in clones if c["timestamp"][:10] >= created]
        if clones:
            runs = own_runs_by_day(min(window))
            for c in clones:
                day = c["timestamp"][:10]
                row = {"clones": c["count"], "unique": c["uniques"], "own_workflow_runs": runs.get(day, 0)}
                if row["clones"] or day in days:
                    days[day] = row
            counted_from = max(min(counted_from or min(window), min(window)), created)
            counted_to = max(counted_to or max(window), max(window))
    else:
        print("no TRAFFIC_TOKEN: the stored clone counts stay as they are")

    releases = api(f"/repos/{REPO}/releases?per_page=100") or []
    release_downloads = sum(a["download_count"] for r in releases for a in r.get("assets", []))
    clones_total = sum(d["clones"] for d in days.values())
    own_total = sum(min(d["clones"], d["own_workflow_runs"]) for d in days.values())
    downloads = clones_total - own_total + release_downloads

    out = {"downloads": downloads, "clones": clones_total, "own_workflow_runs": own_total,
           "release_downloads": release_downloads, "note": NOTE, "counted_from": counted_from, "counted_to": counted_to,
           "days": dict(sorted(days.items()))}
    files = {"downloads.json": json.dumps(out, indent=1) + "\n",
             "badge.json": json.dumps({"schemaVersion": 1, "label": "downloads", "message": f"{downloads:,}", "color": "blue"}) + "\n",
             "badge.svg": badge_svg("downloads", f"{downloads:,}")}
    print(f"{REPO}: {downloads:,} downloads ({clones_total} clones, {own_total} own workflow runs, {release_downloads} release downloads)")

    if os.environ.get("DRY_RUN"):
        for name, text in files.items():
            print(f"--- {name}\n{text}", end="")
        return
    if files["downloads.json"] == old and stored("badge.svg") == files["badge.svg"]:
        print("nothing changed")
        return
    tree = [{"path": n, "mode": "100644", "type": "blob", "content": t} for n, t in files.items()]
    ref = api(f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    if ref:                                                          # one commit on top of the branch
        parent = ref["object"]["sha"]
        base = api(f"/repos/{REPO}/git/commits/{parent}")["tree"]["sha"]
        new_tree = api(f"/repos/{REPO}/git/trees", method="POST", body={"base_tree": base, "tree": tree})
        commit = api(f"/repos/{REPO}/git/commits", method="POST",
                     body={"message": f"downloads: {downloads:,}", "tree": new_tree["sha"], "parents": [parent]})
        api(f"/repos/{REPO}/git/refs/heads/{BRANCH}", method="PATCH", body={"sha": commit["sha"]})
    else:                                                            # first run: a branch with no history in common with main
        new_tree = api(f"/repos/{REPO}/git/trees", method="POST", body={"tree": tree})
        commit = api(f"/repos/{REPO}/git/commits", method="POST",
                     body={"message": f"downloads: {downloads:,}", "tree": new_tree["sha"], "parents": []})
        api(f"/repos/{REPO}/git/refs", method="POST", body={"ref": f"refs/heads/{BRANCH}", "sha": commit["sha"]})
    print(f"wrote {', '.join(files)} to the branch {BRANCH}")


if __name__ == "__main__":
    sys.exit(main())
