# Campaign synthesis

What to write at the end of a campaign of runs. A log says what happened in order. A synthesis says what is
known, how well, and what to do differently.

## 1. Grade every claim by its evidence

Order the summary by grade, strongest first:

| Grade | The evidence |
|---|---|
| 1 | a paired test that was pre-registered |
| 2 | a paired test designed after the data were seen |
| 3 | a single run (n = 1) |
| 4 | an aggregate with no pairing |
| 5 | a mechanism that was measured directly |
| 6 | reasoning only |
| 7 | a judgment |
| 8 | an inference from other results |

A claim carries its grade and the path of the record behind it wherever it is stated.

## 2. One block per topic

- What we did.
- What we measured, with its grade and record path.
- Why we think it happened, labeled as a hypothesis.
- What we would do differently.

## 3. Across topics

- The five costliest operational failures, each with its cost in GPU-days.
- A review of the decisions: what pre-registration did well and what it did not. List the decisions it protected
  (a pick fixed before scores were seen, a control rerun under the frozen config) and the ones it did not reach
  (a choice made between two pre-registrations, a metric added mid-campaign). Each item names its record.
- An inventory of selection risks: every place where a choice was made after data were seen.
- "If we started over", ranked.

## 4. Contradictions and superseded claims

Close with an appendix: `| claim | status | where |`. Build it from read-only digests of the documents, checked
against the records. Where two documents disagree, the paired record wins.

## 5. How to build it

Give each helper one topic and read-only access. Each returns a digest with record paths. One writer assembles
the synthesis and checks every graded claim against its record before it is kept.
