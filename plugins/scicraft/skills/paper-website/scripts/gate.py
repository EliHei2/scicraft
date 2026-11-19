#!/usr/bin/env python3
"""Build a password-gated copy of a static site: <site>/public -> <site>/dist.

    python3 gate.py --site . --title "Short name" --subtitle "The rest of the title" [--icon brand/mark.png]

dist/index.html is a sign-in page that carries the real page encrypted (AES-GCM, key from PBKDF2-SHA256 of the
password). Every asset sits under dist/<secret>/, a folder whose name appears only inside the encrypted page, and
robots.txt asks crawlers to stay out. dist/ is what gets pushed to the host (GitHub Pages serves it as is).

This keeps casual visitors and search engines out. It is NOT strong access control: whoever has the password, or the
exact URL of a data file, can read it. Say so to the author before anything sensitive goes on the page.

The password and the secret folder name live in <site>/pipeline/.beta_password and <site>/pipeline/.deploy_secret.
They are created on the first run, never committed, never deployed, and never printed: do not echo them either, and
mask the folder name in any output you show (sed -E 's/[a-z0-9]{24}/<secret>/g').
  - to set a password, write it into .beta_password before running;
  - to change it, edit that file and run again (old links keep working);
  - to move the data folder as well, delete .deploy_secret.

Needs the `cryptography` package (pip install cryptography).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import string
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:  # pragma: no cover
    raise SystemExit('gate.py needs the cryptography package: pip install cryptography')

ITER = 250_000


def persisted(path: Path, make) -> str:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(make())
        os.chmod(path, 0o600)
    return path.read_text().strip()


GATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>/*TITLE*/</title>
/*ICONLINK*/
<style>
  :root { color-scheme: dark; }
  html, body { margin: 0; height: 100%; background: #141416; color: #f4f4f5; font: 300 16px/1.5 'Helvetica Neue', Helvetica, Inter, Arial, sans-serif; -webkit-font-smoothing: antialiased; }
  main { min-height: 100%; display: grid; place-items: center; padding: 24px; box-sizing: border-box; }
  form { width: min(100%, 400px); }
  .mark { display: block; width: 34px; height: auto; margin: 0 0 22px -2px; }
  .eyebrow { margin: 0 0 10px; font: 400 12px/1.4 ui-monospace, 'SF Mono', Menlo, monospace; color: #9b9ba2; }
  h1 { margin: 0 0 0 -0.04em; font-weight: 500; font-size: 60px; line-height: .95; letter-spacing: -0.045em; }
  .sub { margin: 14px 0 30px; max-width: 330px; color: #d2d2d7; font-size: 18px; line-height: 1.3; letter-spacing: -0.01em; text-wrap: balance; }
  .row { display: flex; gap: 8px; }
  input { flex: 1; min-width: 0; background: transparent; color: #fff; border: 0; border-radius: 999px; box-shadow: inset 0 0 0 1px #45454c; padding: 11px 18px; font: inherit; outline: none; }
  input::placeholder { color: #6f6f77; }
  input:focus { box-shadow: inset 0 0 0 1px #c9c9cf; }
  button { background: transparent; color: #f4f4f5; border: 0; border-radius: 999px; box-shadow: inset 0 0 0 1px #55555c; padding: 11px 20px; font: 500 15px 'Helvetica Neue', Helvetica, Inter, Arial, sans-serif; cursor: pointer; }
  button:hover, button:focus-visible { background: #fff; color: #141416; box-shadow: none; outline: none; }
  .msg { min-height: 22px; margin-top: 12px; padding-left: 18px; font-size: 13.5px; color: #d2d2d7; }
  .fine { margin: 22px 0 0; font-size: 12.5px; line-height: 1.5; color: #8b8b93; }
</style>
</head>
<body>
<main>
  <form id="f" autocomplete="on">
    /*ICONIMG*/
    <p class="eyebrow">Private preview</p>
    <h1>/*TITLE*/</h1>
    <p class="sub">/*SUBTITLE*/</p>
    <div class="row"><input id="pw" type="password" name="password" placeholder="Password" aria-label="Password" autocomplete="current-password" required autofocus><button>Enter</button></div>
    <div class="msg" id="msg" role="status" aria-live="polite"></div>
    <p class="fine">/*NOTICE*/</p>
    <input type="text" name="username" autocomplete="username" value="/*KEY*/" hidden>
  </form>
</main>
<script>
const P = /*PAYLOAD*/null, KEY = '/*KEY*/';
const b = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
async function unlock(pw, quiet) {
  try {
    const km = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
    const key = await crypto.subtle.deriveKey({ name: 'PBKDF2', salt: b(P.salt), iterations: P.iter, hash: 'SHA-256' }, km, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
    const html = new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: b(P.iv) }, key, b(P.data)));
    try { localStorage.setItem(KEY, pw); } catch (e) {}
    document.open(); document.write(html); document.close();
  } catch (e) {
    if (!quiet) document.getElementById('msg').textContent = 'That password did not work.';
    try { if (quiet) localStorage.removeItem(KEY); } catch (e2) {}
  }
}
document.getElementById('f').addEventListener('submit', (e) => { e.preventDefault(); document.getElementById('msg').textContent = ''; unlock(document.getElementById('pw').value, false); });
try { const s = localStorage.getItem(KEY); if (s) unlock(s, true); } catch (e) {}
</script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--site', default='.', help='the site folder, with public/ in it (default: the working directory)')
    ap.add_argument('--title', required=True, help='the name shown on the sign-in page')
    ap.add_argument('--subtitle', default='', help='one line under the name')
    ap.add_argument('--notice', default='Unpublished work. Please do not share the link or the password.')
    ap.add_argument('--icon', default='', help='a small png or svg inside public/, carried by the sign-in page itself')
    ap.add_argument('--max-mb', type=float, default=45, help='refuse files larger than this (GitHub rejects 100 MB and warns at 50)')
    ap.add_argument('--skip', default='', help='comma-separated path prefixes under public/ to hold back')
    a = ap.parse_args()

    site = Path(a.site).resolve()
    public, dist, pipe = site / 'public', site / 'dist', site / 'pipeline'
    if not (public / 'index.html').exists():
        raise SystemExit(f'no index.html in {public}')
    secret = persisted(pipe / '.deploy_secret', lambda: ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(24)))
    password = persisted(pipe / '.beta_password', lambda: secrets.token_urlsafe(9))

    dist.mkdir(exist_ok=True)
    for child in dist.iterdir():                                   # keep dist/.git: dist is its own repository
        if child.name == '.git':
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    root = dist / secret
    root.mkdir()
    skip = [s for s in a.skip.split(',') if s]
    too_big = []
    for p in sorted(public.rglob('*')):
        rel = p.relative_to(public)
        if p.is_dir() or p.name == 'index.html' or any(part.startswith('.') for part in rel.parts) or '.part' in p.name or any(str(rel).startswith(s) for s in skip):
            continue
        if p.stat().st_size > a.max_mb * 1e6:
            too_big.append(f'{rel} ({p.stat().st_size / 1e6:.0f} MB)')
            continue
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, root / rel)
    if too_big:
        raise SystemExit('too large for the host; split them into parts the page loads by range, or hold them back with --skip:\n  ' + '\n  '.join(too_big))

    page = (public / 'index.html').read_text()
    assert '<head>' in page, 'index.html has no <head>'
    page = page.replace('<head>', f'<head>\n<base href="{secret}/">', 1)          # every relative path now points into the secret folder
    page = re.sub(r'\s*<meta property="og:[^>]+>|\s*<meta name="twitter:[^>]+>', '', page)      # link previews would be empty anyway
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITER, 32)
    b64 = lambda b: base64.b64encode(b).decode()  # noqa: E731
    payload = json.dumps(dict(salt=b64(salt), iv=b64(iv), iter=ITER, data=b64(AESGCM(key).encrypt(iv, page.encode(), None))))
    link = img = ''
    if a.icon:
        icon = public / a.icon
        mime = 'image/svg+xml' if icon.suffix == '.svg' else f'image/{icon.suffix.lstrip(".")}'
        uri = f'data:{mime};base64,{b64(icon.read_bytes())}'
        link, img = f'<link rel="icon" href="{uri}">', f'<img class="mark" src="{uri}" alt="" width="34">'
    slug = re.sub(r'[^a-z0-9]+', '-', a.title.lower()).strip('-') + '-preview'
    esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;')  # noqa: E731
    html = (GATE.replace('/*TITLE*/', esc(a.title)).replace('/*SUBTITLE*/', esc(a.subtitle)).replace('/*NOTICE*/', esc(a.notice))
            .replace('/*ICONLINK*/', link).replace('/*ICONIMG*/', img).replace('/*KEY*/', slug).replace('/*PAYLOAD*/null', payload))
    (dist / 'index.html').write_text(html)
    (dist / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
    (dist / '.nojekyll').write_text('')

    files = [p for p in dist.rglob('*') if p.is_file() and '.git' not in p.parts]
    total, biggest = sum(p.stat().st_size for p in files), max(files, key=lambda p: p.stat().st_size)
    print(f'dist: {len(files)} files, {total / 1e6:.1f} MB, largest {biggest.stat().st_size / 1e6:.1f} MB ({biggest.name}). '
          'The password is in pipeline/.beta_password; run leak_scan.py on dist/ before pushing.')


if __name__ == '__main__':
    main()
