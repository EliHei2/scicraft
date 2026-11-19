#!/usr/bin/env python3
"""Local preview of a static site, with HTTP Range support (large binary data is usually fetched by ranges, and
python -m http.server does not answer them). Binds to 127.0.0.1 only, so nothing is reachable from outside.

    python3 serve.py [port] [folder]        default: 8765 ./public

Run it in the background from the site folder. It is single-threaded in practice: run headless checks one browser
at a time.
"""
from __future__ import annotations

import argparse
import http.server
import os
import re
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
ap.add_argument('port', nargs='?', type=int, default=8765, help='port on 127.0.0.1 (default 8765)')
ap.add_argument('folder', nargs='?', default='public', help='folder to serve (default ./public)')
ARGS = ap.parse_args()
ROOT = Path(ARGS.folder).resolve()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_GET(self):
        m = re.fullmatch(r'bytes=(\d+)-(\d*)', self.headers.get('Range', ''))
        path = self.translate_path(self.path)
        if not m or not os.path.isfile(path):
            return super().do_GET()
        size = os.path.getsize(path)
        a = int(m.group(1))
        b = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
        if a > b:
            self.send_error(416)
            return
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {a}-{b}/{size}')
        self.send_header('Content-Length', str(b - a + 1))
        self.end_headers()
        with open(path, 'rb') as f:
            f.seek(a)
            self.wfile.write(f.read(b - a + 1))


if __name__ == '__main__':
    if not ROOT.is_dir():
        raise SystemExit(f'no such folder: {ROOT}')
    port = ARGS.port
    Handler.extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, '.webp': 'image/webp', '.js': 'text/javascript',
                              '.mjs': 'text/javascript', '.bin': 'application/octet-stream', '.woff2': 'font/woff2', '.svg': 'image/svg+xml'}
    print(f'http://127.0.0.1:{port}/  ({ROOT})', flush=True)
    http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
