# Contributing

scicraft grows by the same method that built it: a rule goes in when something
happened that the rule would have prevented.

## Before you open a pull request

1. Read [`docs/AUTHORING.md`](../docs/AUTHORING.md). It is the contract every skill is
   written to: evidence for each rule, numbers with their reasons, no private
   material, plain prose.
2. Run the gate. It checks structure, links, scripts, private strings and voice:

   ```bash
   python3 tools/check.py
   python3 tools/build_index.py
   python3 tools/build_third_party.py
   ```

3. Run every script you added or changed on a small real input. A script that
   has not run does not ship.
4. A new skill needs one line in `tools/catalog.json`: the stage of a project it
   belongs to and what it does, in at most 72 characters. `tools/build_index.py`
   then rewrites the overview in the README and `docs/INDEX.md`.

## What a good contribution looks like

- **A rule with its story.** What was asked for, what was thrown out, what
  replaced it. A rule with no failure behind it is advice, and advice stays out.
- **One home per rule.** If a sibling skill owns the topic, point to it.
- **Nothing private.** No names of colleagues, no institute infrastructure, no
  unpublished results, no reviewer text. Use a bracketed placeholder or a
  clearly fictional value.
- **A test case** for a new capability with a result someone can check.

## Reporting a problem

Open an issue with the request you typed, what the skill did, and what you
expected. For anything that should not be public, see [`SECURITY.md`](SECURITY.md).

By contributing you agree that your contribution is licensed under the
Apache License 2.0, like the rest of the repository.
