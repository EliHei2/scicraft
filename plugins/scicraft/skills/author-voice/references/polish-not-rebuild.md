# Polish, never rebuild

## The incidents

Five rejections of the same kind, each costing a working session or more.

1. **The rebuilt reply.** The author had worked out a reply over 37 chat turns and asked the agent to understand
   the strategy in the log, add a few points and "not fixate". The agent spent about three and a half hours with
   research, adversarial and audit agents, an imported format, drafts v1 to v13, an unrequested comment to a third
   party and a 24 KB preview page. The text kept moving while auditors reported on stale versions. Rejected in
   full: "the responses I made with chat were so much better ... really killed my whole points ... just try to
   polish the edges ... what you did is super overwhelming." Within ten minutes the agent rebuilt both texts as
   light polishes of the last chat version, and from then on each turn integrated one or two of the author's
   points into the accepted text.
   What went wrong, as recorded: the last versions were treated as material, auditors' preferences beat the
   author's written rules, a style was borrowed from a link given for another purpose, the scope crept, and the
   author's key points were buried.
2. **The rewritten chapters.** "Update against the new versions" and "rewrite like a human" were read as a license
   to restructure: new chapter files, new headings, twelve humanizing editors. "You really butchered my beautiful
   text, the titles were so nice and human now you made it all AI slop, go back to the previous version and just
   update the technical details." Restored byte for byte from a snapshot.
3. **The drifting round.** A later round replaced 37 to 90 % of the author's sentences, measured with a sentence
   drift tool. The next instruction: "your understanding of text is not very good, so don't generate more ... do
   simple small surgeries."
4. **The merged file.** Asked to place a supplied file and "apply our aesthetics", the agent merged 9,786 words
   onto the house style. "I told you to literally copy-paste the latest final v2 file."
5. **The paraphrased papers.** "I gave you literally papers that you could just paraphrase and you butchered
   them."

## Procedure: polishing from a chat log or a draft

1. **Find the last version.** In a chat log, the last turn the author wrote or accepted (in the first incident,
   turn 34 of 37). In a repository, the committed file; diff the author's rewrites against the committed file, not
   against an older `*_revised` draft.
2. **Snapshot** the base (`cp -r chapters _snapshots/r4_<date>/`) and give the path in the first message.
3. **Copy the author's rules** (every never, always and do not from their notes and the log) into a rules file and
   read it before each change.
4. **List the deliverables** and keep to them.
5. **Apply only named fixes and real errors**: typos and grammar, points the author asked to add, cuts to fit a
   hard limit, corrections of fact. Each change is one sentence, logged old to new with its reason and, for a fact,
   the source quote.
6. **Before anything wider than a sentence, show the plan at the level of the outline and stop.**
7. **Run the gate**: `scripts/drift_gate.py` against the snapshot, with the numbers the author asked to change in
   `--allow-numbers`.
8. **Return the change list in a few lines**, the snapshot path, and numbered questions only the author can
   answer.

## Allowed and not allowed

| Allowed without asking | Ask first | Never |
|---|---|---|
| fixing a typo, a wrong number, a broken pointer | moving a paragraph | re-titling the author's sections |
| adding a point the author named | merging or splitting sections | rewording to improve |
| cutting to meet a hard page or character limit (moves and whole-sentence deletions) | a new section | adopting an outside template |
| replacing a retired value with the new one | a humanizing pass on a named file | an editor fan-out the author did not ask for |

## Intake of text written outside the session

When the author hands over a text written elsewhere (their own rewrite, a co-author's draft, another tool's
version they liked):

1. **Paste it byte for byte.**
2. **Make only mechanical edits**: citation keys that break the build or duplicate an existing work, float
   environments if a figure plan was given. No sentence added, moved or rewritten, including around a float.
3. **Measure it against the last accepted version**: words, sections, paragraphs, median and longest paragraph,
   mean and p90 sentence length, citations, numerals and bold per 1,000 words, first person. Any row closer to a
   rejected version than to the accepted one is a regression to report.
4. **Check numbers against the fact base** and keys by title and author.
5. **Write a header comment listing what the text does not yet carry**, one line per deviation, recorded and not
   fixed.
6. **Hand it back and say so once.** A package is never adopted or refused whole; each row is decided on its own.

A clean build and a supplied self-audit are not evidence about the text. One incoming package reported a successful
compile and zero undefined citations, and measured at 2.03 times the accepted length with 28 absent citation keys.

## Version updates

When the science under a text changes (a new manuscript version, new numbers):

1. Convert the new version to text and write a delta: old value to new value, removed results ("gone, do not
   use"), placeholder passages ("nothing from that paragraph may be quoted").
2. Keep one authority file for every number, with a retired-numbers list to delete on sight.
3. Apply old to new inside the author's sentences, listed per file. When the science under a passage changed
   enough that the sentences are wrong, rewrite the technical sentences inside the author's skeleton and touch the
   narrative one sentence at a time.
4. Conflicts among the author's own sources are not averaged and not picked silently: use the manuscript value
   where one exists, otherwise mark it for the author.

## Endgame

When the author says "finalize", deliver the artifact first. "No adverserial reauditing just the fixes. go." Report
any audit still running in one line and apply its findings only if it reports a factual error.
