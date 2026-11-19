# The zero-defect proofread loop

The author's standard for a final package: "when you give me the thing there should be 0 discrepancy or bug or AI
pattern, so really make sure to run the agent again and again until 0 discrepancy is detected, and make the agent
really impartial, and a bit adversarial. do not fixate on AI [patterns] and focus on human psychology and reviewer
psychology". The loop below met that standard on two rebuttal packages for a machine-learning conference paper and
on a book. It works on any deliverable that strangers will judge: a paper with its replies, a camera-ready, a
release with its documentation.

## Contents
1. When to run it
2. The snapshot
3. The brief
4. Rounds
5. What the rounds found
6. Delivering while rounds still run
7. Variants for other deliverables

## 1. When to run it

- After every scripted gate passes and you have looked at the render yourself. The loop finds what a fresh reader
  sees; it does not replace your own look.
- When there are at least fifteen minutes per round. Under a harder deadline, run one round or none, deliver, and
  say so.
- One agent at a time. A fleet of proofreaders at once finds the same items several times and costs more than it
  finds; fan out only when the author asks (see `auditors.md`).

## 2. The snapshot

A fresh folder per round, so the reader sees exactly what will be sent and cannot be confused by working files:

```
proof_r2/
├── paper.pdf             the build that will be delivered
├── paper.txt             pdftotext -layout paper.pdf paper.txt, with line numbers if the venue prints them
├── replies.md            or the accompanying texts: cover letter, release notes, README
├── requests.md           the verbatim text being answered: reviews, the call, the brief, the author's notes
└── submitted.txt         the earlier version, when changes must be judged against it
```

Record a checksum of each file in the brief (`shasum -a 256 proof_r2/*`) so a finding can be tied to the version it
was made on.

## 3. The brief

`assets/proofread_brief.md` is the template. Its parts, and why each is there:

- **Who the reader is.** "An impartial, mildly adversarial proofreader. You did not write any of it and you owe the
  authors nothing. Your job is to find every discrepancy, error, gap or weak spot before the skeptical readers do."
  Then the seat it reads from: the three reviewers and the area chair; the editors; a user who installs the
  release.
- **Read-only.** "Do not edit any file. Report only." The lead applies fixes; a proofreader that edits cannot be
  checked.
- **The four passes:**
  - **A. Coverage.** Every labeled point of the request (W1, Q1, each editor's remark) has a direct answer, part
    by part.
  - **B. Pointers.** Every number, table, figure, appendix and line range cited in the accompanying text is checked
    at the cited place in the built document.
  - **C. Self-consistency.** The document against itself on the changed pages: counts against figures, captions
    against what the figure draws, main text against appendix, one name per thing, unexplained markers or symbols.
  - **D. What a human reader would hold against the authors**, and only that: a sentence they would quote in a
    reply, a claim stronger than its evidence, a promise the document does not keep.
- **Out of scope**, stated: what the authors chose to include, new experiments, framing and tone, requests for more
  disclosure, and on later rounds the items already settled ("do not re-raise the excluded items below").
- **Report shape.** Counts first, then each finding with ID, severity, the exact location (file, page, line), the
  quoted text, the problem and the exact fix. A finding without a quote and a location is dropped.
- **Confidentiality** when the material is unpublished: "work only from local files, do not use web search or web
  fetch, and do not send any of it to any external service."

## 4. Rounds

1. Round 1 on the snapshot with the full brief.
2. Read every finding yourself against the source before acting. Decline the wrong ones with a reason you could
   give the author.
3. Fix, rebuild, rerun the scripted gates, look at the changed pages.
4. Round 2 with a **new** agent on a new snapshot: "This is a second round on a corrected version, so a short
   report is fine."
5. Round 3 and later: "a confirming round; the expected report is short. Do not pad, and do not re-raise the
   excluded items below."
6. Stop when a round finds zero. If you stop earlier, the report says so: "round 2 found 15 items, all fixed; I did
   not run a confirming round. Say the word and I run it."

A small fix does not always need a new round: after the third round in the source work found six one-word last
lines, a scan of the rebuilt PDF confirmed them gone without a fourth agent. Say which way it was confirmed.

### The endgame: the author's polished draft

The loop above holds while the agent writes the text. Once the author has polished it, the rule changes:

- **One focused audit per round, on the author's polished draft.** Brief it in these words: "This is a final
  polish. Do NOT propose a rebuild, a new structure, new sections or a new style." The polished text is the base;
  the audit checks facts, pointers and slips inside it.
- **Apply the fixes and ship.** An audit still running at delivery gets one line in the report, and its findings
  are applied only if one is a factual error.
- **Why.** In the source work a swarm of five to eight adversarial readers fed a rebuild of the author's replies
  (about three to four hours, some thirteen agents, thirteen versions). The author rejected all of it ("just try to
  polish the edges ... don't drift off from that answer") and called the swarm output "super overwhelming". From
  then on the author asked for one audit, fast and short, on their own text.

## 5. What the rounds found

These are the classes of defect a fresh reader catches that the writer does not, from the source rounds:

| Round | Found |
|---|---|
| 1 (reply package) | a citation on the wrong sentence; a "full ranking" promised in the main text and absent from the appendix; a core count that did not add up; main text and appendix naming different tests; a caption not naming a dashed line; a table cited for a number it does not hold; one target with two names; an italic unit |
| 2 | fifteen items, mostly bold lead sentences claiming more than the cited lines show ("the gains are significant" while one comparator was not separated) |
| 2 (second package) | every rank recomputed from the table: one must-fix and one partially answered point |
| 3 (second package) | one grammar slip, six one-word last lines |
| fact-check gate | 0 wrong of 107 statements; 87 statements with 10 imprecise; 140 statements with 1 wrong |

A sibling gate on a book, run under a nine-minute deadline per lane, found a tense break, abbreviations used
before their definition, and a caption that said "four quadrants" where the appendix said "five sectors". One lane
returned nothing and said which file it had only pattern-searched; that honesty is what to ask for.

## 6. Delivering while rounds still run

If the author asks for the package mid-loop: give the current build at once, say it is not final and which round
is running, and send later fixes the same way. Name the files so the author always knows which is current (see
`handover.md`). Never hold a delivery hostage to the loop.

## 7. Variants for other deliverables

| Deliverable | Seat of the reader | Pass A becomes |
|---|---|---|
| rebuttal package | each reviewer and the area chair | every labeled weakness and question answered |
| book | the editors and the publisher | every formal requirement met (title page, signed statements, summaries in both languages corresponding) |
| model release | a user who installs from the README | every documented command runs as written |
| website | a stranger on a phone | every claim on the page traceable to the paper |

For a deck or a website, the loop runs on rendered pictures; give the reader the PNGs, not the source.
