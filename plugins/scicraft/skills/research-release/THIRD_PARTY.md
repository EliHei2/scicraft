# Third-party material

No third-party code or text is included. All scripts are the author's own code, ported and generalized:

| File | Ported from | Changes |
|---|---|---|
| `scripts/leak_scan.py` | the author's release leak scanner and the leak scan of the paper-website skill | project patterns moved to `--private`; generic path, scheduler and token classes; `--forbid`, `--allow`, `--skip`, image metadata, masked secrets |
| `scripts/check_release.sh` | the author's release-candidate check | paths, interpreter, package name and quickstart made parameters |
| `scripts/make_manifest.py` | the author's upload-manifest builder | any folder, pinned md5 from a TSV, sha256 and `SHA256SUMS`, standard library only |
| `scripts/stage_whitelist.py` | the author's whitelist staging script | whitelist from a TSV, ownership marker, table shape checks |
| `scripts/clean_notebook_outputs.py` | the author's notebook output cleaner | standard library instead of nbformat, `--check` mode |

The distribution options in `references/skill-packages.md` summarize public documentation (Claude Code, GitHub,
Zenodo) in new words, with the date it was read.
