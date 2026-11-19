# The knowledge base

What a project knows about its field, its data, its methods and its own measurements, written so that a person or
an agent can find one fact in seconds and trust it as far as its source allows. It lives in `docs/kb/`.

## 1. What it is, and what it is not

The author built two. The first grew from their own notes: "I made a folder called knowledge base, these are all the
files that I made during conceptualization", with the request to build a knowledge base around them. It later
served a book, where drafts were told to "borrow facts (but not slop it)" from it. The second belonged to a
model campaign: 19 numbered entries on comparators, corpora, evaluation and pretraining practice, with a README
that listed the live ones.

**An entry belongs here when it states something that is true outside this repository's code, with how we know
it**: a definition, a published method, a license, a dataset census, an evaluation protocol, a measured property
of a tool.

| It is | It is not | That lives in |
|---|---|---|
| evidence: what is true and how we know | a decision about what to do | `DECISIONS.md`, which cites the entry |
| the field, the data, the methods of others | how this project's code is built | `DESIGN.md` |
| topic documents that outlive a session | facts about this machine and this package version | `NOTES.md` |
| a digest written from sources | the author's inputs, verbatim | `SPEC.md` |
| reference text an agent pulls on demand | text an agent loads on every turn | the index file |

## 2. Layout

```text
docs/kb/
  README.md      what this knowledge base is for, how to use it, the conventions
  INDEX.md       one line per entry; the file to read first
  NN_topic.md    the entries, numbered in order of creation
  sources/       whole texts that must be read in full (ignored by git when large)
  archive/       superseded entries, each with a banner naming its successor
```

Past about 30 entries, group them in folders by kind (`concepts/`, `methods/`, `metrics/`, `comparators/`,
`data/`) and keep `INDEX.md` at the top. The book's knowledge base used that form, with one metric per file. Its
index was named `llms.txt`, the name some tools look for; `scripts/doctor.py` accepts either name.

## 3. An entry

```text
# <Title: the topic in a few words>

> <One sentence: what this entry tells you.>

- Status: verified | partly verified | unverified
- Updated: <YYYY-MM-DD>
- Sources: <paper, code or dataset with its link and the date it was opened; own measurement with script and file>
- Used by: <the document or decision that relies on this entry>

## What is established
- [RUN] <a fact measured here, with the command or script>
- [DOC] <a fact read in a source, with the link and the date>

## What is open
- [U] <a claim not yet checked, and how to check it>

## Pointers
- Code: `path/to/file.py:line`
- Related entries: `NN_other.md`
```

The tags are those of the sibling `research-kickoff` skill: `[RUN]` ran it here, `[DOC]` read in a source,
`[U]` unverified.

## 4. Rules

- **One topic per file, and the first line under the title is its summary.** The source convention: "One topic
  per file." and "First paragraph = one-line summary." A reader decides in three seconds whether this is the file.
- **An entry stands alone.** It defines its terms and carries its formulas, so that two or three entries are
  enough context for a task. Size: one to three thousand tokens, about 100 to 400 lines. Split a longer one.
- **Evidence only.** The source README said of four recovered entries: "Read them as evidence, not as decisions."
  What the project does about a fact is a `DECISIONS.md` row.
- **Every claim carries its tag and its source.** A number names the command or the file that reproduces it. A
  source register carried the instruction never to quote a number from its prose without re-running the command.
- **A method is checked against its authors' code or paper, never against the entry.** An entry is a digest, and a
  digest written by an agent can be wrong in the one detail that matters.
- **Point to code, do not paste it.** `path/to/file.py:line`. Long snippets go stale without anyone noticing.
- **No filler.** The source convention: "No prose padding." No sentence that announces what a section will say.
- **A link never points at nothing.** A link to an entry that is not written yet is allowed only when `INDEX.md`
  lists that entry as planned.
- **Status is honest.** An entry written from an agent's research that nobody audited says `unverified`. An entry
  rebuilt after a crash says what it was rebuilt from and which steps of its making never ran.

## 5. The index

`INDEX.md` has one line per entry: the file, what it tells you, its status and its date. It is the only file of
the knowledge base that an agent reads without a reason.

```text
| Entry | What it tells you | Status | Updated |
|---|---|---|---|
| [`03_comparators.md`](03_comparators.md) | the published models we compare against, their inputs and weights | verified | 2026-03-02 |
| `07_license_tiers.md` | planned: which sources may train a released model | planned | |
```

The use, from the source README: "Pull only the 2-3 relevant files into the writing context".

## 6. Building one from a pile of sources

1. Put the raw material in `docs/kb/sources/`: notes, papers, exemplar texts. List what is there.
2. Name the topics the project needs. One entry each.
3. Write each entry from the sources: definitions, facts with tags, formulas, code pointers, links to sibling
   entries. The author's order for a cleanup: "clean up the knowledge based and produce proper agent-ready md
   files out of it".
4. Write the index line for each entry, and list planned entries as planned.
5. Verify. Open every `[DOC]` claim at its source. Check every method against its authors' code or paper.
6. Remove digested papers from the working folder once every claim taken from them sits in an entry with its
   citation. The author's wording: "once you make sure you have everything drop the papers". Keep a whole text
   only where it must be read in full, such as an exemplar whose structure and level of detail a draft should
   match.

Research done by helper agents enters the same way: as entries with `[DOC]` tags and sources, status `unverified`
until someone opens the sources.

## 7. Keeping it true

- **Archive, never delete, and never leave a stale entry beside live ones.** One cleanup moved sixteen superseded
  documents to `archive/`, each with a banner naming its successor. The README then said: "Nothing below is stale.
  If a document you remember is missing, it is archived, not deleted."
- **Consolidate.** When several entries answer one question, write one entry that replaces them and archive the
  originals. Five evaluation documents became two a week after the cleanup.
- **Write what a session learned before its context is lost.** The author's standing order at the end of a long
  session: "update claude.md, update knowledge base and compact".
- **A recovered entry carries its provenance.** Four entries were rebuilt from workflow journals after a crash.
  Each got a provenance line and a closing section naming the phases of its making that never ran.
- **Run `scripts/doctor.py`** after a reorganization: it lists entries missing from the index, index lines whose
  file is gone, and entries without a status or a date.

## 8. How an agent uses it

- Read `INDEX.md`. Open at most the two or three entries the task needs.
- Use an entry's facts with their tags. A `[U]` claim is verified before anything is built on it.
- When writing prose from the knowledge base, take the facts and the citations and write new sentences in the
  voice of the document.
- When a task produces a fact worth keeping, add it to the entry that owns the topic, or write a new entry and
  its index line in the same edit.
