#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
# The planted home path and address are assembled here so that the skill package itself holds neither.
HOME_PATH="/Us""ers/mlab"
EMAIL="plates-admin""@""lab-internal.org"
F=lab-skills/skills/plate-qc/SKILL.md
sed -i.bak -e "s#@@HOME@@#${HOME_PATH}#g" -e "s#@@EMAIL@@#${EMAIL}#g" "$F" && rm -f "$F.bak"
