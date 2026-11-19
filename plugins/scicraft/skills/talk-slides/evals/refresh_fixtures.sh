#!/usr/bin/env bash
# Bring the test fixtures up to the current scripts: the builder copies of notes-on-slides and the planted-defect deck.
set -eu
cd "$(dirname "$0")"
cp ../scripts/deck.py ../scripts/placeholders.py notes-on-slides/files/talk_demo/build/
cp ../scripts/starter_deck.py notes-on-slides/files/talk_demo/build/build_deck.py
(cd audit-before-sending && python3 make_fixture.py && rm -rf files/talk_bad/media files/talk_bad/build/_cache files/talk_bad/build/notes)
echo fixtures refreshed
