#!/usr/bin/env python3
"""Write the manifest of a data deposit: every file with size, md5 and sha256, checked against pinned checksums.

    python3 make_manifest.py <deposit folder> [--pinned PINNED.tsv] [--base-url URL]
                             [--copy "aws s3 cp {local} {url}"] [--out DIR]

For every file under <deposit folder> (symlinks followed, hidden files skipped) it writes, into --out
(default: the deposit folder):

  MANIFEST.tsv   path, size_bytes, md5, sha256, pinned_md5, status, url
  SHA256SUMS     in `shasum -a 256 -c` format, so a receiver can verify the download
  UPLOAD.md      the exact upload commands (one per file, from --copy), the file count and total size

--pinned is a TSV with columns `path` and `md5` (paths relative to the deposit folder): the checksums the code
or notebooks already expect, for example a datasets registry in the package. A file whose md5 differs from its pin
is a MISMATCH and makes the exit code 1; a pinned file that is absent is MISSING and also fails. Re-export a file
only together with a new pin.

--base-url is joined with each relative path to give the public URL the notebooks will download from.
--copy is a command template with {local} and {url}; without it UPLOAD.md lists the files only.
Standard library only. Nothing is uploaded.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shlex
import sys
from pathlib import Path

OWN = {"MANIFEST.tsv", "SHA256SUMS", "UPLOAD.md"}


def digests(path: Path, chunk: int = 1 << 24):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            md5.update(block)
            sha.update(block)
    return md5.hexdigest(), sha.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--pinned", type=Path, help="TSV with columns path and md5")
    ap.add_argument("--base-url", default="", help="public URL prefix; the relative path is appended")
    ap.add_argument("--copy", default="", help='upload command template, e.g. "aws s3 cp {local} {url}"')
    ap.add_argument("--out", type=Path, help="where the three files go (default: the deposit folder)")
    a = ap.parse_args()
    root = a.folder.resolve()
    if not root.is_dir():
        print(f"no such folder: {a.folder}")
        return 2
    out = (a.out or root).resolve()
    out.mkdir(parents=True, exist_ok=True)
    pinned = {}
    if a.pinned:
        with open(a.pinned, newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                pinned[row["path"].strip()] = row["md5"].strip().lower()

    rows = []
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and not any(part.startswith(".") for part in p.relative_to(root).parts)
                   and not (p.parent == out and p.name in OWN))
    for p in files:
        rel = p.relative_to(root).as_posix()
        md5, sha = digests(p)
        pin = pinned.get(rel, "")
        status = "ok" if not pin or pin == md5 else "MISMATCH"
        url = a.base_url.rstrip("/") + "/" + rel if a.base_url else ""
        rows.append({"path": rel, "size_bytes": p.stat().st_size, "md5": md5, "sha256": sha,
                     "pinned_md5": pin, "status": status, "url": url, "local": str(p)})
        print(f"{status:8s} {rel}", flush=True)
    present = {r["path"] for r in rows}
    for rel, pin in sorted(pinned.items()):
        if rel not in present:
            rows.append({"path": rel, "size_bytes": "", "md5": "", "sha256": "", "pinned_md5": pin,
                         "status": "MISSING", "url": "", "local": ""})
            print(f"MISSING  {rel}")

    cols = ["path", "size_bytes", "md5", "sha256", "pinned_md5", "status", "url"]
    with open(out / "MANIFEST.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(out / "SHA256SUMS", "w") as f:
        for r in rows:
            if r["sha256"]:
                f.write(f"{r['sha256']}  {r['path']}\n")

    real = [r for r in rows if r["sha256"]]
    total = sum(r["size_bytes"] for r in real)
    lines = ["# Files to upload", "",
             f"{len(real)} files, {total / 1e9:.2f} GB in total. Sizes and checksums are in `MANIFEST.tsv`;",
             "a receiver verifies the download with `shasum -a 256 -c SHA256SUMS`.", ""]
    if a.copy:
        if "{local}" not in a.copy:
            print("--copy needs {local} (and usually {url})")
            return 2
        lines += ["```bash"] + [a.copy.format(local=shlex.quote(r["local"]), url=shlex.quote(r["url"] or r["path"]))
                                for r in real] + ["```", ""]
    lines += ["| path | size (MB) | md5 |", "|---|---:|---|"]
    lines += [f"| `{r['path']}` | {r['size_bytes'] / 1e6:,.1f} | `{r['md5']}` |" for r in real]
    (out / "UPLOAD.md").write_text("\n".join(lines) + "\n")

    bad = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(real)} files, {total / 1e9:.2f} GB; mismatched or missing against pins: {len(bad)}")
    print(f"wrote {out / 'MANIFEST.tsv'}, {out / 'SHA256SUMS'}, {out / 'UPLOAD.md'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
