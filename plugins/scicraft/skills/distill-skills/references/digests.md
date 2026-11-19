# Digests: condensing the history

`scripts/extract_sessions.py` is the script that made the digests of the original build, with the
project-specific path handling generalized. It reads Claude Code's own files; another agent tool needs
its own reader, and the rules below still hold.

## The sources and where they live

| Source | Default place | Holds |
|---|---|---|
| prompt history | `~/.claude/history.jsonl` | one JSON line per prompt typed: `display`, `project`, `timestamp` (epoch ms), `pastedContents` |
| pasted blocks | `~/.claude/paste-cache/[hash].txt` | long pastes the history refers to by `contentHash` |
| session transcripts | `~/.claude/projects/[encoded project path]/[session uuid].jsonl` | every record of a session: messages, tool calls, results, snapshots |
| memory notes | `~/.claude/projects/[encoded project path]/memory/*.md` | notes the agent saved: corrections, project state, pointers (read directly by K miners; not digested) |
| repositories, skills | wherever they live | ground truth for code, templates and styles (read directly by A miners) |

The encoded project path is the absolute path with `/` replaced by `-`. The script strips the home
part from slugs and index entries, so the user's name does not appear in file names.

## What a digest keeps

| Kept | Cap per block | Why |
|---|---|---|
| every prompt the author typed | 7,000 characters (head 75 percent, tail 25 percent) | the highest-value signal: corrections, praise, standing rules |
| prompts typed while the agent worked (queue operations) | 7,000 | mid-turn corrections are often the sharpest |
| assistant prose | 2,600 | what was claimed and decided |
| one line per tool call | about 110 to 300 characters per field | the procedure: commands, files written, agents launched with model and brief start |
| subagent hand-back reports | 1,000 | what delegated work returned |
| context compaction summaries | 9,000 | the densest record of state and method in the whole corpus |
| pasted blocks in the history | 2,500 | errors, reviews, messages the author pasted |
| markers | none | `[skill loaded: name]`, `[background task done: ...]`, `(+N images)` |

## What a digest drops

- Record types with no conversation in them: API request records, file-history snapshots, mode and
  permission changes, cost state, last-prompt pointers (skipped by line prefix before JSON parsing,
  which keeps a 300 MB session fast).
- Lines over 40 MB (base64 images and blobs).
- Sidechain records (a subagent's own turns inside the parent file).
- System reminders, local command output and caveats inside user messages.
- Bare slash commands under 60 characters (`/clear`, `/model`), and short repeats of a prompt already
  kept (deduplicated on the first 160 characters, and on record uuid across resumed sessions).
- Tool results. The one-line call trace plus the assistant's prose carries the procedure; the results
  are what made raw files 2 GB.

## Redaction

Every block passes through `redact()` inside the chunk writer, so nothing reaches a file unredacted;
the index lines are redacted too, because session titles can carry pasted text.

| Kind | Pattern (summary) |
|---|---|
| `anthropic_key` | `sk-ant-` plus at least 20 characters |
| `api_key` | `sk-` or `sk-proj-` plus at least 32 characters |
| `github_token` | `ghp_`, `gho_`, `ghs_`, `ghu_` plus 30, or `github_pat_` plus 40 |
| `hf_token` | `hf_` plus 30 |
| `aws_key` | `AKIA` plus 16 |
| `slack_token` | `xoxb-`, `xoxp-` and relatives |
| `google_key` | `AIza` plus 35 |
| `private_key` | a full `BEGIN ... PRIVATE KEY` block |
| `url_credentials` | `https://user:password@` (the scheme is kept) |
| `wandb_key` | a 40-hex string within 40 characters after `wandb` |

- A pattern list catches the formats it knows. A password typed in plain words, a database URL in an
  unusual form or a key of a service not listed passes through. Miners therefore still report every
  credential-like string they see in section 9, by place and never by value.
- **Rotate, then tell.** The index ends with a count per kind and the line "Rotate them". The lead puts
  the kinds and dates (never the values) on the state file's "tell the user" list and tells the user
  once at the start and again in the final report.
- Add a pattern when a miner reports a kind the list missed, and re-run the extractor.

## Output layout

```
digests/
├── INDEX.md                                   prompts per project, sessions with sizes, redaction counts
├── history/history__[project slug]_NNN.md     "[YYYY-MM-DD HH:MM] prompt", pastes indented below
└── sessions/[project slug]/[session8]_NNN.md  "## USER", "### ASSISTANT", "TOOLS:", "#### SUBAGENT REPORT"
```

Each chunk opens with a header naming its source and part number. Chunks are at most 60 KB by
default (`--chunk-kb`), the size one read call takes whole.

## Traps met

- **Notifications filed as prompts.** Background-task notifications and subagent hand-backs arrive as
  user-role records. The first digest counted them as the author's prompts, which would have put
  agent text in the author's mouth. `classify()` separates them; look at one chunk of every project
  before launching miners.
- **Two clocks.** History timestamps are epoch milliseconds (read as local time); session timestamps
  are UTC ISO strings. The original digests showed the same prompt an hour apart in the two files. The
  ported script converts both to local time.
- **Resumed sessions** repeat earlier records; the uuid set per project removes them.
- **A crashed session** has no closing records. Its digest simply ends; the compaction summaries
  before the crash still hold the state.
- **Scratch and task paths** of the agent's temp folders are replaced by `$SCRATCH` and `$TASKS`, and the
  home folder by `~`, in assistant prose and tool lines.

## Run it

```bash
python3 scripts/extract_sessions.py --help
python3 scripts/extract_sessions.py --out [ws]/digests                       # whole history
python3 scripts/extract_sessions.py --out [ws]/digests --skip-sessions       # prompts only, seconds
python3 scripts/extract_sessions.py --out [ws]/digests --project-filter paper # one project
```

Exit code 1 when neither the history file nor the projects folder exists. The run prints the index;
the number of redacted secrets goes to stderr. Test it on a synthetic home first:
`evals/digest-own-history/files/make_fixture.py OUT` writes a tiny one with two planted fake keys.
