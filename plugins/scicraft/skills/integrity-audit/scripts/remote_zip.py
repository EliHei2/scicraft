#!/usr/bin/env python3
"""Read members out of a remote ZIP over HTTP range requests (ZIP64 aware).

Used to verify that a public dataset bundle is byte-identical to the local copy:
it pulls one small member (a manifest, an experiment descriptor, a metrics CSV)
straight out of a multi-GB remote ZIP without downloading the archive.

    python3 remote_zip.py URL --list
    python3 remote_zip.py URL MEMBER [MEMBER ...]
    python3 remote_zip.py URL MEMBER --compare LOCAL_FILE [--compare LOCAL_FILE ...]
    python3 remote_zip.py URL MEMBER --out DIR

A member matches when its path inside the ZIP ends with the given name.
With --compare, the member's bytes are compared with the local file given in
the same position; the exit code is 1 on any mismatch or missing member.

The server must honor HTTP Range requests (most object stores and CDNs do).
If it answers a range request with the whole file, the script stops instead of
downloading the archive. Some vendor sites sit behind bot checks (HTTP 429);
their open CDN host usually supports ranges. Object-store paths are
case-sensitive: a 404 can be a capital letter in the prefix.

Standard library only. Python 3.9 or later.
"""
import argparse
import hashlib
import struct
import sys
import urllib.error
import urllib.request
import zlib
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125 Safari/537.36"


def _get(url, start=None, end=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if start is not None:
        req.add_header("Range", f"bytes={start}-{end}")
    with urllib.request.urlopen(req, timeout=120) as r:
        if start is not None and r.status != 206:
            raise RuntimeError(f"server ignored the Range header (HTTP {r.status}); "
                               "refusing to download the whole archive")
        return r.read(), dict(r.headers)


def size_of(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"]), dict(r.headers)


def central_directory(url, total):
    tail_n = min(1 << 20, total)
    tail, _ = _get(url, total - tail_n, total - 1)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise RuntimeError("no EOCD")
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])
    n_ent = struct.unpack("<H", tail[i + 10:i + 12])[0]
    j = tail.rfind(b"PK\x06\x06")
    if j >= 0:  # ZIP64
        n_ent, cd_size, cd_off = struct.unpack("<QQQ", tail[j + 32:j + 56])
    cd, _ = _get(url, cd_off, cd_off + cd_size - 1)
    return cd, n_ent


def parse_cd(cd):
    out, p = [], 0
    while p < len(cd) - 4 and cd[p:p + 4] == b"PK\x01\x02":
        (method,) = struct.unpack("<H", cd[p + 10:p + 12])
        (crc,) = struct.unpack("<I", cd[p + 16:p + 20])
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nlen, elen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
        lho, = struct.unpack("<I", cd[p + 42:p + 46])
        name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
        extra = cd[p + 46 + nlen:p + 46 + nlen + elen]
        # ZIP64 extra
        q = 0
        while q < len(extra) - 4:
            hid, hsz = struct.unpack("<HH", extra[q:q + 4])
            if hid == 0x0001:
                blob, k = extra[q + 4:q + 4 + hsz], 0
                if usize == 0xFFFFFFFF: usize = struct.unpack("<Q", blob[k:k + 8])[0]; k += 8
                if csize == 0xFFFFFFFF: csize = struct.unpack("<Q", blob[k:k + 8])[0]; k += 8
                if lho == 0xFFFFFFFF: lho = struct.unpack("<Q", blob[k:k + 8])[0]; k += 8
                break
            q += 4 + hsz
        out.append(dict(name=name, method=method, crc=crc, csize=csize, usize=usize, lho=lho))
        p += 46 + nlen + elen + clen
    return out


def read_member(url, ent):
    hdr, _ = _get(url, ent["lho"], ent["lho"] + 29)
    nlen, elen = struct.unpack("<HH", hdr[26:30])
    ds = ent["lho"] + 30 + nlen + elen
    if ent["csize"] == 0:
        return b""
    raw, _ = _get(url, ds, ds + ent["csize"] - 1)
    if ent["method"] == 0:
        data = raw
    elif ent["method"] == 8:
        data = zlib.decompressobj(-15).decompress(raw)
    else:
        raise RuntimeError(f"{ent['name']}: compression method {ent['method']} not supported")
    if zlib.crc32(data) & 0xFFFFFFFF != ent["crc"]:
        raise RuntimeError(f"{ent['name']}: CRC mismatch after reading; the transfer is incomplete")
    return data


def digests(data):
    return hashlib.md5(data).hexdigest(), hashlib.sha256(data).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="http(s) URL of the remote ZIP")
    ap.add_argument("members", nargs="*", help="member names to read (suffix match)")
    ap.add_argument("--list", action="store_true", help="list every member with sizes and stop")
    ap.add_argument("--compare", action="append", default=[], metavar="LOCAL",
                    help="local file to compare byte for byte with the member in the same position")
    ap.add_argument("--out", metavar="DIR", help="write each member here instead of printing it")
    ap.add_argument("--quiet", action="store_true", help="do not print member contents")
    a = ap.parse_args(argv)

    if a.compare and len(a.compare) != len(a.members):
        ap.error("give one --compare file per member, in the same order")
    if not a.list and not a.members:
        ap.error("name at least one member, or use --list")

    try:
        total, hdrs = size_of(a.url)
        print(f"# {a.url}\n#   HTTP 200  bytes={total}  last-modified={hdrs.get('Last-Modified')}  etag={hdrs.get('ETag')}")
        cd, n = central_directory(a.url, total)
    except (urllib.error.URLError, RuntimeError, KeyError, ValueError) as e:
        print(f"ERROR {a.url}: {e}", file=sys.stderr)
        return 2
    ents = parse_cd(cd)
    print(f"#   zip entries={len(ents)} (directory says {n})")
    if a.list:
        for e in ents:
            print(f"{e['usize']:>14}  {e['csize']:>14}  {e['name']}")
        return 0

    failed = 0
    for idx, w in enumerate(a.members):
        hit = [e for e in ents if e["name"].endswith(w)]
        if not hit:
            print(f"### MISSING {w}")
            failed += 1
            continue
        if len(hit) > 1:
            print(f"#   {w} matches {len(hit)} members; using {hit[0]['name']}")
        e = hit[0]
        try:
            data = read_member(a.url, e)
        except (urllib.error.URLError, RuntimeError) as err:
            print(f"### ERROR {e['name']}: {err}")
            failed += 1
            continue
        md5, sha = digests(data)
        print(f"### {e['name']}  (offset {e['lho']}, csize={e['csize']}, usize={e['usize']}, md5={md5}, sha256={sha})")
        if a.compare:
            local = Path(a.compare[idx])
            if not local.exists():
                print(f"    COMPARE {local}: local file missing")
                failed += 1
            else:
                ld = local.read_bytes()
                lmd5, _ = digests(ld)
                if ld == data:
                    print(f"    IDENTICAL to {local} ({len(ld)} bytes, md5={lmd5})")
                else:
                    first = next((i for i, (x, y) in enumerate(zip(ld, data)) if x != y), min(len(ld), len(data)))
                    print(f"    DIFFERENT from {local}: local {len(ld)} bytes md5={lmd5}, "
                          f"remote {len(data)} bytes; first difference at byte {first}")
                    failed += 1
        if a.out:
            dest = Path(a.out) / Path(e["name"]).name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            print(f"    wrote {dest}")
        elif not a.quiet and not a.compare:
            sys.stdout.write(data.decode("utf-8", "replace"))
            print()
    print(f"# checked {len(a.members)} member(s): {failed} problem(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
