#!/usr/bin/env python3
"""Look through a built site for things that must not leave the machine. Run it on dist/ (or public/) before every push.

    python3 leak_scan.py <folder> [--patterns FILE] [--forbid FILE ...] [--allow REGEX ...]

It reports, and exits 1 if it finds any of:
  - local and cluster paths, e-mail addresses, access tokens and private keys in text files (html, js, css, json, svg, ...)
  - project-specific patterns: one regular expression per line in --patterns (sample or patient identifiers, internal
    names, the names of results that are not public, words the author has retired)
  - the content of a secret file anywhere, text or binary (--forbid pipeline/.beta_password): the value is never printed
  - metadata inside images (EXIF, XMP, text chunks), where the camera, the software or a path can hide

--allow drops findings whose matched text fits the expression (for a known harmless match, e.g. an address the page
means to show). Nothing is sent anywhere; this only reads files.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TEXT = {'.html', '.htm', '.js', '.mjs', '.css', '.json', '.svg', '.txt', '.md', '.xml', '.csv', '.tsv', '.map', '.yaml', '.yml'}
IMAGE = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.tif', '.tiff'}
DEFAULT = [
    (r'/Users/[A-Za-z0-9._-]+', 'a home folder path'),
    (r'/home/[A-Za-z0-9._-]+', 'a home folder path'),
    (r'(?<![A-Za-z0-9])/(?:mnt|scratch|gpfs|lustre|omics|cluster|nfs)/[A-Za-z0-9._/-]+', 'a cluster path'),
    (r'[A-Za-z]:\\\\Users\\\\', 'a home folder path'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b', 'an e-mail address'),
    (r'-----BEGIN [A-Z ]*PRIVATE KEY-----', 'a private key'),
    (r'\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}', 'a GitHub token'),
    (r'\bhf_[A-Za-z0-9]{30,}', 'a Hugging Face token'),
    (r'\bsk-[A-Za-z0-9_-]{20,}', 'an API key'),
    (r'\bAKIA[0-9A-Z]{16}\b', 'an AWS key id'),
]


def image_metadata(path: Path):
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            keys = [k for k in im.info if k.lower() in ('exif', 'xmp', 'xml:com.adobe.xmp', 'comment', 'software', 'description', 'author', 'icc_profile') and im.info[k]]
            keys = [k for k in keys if k.lower() != 'icc_profile']                      # a colour profile is not a leak
            return keys
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('folder')
    ap.add_argument('--patterns', help='a file with one regular expression per line (lines starting with # are ignored)')
    ap.add_argument('--forbid', action='append', default=[], help='a file whose content must not appear anywhere')
    ap.add_argument('--allow', action='append', default=[], help='drop findings whose matched text fits this expression')
    a = ap.parse_args()
    root = Path(a.folder)
    if not root.is_dir():
        raise SystemExit(f'no such folder: {root}')
    pats = [(re.compile(p), why) for p, why in DEFAULT]
    if a.patterns:
        for line in Path(a.patterns).read_text().splitlines():
            if line.strip() and not line.startswith('#'):
                pats.append((re.compile(line.strip()), 'a project pattern'))
    allow = [re.compile(x) for x in a.allow]
    forbid = [(f, Path(f).read_bytes().strip()) for f in a.forbid if Path(f).exists()]
    found, no_pil = [], False
    files = [p for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts]
    for p in files:
        rel, ext = p.relative_to(root), p.suffix.lower()
        raw = p.read_bytes()
        for name, secret in forbid:
            if secret and secret in raw:
                kind = '' if ext in TEXT else ' (a binary file: a short secret can occur by chance in compressed bytes; check whether the hit is text before acting)'
                found.append(f'{rel}: holds the content of {name}{kind}')
        if ext in TEXT:
            text = raw.decode('utf-8', 'replace')
            for rx, why in pats:
                for m in rx.finditer(text):
                    if any(x.search(m.group(0)) for x in allow):
                        continue
                    line = text.count('\n', 0, m.start()) + 1
                    found.append(f'{rel}:{line}: {why}: {m.group(0)[:80]}')
                    break                                                  # one per pattern and file is enough to act on
        elif ext in IMAGE:
            keys = image_metadata(p)
            if keys is None:
                no_pil = True
            elif keys:
                found.append(f'{rel}: image metadata ({", ".join(keys)})')
    print(f'{len(files)} files scanned in {root}')
    if no_pil:
        print('note: Pillow is not installed, so image metadata was not checked (pip install pillow)')
    for f in found:
        print('  ' + f)
    print('clean' if not found else f'{len(found)} finding(s): fix them, or --allow what is meant to be public')
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
