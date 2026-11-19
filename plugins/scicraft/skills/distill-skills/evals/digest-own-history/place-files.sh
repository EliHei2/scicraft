#!/usr/bin/env bash
set -eu
# Builds a tiny synthetic Claude Code home in the working folder (./claude_home) with two planted fake keys.
python3 "$(dirname "$0")/files/make_fixture.py" .
