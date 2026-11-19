#!/bin/bash
# Check a release candidate folder before anything is published. Publishes nothing.
#
#   bash check_release.sh <rc folder> [fast]
#
# The rc folder holds what the build side handed over:
#   SHA256SUMS            checksums of every file in the folder (shasum -a 256 format)
#   <name>.bundle         the public repository as a git bundle (git bundle create x.bundle --all)
#   hub/                  optional: model files, model card, data samples
#   docs_html.tar.gz      optional: the built documentation
#
# Settings come from the environment, so nothing in this file names a project or a machine:
#   PKG=<import name>          the package to import after install (required for step 5)
#   PY=<python>                interpreter for the clean environment (default: python3)
#   PRIVATE=<file>             private leak patterns, kept outside every repository (optional)
#   QUICKSTART=<script.py>     the README's quickstart, run as: python script.py <rc folder> <out.png> (optional)
#   OUT=<folder>               where results go (default: <rc folder>/../checks/<rc name>)
#   PYTEST="pytest<9"          the pytest requirement for the test environment (default: pytest)
#   PIP_ARGS="..."             extra pip arguments, e.g. --no-build-isolation on a machine without network
#
# "fast" builds the test environment with --system-site-packages, reusing this machine's heavy packages.
# Writes everything under $OUT, prints one PASS/FAIL/SKIP/INFO line per step, writes $OUT/SUMMARY.txt,
# and exits 1 on any FAIL.
set -u
export PYTHONNOUSERSITE=1   # packages in the user site would shadow the clean environment
case "${1:-}" in -h|--help|"") sed -n '2,23p' "$0" | sed 's/^# \{0,1\}//'; [ -z "${1:-}" ] && exit 2; exit 0;; esac
HERE=$(cd "$(dirname "$0")" && pwd)
IN=$(cd "$1" 2>/dev/null && pwd) || { echo "no such folder: $1"; exit 2; }
MODE=${2:-clean}
PY=${PY:-python3}
PKG=${PKG:-}
PRIVATE=${PRIVATE:-}
QUICKSTART=${QUICKSTART:-}
PIP_ARGS=${PIP_ARGS:-}
PYTEST=${PYTEST:-pytest}
OUT=${OUT:-$(dirname "$IN")/checks/$(basename "$IN")}
mkdir -p "$OUT"
LEAK=("$PY" "$HERE/leak_scan.py")
PRIV=()
[ -n "$PRIVATE" ] && PRIV=(--private "$PRIVATE")
RESULT=""
step() { RESULT="$RESULT$(printf '%-5s %s' "$1" "$2")\n"; printf '%-5s %s\n' "$1" "$2"; }

echo "== 1 checksums"
if [ -f "$IN/SHA256SUMS" ]; then
  if (cd "$IN" && shasum -a 256 -c SHA256SUMS > "$OUT/sums.txt" 2>&1); then step PASS "checksums ($(grep -c ': OK' "$OUT/sums.txt") files)"; else step FAIL "checksums: see $OUT/sums.txt"; fi
else step FAIL "no SHA256SUMS in $IN"; fi

echo "== 2 clone"
REPO="$OUT/repo"
BUNDLE=$(find "$IN" -maxdepth 1 -name '*.bundle' | head -1)
if [ -n "$BUNDLE" ]; then
  rm -rf "$REPO"
  if git clone -q "$BUNDLE" "$REPO" 2> "$OUT/clone.txt"; then
    step PASS "clone of $(basename "$BUNDLE"): $(git -C "$REPO" rev-list --count --all) commits, tags: $(git -C "$REPO" tag | tr '\n' ' ')"
  else step FAIL "clone: see $OUT/clone.txt"; fi
else step FAIL "no .bundle in $IN"; fi

echo "== 3 leak scan"
if [ -d "$REPO" ]; then
  if "${LEAK[@]}" "$REPO" --git --style ${PRIV[@]+"${PRIV[@]}"} > "$OUT/leak_repo.txt" 2>&1; then step PASS "leak scan, repository and history: $(tail -1 "$OUT/leak_repo.txt")"; else step FAIL "leak scan, repository and history: $(tail -1 "$OUT/leak_repo.txt") (see $OUT/leak_repo.txt)"; fi
fi
if [ -d "$IN/hub" ]; then
  if "${LEAK[@]}" "$IN/hub" --style ${PRIV[@]+"${PRIV[@]}"} > "$OUT/leak_hub.txt" 2>&1; then step PASS "leak scan, hub files: $(tail -1 "$OUT/leak_hub.txt")"; else step FAIL "leak scan, hub files: $(tail -1 "$OUT/leak_hub.txt")"; fi
else step SKIP "no hub/ folder"; fi
if [ -f "$IN/docs_html.tar.gz" ]; then
  rm -rf "$OUT/docs_html"; mkdir -p "$OUT/docs_html"; tar -xzf "$IN/docs_html.tar.gz" -C "$OUT/docs_html"
  if "${LEAK[@]}" "$OUT/docs_html" ${PRIV[@]+"${PRIV[@]}"} > "$OUT/leak_docs.txt" 2>&1; then step PASS "leak scan, built docs: $(tail -1 "$OUT/leak_docs.txt")"; else step FAIL "leak scan, built docs: $(tail -1 "$OUT/leak_docs.txt")"; fi
else step SKIP "no docs_html.tar.gz"; fi

echo "== 4 sizes"
if [ -d "$REPO" ]; then
  {
    echo "tracked files: $(git -C "$REPO" ls-files | wc -l | tr -d ' ')"
    echo "working tree:  $(du -sh "$REPO" | cut -f1)   .git: $(du -sh "$REPO/.git" | cut -f1)"
    echo "largest tracked files:"; (cd "$REPO" && git ls-files -z | xargs -0 ls -l 2>/dev/null | sort -k5 -n -r | head -8 | awk '{printf "  %8.1f kB  %s\n", $5/1000, $9}')
    echo "lines of Python in src/:"; (cd "$REPO" && [ -d src ] && find src -name '*.py' -print0 | xargs -0 wc -l 2>/dev/null | sort -n | tail -40)
    echo "Markdown files outside docs/: $(cd "$REPO" && git ls-files '*.md' | grep -v '^docs/' | tr '\n' ' ')"
  } > "$OUT/sizes.txt" 2>&1
  step INFO "sizes: $(sed -n 1,2p "$OUT/sizes.txt" | tr '\n' ' ') (details in $OUT/sizes.txt)"
  BIG=$(cd "$REPO" && git ls-files -z | xargs -0 ls -l 2>/dev/null | awk '$5 > 50000000 {print $9}')
  if [ -n "$BIG" ]; then step FAIL "tracked files over 50 MB: $BIG"; fi
fi

echo "== 5 install and tests ($MODE)"
VENV="$OUT/venv"
INSTALLED=""
if [ -d "$REPO" ] && [ -n "$PKG" ]; then
  rm -rf "$VENV"
  if [ "$MODE" = "fast" ]; then "$PY" -m venv --system-site-packages "$VENV"; else "$PY" -m venv "$VENV"; fi
  "$VENV/bin/python" -m pip install -q $PIP_ARGS --upgrade pip > "$OUT/install.txt" 2>&1
  if "$VENV/bin/python" -m pip install -q $PIP_ARGS "$REPO" >> "$OUT/install.txt" 2>&1; then
    INSTALLED=1
    step PASS "pip install: $PKG $("$VENV/bin/python" -c "import $PKG; print(getattr($PKG, '__version__', '(no __version__)'))" 2>&1 | tail -1)"
    if [ -d "$REPO/tests" ]; then
      "$VENV/bin/python" -m pip install -q $PIP_ARGS "$PYTEST" >> "$OUT/install.txt" 2>&1
      if (cd "$REPO" && "$VENV/bin/python" -m pytest -q tests > "$OUT/tests.txt" 2>&1); then step PASS "tests: $(tail -1 "$OUT/tests.txt")"; else step FAIL "tests: $(tail -1 "$OUT/tests.txt") (see $OUT/tests.txt)"; fi
    else step FAIL "no tests/ folder in the repository"; fi
  else step FAIL "pip install: see $OUT/install.txt"; fi
else step SKIP "install and tests: set PKG=<import name>"; fi

echo "== 6 quickstart"
if [ -n "$INSTALLED" ] && [ -n "$QUICKSTART" ] && [ -f "$QUICKSTART" ]; then
  if MPLBACKEND=Agg "$VENV/bin/python" "$QUICKSTART" "$IN" "$OUT/quickstart.png" > "$OUT/quickstart.txt" 2>&1; then
    step PASS "quickstart: $(tail -1 "$OUT/quickstart.txt"); figure at $OUT/quickstart.png (look at it)"
  else step FAIL "quickstart: $(tail -1 "$OUT/quickstart.txt") (see $OUT/quickstart.txt)"; fi
else step SKIP "quickstart: set QUICKSTART=<script> and PKG"; fi

echo "== 7 docs build"
if [ -n "$INSTALLED" ] && [ -f "$REPO/docs/conf.py" ]; then
  if "$VENV/bin/python" -m pip install -q $PIP_ARGS "$REPO[docs]" > "$OUT/docs_install.txt" 2>&1 && "$VENV/bin/python" -m sphinx -W -q -b html "$REPO/docs" "$OUT/docs_build" > "$OUT/docs.txt" 2>&1; then
    step PASS "docs build with warnings as errors: open $OUT/docs_build/index.html"
  else step FAIL "docs build: $(tail -1 "$OUT/docs.txt" 2>/dev/null) (see $OUT/docs_install.txt and $OUT/docs.txt)"; fi
else step SKIP "docs build: no docs/conf.py or no install"; fi

echo
echo "== summary for $(basename "$IN")"
printf "$RESULT" | tee "$OUT/SUMMARY.txt"
grep -q '^FAIL' "$OUT/SUMMARY.txt" && exit 1
exit 0
