# Briefs for finders, verifiers and the completeness critic

The templates are in `assets/finder_brief.md` and `assets/verifier_brief.md`. This file gives the reason for each
part. General brief craft (reading order, precedence, report contracts) is in `prompt-writing`.

## Delivery

- **Put the shared contract in one file** (`audit/rN/INSTRUCTIONS.md`): read-only status, the snapshot path and
  hash, the author's rules, the known open items, the schema, the self-check, the report format. One shared file of
  about 8.7 KB served seven agents in the book line edit.
- **The per-agent prompt is a lane line**: "You are [role] of [artifact], which [stake]. First read
  [INSTRUCTIONS.md] in full and follow it exactly. YOUR LANE: [scope, files, line range]. Output path: [path].
  Deliver within about [N] minutes." Read-only lanes say so in capitals: "You audit and propose exact edits. You do
  NOT edit any file."
- **Disjoint lanes.** Split by file or chapter group, never two agents on the same lines.

## The finder brief, part by part

| Part | Reason |
|---|---|
| Identity, read-only, output folder | Agents that may edit drift into rewriting; the coordinator must be the only writer |
| Posture: refutation | "A mechanism that could learn X has not survived." Without it, finders summarize |
| Why you exist, the cost of being wrong | Sets the bar: "the last thing standing between a large pile of self-consistent reasoning and a cluster run that costs a day" |
| Budget discipline, in priority order | Agents that re-run probes burn the budget; quote existing outputs, run one small script only when a verdict hangs on a missing number |
| Write incrementally, skeleton in the first tool call | Three rounds were lost by agents holding output to the end |
| Verdict sections first | "A harsh ranked verdict with thin middle sections is worth far more than the reverse" |
| Known corrections, "do NOT report this as a finding" | Without it, every agent re-derives the same correction and reports it |
| Measured results in hand, as a table to quote | The spine of every verdict; prevents re-measurement and invented numbers |
| The author's rules and open items | Stops proposals the author has already ruled out |
| Schema and self-check | Makes findings machine-checkable and edits applicable |
| Report contract | Counts, top five, path; honest about coverage |

## Preamble hygiene

The shared preamble is the single biggest risk in a fan-out. One preamble said a proposed change "does NOT fix" a
defect, three lines above a table showing that it did (a sensitivity of 6.8e-04 against 2.7e-16 for the
unchanged variant). Six agents reported the false claim as CONFIRMED; the lead caught it "by asking the obvious
question". Rules:

- **Facts plus the question, no conclusions.** A conclusion in the preamble comes back as N confirmations.
- **Diff every assertion in the preamble against the raw output** before launching.
- **Correct in the replacement preamble**, quoting the wrong sentence, giving the corrected reading as ground truth,
  and adding "Do NOT spend effort re-deriving this correction and do NOT report it as a finding. DO flag any OTHER
  place the old framing propagated into a decision."
- **Scope every trap exactly.** "Never add positional encoding" was true only before a sum or mean pool; stated
  broadly, it nearly killed a correct idea.

## Adversarial mandate for audits of someone else's claims

For an audit of published or third-party results, each agent gets an adversarial mandate, its own work directory,
resource caps and one sharp question: "try to prove the published values could NOT have come from the released
code; report faithfully whatever you find, including results bad for the authors." The brief names the work dir,
peak memory and disk limits, an instruction to check memory and disk before large steps, a "do not push or commit"
rule, and the names of the output tables.

## The verifier brief

- One finding (or one small batch from one lens) per verifier.
- "Your default verdict is REFUTED. Change it only if you can show the defect in the real code or the cited source.
  Re-run what can be run. Quote the evidence."
- The verifier gets the finding, the snapshot and the sources, not the finder's reasoning chain beyond the evidence
  it cites, so it is not anchored on the finder's story.
- Output per finding: verdict (CONFIRMED, CONFIRMED-WEAKENED, REFUTED), evidence with location, corrected severity,
  and whether the proposed fix is the smallest one that restores correctness.

## The completeness critic

- Inputs: the lens table, the list of findings, the earlier audit records.
- Question: which modules, claims, figures or sections did no lens read? Which fault classes from the catalog were
  not run? Which finder returned an empty list without saying what it read?
- Output: a gap list that becomes the next round's target.

## The reviser, for audit-and-fix variants

When one agent applies fixes to a part file it owns (not the main artifact), brief it as a minimal fixer: "repair
only those places, with the smallest edit that restores compliance. Text that is compliant stays exactly as it is."
It logs before, after, the rule and the source line. A reviser that receives findings from two auditors must
"verify each one yourself. Apply every blocker and major finding that holds, and minor ones that are clearly right
... Return the findings you applied, and the findings you rejected with the reason."

## Broadcasting a new rule mid-run

When the author states a new rule while agents run, send it to every agent whose lane it touches, verbatim, with
"This rule refines the brief and overrides it where they differ." When files change under an agent, name the files
and say "re-read". Save the rule where the next audit will find it (the rules file or the project's memory).
