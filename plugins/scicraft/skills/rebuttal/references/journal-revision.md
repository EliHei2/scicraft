# Journal revision

Distilled from one major revision of a computational methods paper at a journal: two reviewers, co-author
directives, a four-week plan, new datasets and comparators, reruns on a compute cluster, bug-fix pull requests and a
point-by-point letter. The templates are in `assets/journal/`.

## How it differs from a conference rebuttal

| | Conference rebuttal | Journal revision |
|---|---|---|
| time | days; text first | weeks; a phased plan with a critical path; reruns were still running three weeks after a package called itself complete |
| new experiments | only what was asked or carries the main claim | the core of the work: in the source campaign new datasets, new comparators, a new metric set, robustness perturbations, ablations, transfer, a downstream analysis, a software release |
| length | at most one platform comment per reviewer (5,000 characters there) | every comment quoted in full with a five-part block; the source letter was about 43 KB |
| opening | a general response the area chair reads in 30 seconds | a cover letter and a three-paragraph opening of the response, to Editor and Reviewers |
| manuscript | marked in one color | marked in one color, plus a clean copy; every change has a location (page and line in the tracked-changes version) |
| co-authors | a few senior readers | internal to-dos per co-author with IDs and owners, Word copies, a change summary |
| repository | rarely touched | a release: fix branches, a paper-only branch, new output folders |

Everything else in this skill holds for journals too: triage (section 1), the integrity floor, numbers and quotes
checked by script (section 7), the revision switch (section 8), polish not rebuild (section 9), the proofread loop
(section 10). The character limits and the platform table (section 5) do not apply.

## 1. From reviews to a plan

The author asked for separate documents, one per job: "make separated docs obviously for each I told you", after one
35 KB combined plan was delivered. The set, each with a date line and a Word export for co-authors who work in Word
(Markdown stays the source):

| File (assets/journal/) | Holds |
|---|---|
| `01_SUMMARY.md` | outcome, each reviewer's stance in a few lines, the consensus demands (three at most), what was built, where it stands, a bottom line honest about what remains. Written last. |
| `02_CHECKLIST.md` | every reviewer point and internal to-do with ID, class, priority, status, evidence, owner |
| `03_ACTION_PLAN.md` | phases with week ranges, steps with owner, days and a cluster flag, phase deliverables, a timeline, the critical path |
| `04_RESPONSE_LETTER.md` | the letter, drafted on day one with explicit placeholders |

Steps:
1. Convert the decision letter to text and keep each comment verbatim. Co-authors' margin notes become Part B to-dos.
2. **One ID per reviewer point, taken from the reviewer's own numbering**: `R1.1` for majors, `R1.m1` for minors,
   `R1.c1` for code and data remarks; `I.1` for internal to-dos, `ENG.1` for software changes nobody asked for. Use
   the ID in every document, branch name and figure note. The first plan in the source campaign filed reviewer 2's
   minor points under reviewer 1 and answered "Reviewer 1, Major Comment 6" with a quote that belonged to reviewer 2.
   Check every ID and every quote against the decision letter.
3. **Class each point** by the work it needs, before drafting any reply. The class decides what the letter can claim.

   | Class | Includes |
   |---|---|
   | new experiment | a new comparator, a new dataset, a rerun at new scale |
   | new analysis | on existing outputs; a figure redesign |
   | text change | Methods, Discussion, wording, a definition |
   | reply only | an argued disagreement (with a substitute experiment when one is declined), or already addressed, with its evidence |

   Then a priority (high, medium, low) and an owner.
4. **Audit the repositories against the checklist before planning.** For each ID, record the evidence as file
   paths (code, run folders, figures) and its status, keeping "configured" apart from "result available". Open
   `02_CHECKLIST.md` with a short block that says how many points are written, in hand, running and not started.
   Then sort what remains into must do, strongly recommended and writing only, each with an effort in days. These
   become the plan's steps. In the source campaign this audit was the honest package that showed most experiments
   not started (section 2).
5. **Find the consensus.** What two reviewers both demand becomes a main new figure; a single reviewer's ask becomes a
   section or a text change. The source campaign had three consensus demands: broader benchmarking, ablations,
   robustness.
6. **Plan in phases** with week ranges. Each step: what exactly, the IDs it addresses, owner, time in days, "(cluster)"
   if it needs compute. Experiments on the shared reference dataset come first. End with the critical path; the
   letter sits at its end, after the Results text:
   ```
   Reruns (1.2) --> Benchmark figure (3.1) --> Results text (3.1)
   Results text (3.1) --> Response letter (4.1) --> Submission (4.4)
   ```
7. **Decide scope in the plan first.** In the source campaign the promised scope changed across three versions in
   one day: a five-part ablation, an extra experiment and a comparator were promised, then narrowed, argued or
   dropped, while the letter followed each version. Cut scope in the plan, with its reason, and only then in the letter.

## 2. Status words are literal

**A point is never marked done before its result exists.** This is the failure the campaign records. On the day the
honest package showed most experiments not started, a second package marked every point "Completed", ticked every
box, and wrote "Completed" under every response; red internal spans carried the real state. The letter's result
placeholders were not filled; they were dissolved into general prose with no numbers and no figure references. Three
weeks later the reference-dataset rerun still lacked the method's own baseline row. The likely trigger was the
author's "make sure it's obvious what we've already done!!", read as "make everything look done".

The rule: a revision document records state; it never advocates.

| Status | Means exactly |
|---|---|
| not started | nothing exists |
| running | configured or submitted; no result file |
| result in hand | a result file exists, named in Evidence; figure and text not written |
| written | the figure or table and the text are in the manuscript, with page and line in Evidence |
| blocked (why) | cannot proceed, reason stated |
| partially done (n of m) | some units have results; the count is stated, for example 4 of 12 datasets |
| superseded (why) | replaced by another item or decision, named in Evidence |
| declined (why) | the letter argues against it or names it as future work; the checklist row points to that response |

A half-run fan-out is never rounded up to result in hand, and a dropped item is never deleted from the checklist.
The source campaign's own vocabulary had twelve states (configured, infrastructure ready and future work among
them); the eight above keep every distinction that changes what the letter may claim.

- Infrastructure never counts as a result. "Configured" is "running" at best.
- A job that exits 0 with missing rows has not succeeded. In the source campaign both rerun jobs ended "Successfully
  completed" while the coverage file showed 3 of 6 rows missing, including the method's own baseline. Read the
  coverage file, not the exit code.
- A placeholder in the letter (`[TO BE FILLED: "the sentence you expect"]`) is filled only with a number from a result
  file, or the claim is cut.
- **Every promise in the letter is checked against what was delivered before the letter goes out**: each response
  that describes a result needs a checklist row at "written". `check_letter.py` reports a response block whose row
  is not "written" as a broken promise.
- Internal flags stay in the checklist and the plan. A red "internal notifications" paragraph reached the end of one
  letter draft and its Word export; grep the letter for placeholders, color spans, "internal", "lock", owner names.

```bash
python3 <skill>/scripts/check_letter.py 04_RESPONSE_LETTER.md --checklist 02_CHECKLIST.md --internal "[owner names],lock,freeze"
python3 <skill>/scripts/check_numbers.py --claims claims.json --trace 04_RESPONSE_LETTER.md --paper revised.txt
python3 <skill>/scripts/check_replies.py 04_RESPONSE_LETTER.md --limit 1000000 --sources decision_letter.txt revised.txt
```
A file without block headers is checked as one block; here `check_replies.py` serves for the quote check and the
banned terms, and the large `--limit` turns the length check off.

## 3. The response block

Every comment gets the same five parts, praise, minor points and code remarks included:

1. **The comment, verbatim**, as a blockquote, in full, typos kept. A draft that printed bold excerpts cut with
   `[...]` was replaced by full quotes. Each reviewer's overall assessment is quoted and answered too.
2. **Response**: the argument and the result, with its number and figure. Open with "We agree." or "We fully agree."
   where true; "This is an excellent and important point" was cut.
3. **Revisions implemented**: only the concrete changes.
4. **Location in revised manuscript**: figure and supplementary numbers and page and line in the tracked-changes
   version. The source letter gave section names only ("Results (robustness analyses)"), which a reviewer cannot
   find; every location must resolve.
5. In place of the source's "Completion" line, the checklist row's evidence. A "Completion: Completed" line under
   every response was the status inflation above.

**The opening** of the letter: three short paragraphs. Thanks and the extra time taken, naming the one concern the
reviews converge on ("We agreed that the initial submission emphasized [one quality] more strongly than
[the quality the reviewers asked for]") and how the revision re-weights the paper; what changed in the software or method and what
did not (say plainly that the formulation is unchanged, where true); the expanded evaluation in a few named readouts,
each with a one-clause meaning, and the one consistent result. A headline that gave only a count of metrics in
categories ("[N] quantitative metrics in [k] categories") was replaced by a handful of named readouts: a metric count
is not a result. Close with one sentence of thanks.

## 4. Disagreeing, declining, and what could not be run

**Disagree in three moves**: acknowledge what is valid; give the methodological and the practical reason, each with
a citation; say what text changed and offer the idea as an optional extension.

> We thank the reviewer for this suggestion. We agree that [X] is compatible with [Y]. We chose not to make it the
> default, for two reasons. Methodologically, [reason] ([citation]). Practically, [cost] ([citation]). We now explain
> this in Methods p. [X] and Discussion p. [Y], and note [X] as an extension for settings where [...].

In the source campaign this answered a request for an extra model component: one methodological reason and one
cost reason, each with a citation.

**Decline an experiment by answering its intent** with a cheaper controlled experiment, and say so. A request for a
new kind of data was first declined with nothing in its place; the final response named the failure mode the reviewer
wanted isolated and added a controlled experiment on the existing inputs that isolates it, and said that this was done
to address the intent of the comment.

**Distinguish an ablation from a new model family.** Removing a component that defines the method's inductive bias
needs re-tuning to be a fair baseline; the letter said so and ablated the axes a user can change, one at a time with
data, schedule, inference and evaluation fixed. Make the letter match what is run: months later the project added
exactly the switches the letter had called a different model family. If a decision changes, change the plan and the
letter together.

**A comparator that could not be run**: say you tried, give the concrete obstacle, and state it in the manuscript.
The template block in `assets/journal/04_RESPONSE_LETTER.md` (R1.4) has the wording.

## 5. Every default and number from the code and the run records

The draft letter of the source campaign stated parameter defaults (architecture sizes, learning rate,
regularization) that contradicted both the software's own hyperparameter table and the commands that
ran; it also described a component the code did not have.

- Take each default from the `--help` or config of the exact version used, never from memory or an older document.
  A hyperparameter table generated from the code lets the Methods and the letter cite the same source.
- Take each number from a result file: record value, file and column in `claims.json` and run `check_numbers.py`.
- Take dataset statistics (size, area, density) from the provider's dataset page. The author asked
  whether a stated density was really true and whether the dataset was listed on the provider's page; the check
  found a density about ten times above the other datasets.
- Describe in Methods only what the code does; check each component claimed against the code (`paper-code-parity`).
- Check reviewer numbering and every quote against the decision letter (section 1, step 2).
- If the software version changed, say so up front, list the changes (`ENG.1`), and state that the formulation is
  unchanged where true, so engineering gains and model gains stay apart.

## 6. The revision as a project

The mechanics live in `research-code`, `project-structure` and `paper-code-parity`; what the revision adds:

- **One fix branch and pull request per bug the reruns expose**, one concern each. Scaling to the datasets the
  reviewers asked for exposed silent data loss, out-of-memory crashes on the largest inputs, empty inputs and
  missing readers; each became its own `bugfix/` branch. A guide to the set lists the invariants (each
  branch current with main, one concern), a branch tree, and one line per pull request.
- **Paper-only experiment switches on a separate branch** (`paper/<name>`), kept current with main, never merged as a
  feature by default.
- **Every rerun writes a new timestamped output folder** (`<purpose>_results_YYYYMMDD_HHMMSS/`), reads earlier
  outputs read-only, and logs a run manifest (submitted at, phase, dataset, job, resources, output root, logs,
  status) and a coverage file per dataset (dataset, method, status, reason). Build the dataset by method matrix from
  the coverage files; any missing cell blocks "compared on all datasets".
- **The aggregator prints `available n/N` for every metric** and writes the missing rows, with their reasons, to a
  diagnostics table it names in the same line ("available rows: 3/6 (see tables/diagnostics.tsv)"). A summary
  that drops missing rows silently reads as complete, and in the source campaign it did.
- Start with one reference dataset, fix every missing row's reason, then fan out.
- Fonts on the compute nodes: one rerun's error log was 600 lines of a missing figure font. Ship the font or render
  final figures locally.

## 7. Co-author summary

`01_SUMMARY.md` for the senior authors. For a software version jump, write two more things, each opening with an
old-versus-new table:

1. **A technical overview**: the problem, the data model or graph, the architecture, the losses and their schedule,
   the old-versus-new table, the optimizations with measured before and after, and a hyperparameter reference
   (parameter, command-line flag, default, range, description) generated from the code of the exact version. The
   Methods and the letter then cite the same table, which is what section 5 asks for.
2. **A short change deck**: the old-versus-new table, one slide per change with a plain note, then which version to
   use when, and the migration commands.

Leave out hype ("Killer Feature", "The Big Shift") and claims without a test ("significantly boosting
sensitivity"). The source overview carried all three, against the plain style the author asks for everywhere else.

## 8. A note to the editor

The source campaign addressed one letter to "Editor and Reviewers" and wrote no separate note about a reviewer. When
one is needed, the order of `references/chair-note.md` is the evidence available (Suggested, not yet tested in real
work for a journal).
