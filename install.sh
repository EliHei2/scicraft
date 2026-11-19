#!/usr/bin/env bash
# Install scicraft skills for Claude Code.
#
#   ./install.sh plugins [--ml] [--all] [--scope user|project|local]
#       Registers this folder as a plugin marketplace and installs the plugins.
#       Skills then appear as scicraft:<skill> and scicraft-ml:<skill>.
#
#   ./install.sh skills [--ml] [--all] [--dest DIR] [--link] [--force]
#       Copies (or links) each skill folder into DIR, default ~/.claude/skills,
#       where it loads under its bare name. An existing folder of the same name
#       is left alone unless --force is given; --force moves it to a dated backup first.
#
#   ./install.sh list
#       Prints every skill in the package.
#
# Add --dry-run to see what would happen. Nothing is deleted by this script.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-}"; [ $# -gt 0 ] && shift
ML=0; SCOPE="user"; DEST="${HOME}/.claude/skills"; LINK=0; FORCE=0; DRY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --ml) ML=1 ;;
    --all) ML=1 ;;
    --scope) SCOPE="$2"; shift ;;
    --dest) DEST="$2"; shift ;;
    --link) LINK=1 ;;
    --force) FORCE=1 ;;
    --dry-run) DRY=1 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

PLUGINS=(scicraft)
[ "$ML" -eq 1 ] && PLUGINS+=(scicraft-ml)

run() { if [ "$DRY" -eq 1 ]; then echo "would run: $*"; else "$@"; fi; }

case "$MODE" in
  plugins)
    command -v claude >/dev/null || { echo "the claude command is not on PATH" >&2; exit 1; }
    run claude plugin marketplace add "$HERE" --scope "$SCOPE"
    for p in "${PLUGINS[@]}"; do
      run claude plugin install "${p}@scicraft" --scope "$SCOPE"
    done
    echo "done. Start a new Claude Code session to load the skills."
    ;;
  skills)
    run mkdir -p "$DEST"
    backup="${DEST}/.scicraft-backup-$(date +%Y%m%d-%H%M%S)"
    n=0; skipped=0
    for p in "${PLUGINS[@]}"; do
      for s in "$HERE/plugins/$p/skills"/*/; do
        [ -f "${s}SKILL.md" ] || continue
        name="$(basename "$s")"; target="$DEST/$name"
        if [ -e "$target" ] || [ -L "$target" ]; then
          if [ "$FORCE" -eq 1 ]; then
            run mkdir -p "$backup"; run mv "$target" "$backup/$name"
            echo "moved existing $name to $backup"
          else
            echo "skipped $name: $target exists (use --force to replace it, with a backup)"
            skipped=$((skipped + 1)); continue
          fi
        fi
        if [ "$LINK" -eq 1 ]; then run ln -s "${s%/}" "$target"; else run cp -R "${s%/}" "$target"; fi
        n=$((n + 1))
      done
    done
    echo "installed $n skill(s) into $DEST, skipped $skipped. Start a new Claude Code session to load them."
    ;;
  list)
    for d in "$HERE"/plugins/*/; do
      echo "$(basename "$d"):"
      for s in "$d"skills/*/; do [ -f "${s}SKILL.md" ] && echo "  $(basename "$s")"; done
    done
    ;;
  *)
    sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
