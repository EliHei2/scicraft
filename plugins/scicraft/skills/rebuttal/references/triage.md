# Triage: what goes into a reply

## The asked-for matrix

Step 0 of any reply is the reviews, verbatim, in `reviews.md`. Label every point (W1, W2 for weaknesses, Q1, Q2 for
questions, or the platform's own labels) and keep the label beside the reviewer's sentence.

Then build one table per reviewer:

| Label | The reviewer's words (verbatim) | What they ask for | Answer from | Where it goes |
|---|---|---|---|---|
| W1 | "[the reviewer's sentence]" | [what they ask for] | [the result that answers it], Table 1 | reply R1, general bullet 1 |
| Q2 | "[How do results change with donors held out?]" | a held-out split | appendix table, lines | reply R1 |

Every paragraph of every draft maps to a row of a matrix or to the paper's main claim. Anything unmapped goes. Run
this lean pass on every draft; in the source work one pass cut the answers from 5,300 to 4,700 words.

Things the lean pass removed, each with the reason it failed:
- **Unasked corrections.** State the right fact in the paper, quietly. Announcing "we corrected X" opens a question
  about everything else.
- **Development-time readings and sequential looks.** Give the pre-declared endpoint only.
- **Weaker variants of your own method** and controls that only show limits, unless asked.
- **Provenance notes that cast doubt without carrying a claim.** Where provenance matters to a claim, it stays in
  the paper.
- **Unasked concessions**: "on par with", "only", "essentially". An asked-about tie is stated once, as a plain
  declarative ("level with").
- **Tangents.** A sentence on a side analysis of the query position answered no one and drew a demand for a
  full audit of the responses.
- **Caveat chains and intervals in the reply.** State the effect and its direction; the intervals, fold counts and
  test stay in the appendix.

## Organize around the one question

For a method paper the question is "is the method effective?". Before adding a table, figure or answer, name the
effectiveness claim it supports. Keep limits short and in one place (a scope line), never spread through the text.

## Claims ledger

For each sentence the author wants to say, record a verdict with its evidence:

| Wanted sentence | Verdict | Evidence | Wording that holds |
|---|---|---|---|
| "definitely better" | narrowed | [what the records do and do not show] | [the wording the records support] |
| "superiority in k of n tasks" | false as worded | k of n counts method-task comparisons, not tasks | "k of n paired comparisons" |

Say "goes further than the records" once, give the wording that holds, and do not re-litigate a settled boundary.

## Counts that reveal failure

A count with a remainder invites the remainder. Sweep every draft for "of the", "N of them", "except", "all but"
(`check_replies.py` lists them as warnings) and decide each:

| Draft | Problem | Honest form |
|---|---|---|
| "All N ablations lower the score, M of them significantly" | invites "so the rest not" | "All N lower the combined score, and each significantly lowers at least one task"; per-ablation table in the appendix |
| "significantly above k of the n comparators" | used where the reviewer asked about magnitude | the effect size the reviewer asked about; the k of n stays in the paper |
| "w of t tests" | a denominator of all tests run | "w significant gains and l significant losses", with the test family named in the paper |

Keep "k of n" when it is the claim itself (a bold lead where significance was the question). Every version must be
true, and the full count must be printed in the paper.

## The integrity floor in practice

The source work contains requests to drop or dilute weak results that no reviewer asked about. The package keeps
the presentation craft and the safeguards, never the concealment:

- **Asked for, weak result.** Report it, once, in a plain sentence beside what holds ("Without the largest task,
  the method keeps the best mean rank. On that task alone it ranks fourth."). Give the standing that answers the
  reviewer's question (mean rank, rating, a pooled test stated with its family) and keep the full table in the
  appendix. In the source work a table with a low placing, on the very point a reviewer raised, was found the night
  before the deadline and called "a clear fatal thing". The form this package teaches: the reply leads with the
  aggregate statistics that hold and answers the point, and the full table stays in the appendix.
- **Not asked for, weak result.** It stays out of the reply. It stays in the records, and if it bears on a claim the
  paper makes, in the appendix with its number.
- **Contradicts a claim.** The claim changes. A selector verdict never overrides this.
- **Post hoc decisions** (a task moved out of the headline after results were seen) are stated in the paper where
  the result is reported, with the rule, the date relative to the results and that it applies to every method.
- **Inclusion rules for rows** (which checkpoints, which comparators) are written into the paper's methods, applied
  to every method alike. A rule that drops only the rows that beat your method is not allowed.
- **A juxtaposition is a claim.** A true overlap fact placed right after "all but one competitor" read as the reason
  that competitor was not separated, and contradicted the paper's own "draw no conclusion". It was moved.

## Prepared answers

Keep `NOTES.md` (private, never posted): each known weak spot, the true answer with its number and line, and the
reviewer most likely to raise it. In the source work a ready answer was kept for a known weak spot of one
pooled test.

## Simulated reviews

When the author pastes simulated reviews (written by a language model) before the real ones arrive, triage them in
three tiers: (1) answers from existing records, (2) experiment specifications for the most likely points, in
reviewer priority, (3) items reserved for the author and never written into a document. When the real reviews
arrive, retire the anticipated answers and answer only the real points, keeping every table and figure built
meanwhile as evidence.

## Before answering a critique, find out which draft the critic read

A colleague cited "table 6" and "table 9" from a draft three versions old. Archive each full version
(`reply_v1_full_<date>/`); when a comment cites numbers, map them against the version the commenter saw.
