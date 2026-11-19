# The leak scan

Run `scripts/leak_scan.py` before every push, upload, deploy and hub upload: on the repository with its history,
on the hub folder, on the built documentation and on every deposit folder.

```bash
python3 scripts/leak_scan.py <repo> --git --style --private ~/release_private/leak_private.txt
python3 scripts/leak_scan.py <built docs or site> --private ~/release_private/leak_private.txt --forbid <secret file>
```

Exit code 1 on any ERROR. Every WARN is read by a person and either fixed or accepted in the report.

## What it finds

| Level | Class | Examples |
|---|---|---|
| ERROR | home path | `/Users/<name>`, `/home/<name>`, a Windows user folder |
| ERROR | cluster path | `/scratch/...`, `/gpfs/...`, `/lustre/...`, `/project/...` |
| ERROR | scheduler | `#SBATCH`, `#BSUB`, `#PBS` lines |
| ERROR | review process | rebuttal, reviewer, OpenReview, area chair |
| ERROR | assistant trace | `CLAUDE.md`, `.claude/`, Co-Authored-By and Generated-with lines |
| ERROR | secret | Hugging Face, GitHub, AWS and API tokens, private keys (printed masked) |
| ERROR | private list | every pattern in `--private` |
| ERROR | forbidden content | the bytes of a `--forbid` file, in text or binary files (never printed) |
| WARN | leftover | TODO, FIXME, XXX, HACK |
| WARN | email | any address except noreply and example domains |
| WARN | claim word | state of the art, outperform, SOTA |
| WARN | image metadata | EXIF, XMP, software and comment chunks in PNG, JPEG, TIFF, WebP (needs Pillow) |
| WARN | style (`--style`) | `powerful`, `seamless`, `leverage`, `comprehensive`, `robust`, em dashes, middle dots between phrases, exclamation marks in prose |
| WARN | commit author (`--git`) | every author identity in the history, for a person to confirm |

Notebooks are read cell by cell, outputs included. File names are checked too.

## The private pattern file

The project's own names go in a file that lives outside every repository and never ships (example in
`assets/leak_private.example.txt`): people's names, in-house sample and cohort identifiers, internal run and
campaign names, internal hosts and group codes, internal names of model variants, the working title. One regular
expression per line. The generic classes above stay in the script; everything specific to one project goes here.

## Test it before trusting it

- **Run it on the research repository first: it should light up.** A scanner that finds nothing in the campaign
  repository is missing patterns.
- Then plant one string of every class in a scratch folder (a home path, a token, a scheduler line, an agent file
  reference, a private identifier, a secret file's content, an email, a TODO, a PNG with a software chunk, and a
  git commit with an attribution line) and check that each one is reported and the exit code is 1.

## Allowing what is meant to be public

- `--allow REGEX` drops findings whose matched text fits, for an address the page means to show.
- `--skip CLASS` drops a whole class. A package of agent skills must name the assistant, so it is scanned with
  `--skip "assistant trace"`; everything else stays on.

## What it cannot see

Unpublished numbers and results, a person named in a sentence that matches no pattern, a figure that shows
unpublished data, and file content in binary formats other than the forbid check. Those need the private list and
a person reading the diff. Say in the report what was scanned and what was not.
