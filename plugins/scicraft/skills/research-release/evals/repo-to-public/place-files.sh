#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
cd research_repo
# The planted home path and token are assembled here so that the skill package itself holds neither.
HOME_PATH="/Us""ers/jdoe"
TOKEN="hf""_QwErTyUiOpAsDfGhJkLzXcVbNm1234567890"
for f in $(grep -rl '@@HOME@@\|@@TOKEN@@' .); do
  sed -i.bak -e "s#@@HOME@@#${HOME_PATH}#g" -e "s#@@TOKEN@@#${TOKEN}#g" "$f" && rm -f "$f.bak"
done
git init -q .
git add .
git -c user.name="Lab Member" -c user.email=member@example.org commit -qm "Campaign state used for the paper

Co-Authored-By: Claude <noreply@anthropic.com>"
