# The edit-proposal protocol

Auditors never edit the artifact. They return proposals; one writer vets and applies them. This held for two
rounds of book line edits (about 514 applied edits), a rebuttal's wording hunt (130 proposals), every reference
audit and every figure audit in the source work.

## The fields

| Field | Required | Content |
|---|---|---|
| `id` | yes | unique within the file, prefixed by lane (`A3`, `REF-17`) |
| `file` | yes | path relative to the artifact root |
| `old` | yes | exact text from the current snapshot, occurring exactly once in that file |
| `new` | yes | the replacement; `null` for a query; equal to `old` for a deliberate keep |
| `why` | yes | the rule or source, with location (`RULES.md 4`, `table 2 row 3`, `ref full text p. 5`) |
| `type` | yes | `surgical`, `semantic` or `query` |
| `severity` | recommended | `blocker`, `major`, `minor` |
| `source` | for facts | `file:line` or page of the evidence |
| `job` | optional | the lens or job class (`fact`, `brush`, `overlap`) |

`assets/edits.schema.json` is the JSON Schema; pass it as the output schema when the agent runner supports one.

## Invariants, and the incidents behind them

- **`old` occurs exactly once.** Index-based edits with non-unique anchors on a 100 KB source file ate the abstract,
  the related work, four method subsections and the contributions list (about 15 turns lost).
- **No overlaps, all apply in order.** Agents re-anchored their edits when the file moved twice while they worked;
  the order check catches an edit whose `new` creates a second copy of a later `old`.
- **Minimum length.** The validator refuses an `old` under 12 characters by default (`--min-old`). The threshold is
  suggested, not yet tested in real work; uniqueness is the rule that was enforced.
- **Preservation.** Citation keys in order, cross-reference targets, labels, numbers, environments, equations,
  inline math and table bodies are identical before and after, unless the edit exists to change them. A de-AI pass
  checked all of these plus the word count before and after.
- **One line, balanced braces, no banned token added**, and in page-limited files a length change of zero or less
  (the wording-hunt self-check).

## The auditor's self-check

Before returning, the auditor applies all its edits to a copy and reports the result: valid JSON, each `old` found
exactly once, no overlap, preservation counts unchanged, braces balanced, and (for documents) a test build of the
copy. The coordinator does not trust this report; it re-runs the validator.

## The coordinator's procedure

1. Snapshot the target files (`cp` into `audit/rN/pre/`) before anything is applied.
2. Dry run with a review sheet:
   ```bash
   python3 <skill>/scripts/apply_edits.py audit/rN/A.json --root . --sheet audit/rN/SHEET_A.md --ban banned.txt
   ```
   Zero validation errors or the agent fixes its file. The validator was itself tested on a deliberately bad
   proposal before use; keep doing that when you change it.
3. Read the sheet. Every flagged item (a changed number, a changed citation key, a brace change, a banned word
   added, a long length change) is read in context, and every fact proposal against its source.
4. Decide per item: apply, edit (rewrite the proposal in the JSON and re-validate), or reject with a reason. Edits
   from typography-only passes are checked mechanically too (only the markup was inserted; nothing in captions,
   headings or tables), and weak ones are dropped by hand (43 weak bold proposals in one pass).
5. Apply the surgical set:
   ```bash
   python3 <skill>/scripts/apply_edits.py audit/rN/A.json --root . --skip A4,A9 --apply
   ```
   The script backs up the touched files, applies in order, confirms each new string landed and writes
   `A.changelog.md`.
6. Copy semantic and query items into `AUTHOR_DECISIONS.md` with the trade-off.
7. Rebuild and run the gates (triage-and-regression.md). Commit with the change log.

Apply group by group as reports arrive; do not wait for the whole fleet.

## Collision control

- **One writer per file.** When agents must edit (part files split at section boundaries), each part has exactly
  one editor, and the assembled file is never re-assembled from parts after later edits, because that overwrites
  them.
- **Figures before captions.** Re-crops and figure-file fixes go in immediately; caption edits wait for the line
  edits on the same files.
- **Do not send one request to two sessions.** It produced two versions of the same reply and the fear that one had
  overwritten the other. When it happens, compare the files byte by byte before reassuring anyone, and say in the
  first line where the version of record is.
- **Freeze the snapshot.** Auditors work on `audit/rN/`; the coordinator applies to the live tree. If the live tree
  moved, the validator reports which `old` strings no longer match, and those proposals are re-anchored or dropped.

## The wording hunt

A wording hunt is one copy-editing pass over a nearly final text: punctuation, house bans, one name per thing. It
ran once, by one agent, on the revised paper and appendix of a rebuttal and gave 130 proposals, most of them
punctuation in the appendix.

1. **Brief one copy-editor agent** with the user's request quoted verbatim, the file list, the banned tokens
   (`RULES_banned.txt`, one word or regex per line) and the rule "single-sentence fixes only, do not drift". The
   verbatim request keeps the agent on what was asked; "do not drift" keeps it from rewriting paragraphs.
2. **It returns `hunt.json`** in the edits format above, with the category in `job`: `punct` (punctuation only),
   `reword` (a word or phrase inside one sentence) or `flag` (a problem it will not fix, sent as a query with
   `"new": null`). Its short report gives the proposal counts per file and per category, and a terminology table:
   term, count in each file, keep or change. The table is where two names for one thing show up.
3. **It self-checks on a copy** before returning: each `old` occurs exactly once and sits on one line, braces
   balance, no `new` adds a banned token, and in a page-limited file the length change of each edit is zero or
   less.
4. **The coordinator re-runs the checks.** The dry run and its sheet cover uniqueness, braces, banned words added
   and the length change. The one-line rule is not in the validator; list breaches with
   ```bash
   python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d=d['edits'] if isinstance(d,dict) else d; print([e['id'] for e in d if '\n' in e['old'] or '\n' in (e['new'] or '')])" hunt.json
   ```
   Print the proposals grouped by category, read the `reword` items and every flagged sheet line in context, and
   apply the accepted set with `--apply`.
5. **Run a leftover scan with the same word list** after applying, so the hunt is measured by what remains:
   ```bash
   grep -n -i -E -f RULES_banned.txt paper/*.tex
   ```
   Every remaining hit is either fixed or recorded as a deliberate keep with its reason (a quote, a technical term).

## When the author takes over

If the author pastes a final version that undoes audit fixes, respect the text and list each undone fix with its
cost ("an unprinted number cited to an appendix; restoring the fix costs 40 characters"). The author decides.
