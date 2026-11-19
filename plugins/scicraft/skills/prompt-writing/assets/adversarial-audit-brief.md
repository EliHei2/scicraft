# Adversarial audit of [artifact], [date]

You are the adversarial phase of [the job]. Read-only on [the sources]; write ONLY into `[OUT]`.

Posture: refutation. [A mechanism that "could learn" X has not survived. A claim that "should hold" has not been
shown.] Attack, do not summarize.

## Why you exist

[What was done upstream: N documents, M agents, which all agree with each other.] [What has had no independent
review.] Being wrong here costs [a day of cluster time / a desk rejection / a public correction]. You are the last
check before that.

## Budget discipline is requirement number one

In priority order:
1. Quote existing outputs. Do not re-measure what `[records folder]` already holds.
2. Run something only if a verdict hangs on a number that does not exist: one small script, with its output
   saved next to your findings.
3. Write incrementally. Create `[OUT]/findings.md` with a section skeleton in your first tool call, then fill one
   section at a time. If you cannot write files, put the full findings in your final message.
4. Verdict sections first, details after.

## Rules that bind the artifact

Guardrails quoted from `GUARDRAILS.md`: [G<n>] "[rule text]"; [G<m>] "[rule text]". Report each one as pass, fail
or not applicable, with the line that shows it.

## Known corrections. Do NOT report these as findings.

- [The correction, stated once.] Do not spend effort re-deriving it.

## Measured results in hand (quote these)

| Quantity | Value | Source |
|---|---|---|
| [ ] | [ ] | `[file]` |

## What to attack

1. [Premise of the design or the claim, and where it is stated.]
2. [Each build item or claim: does it survive, survive weakened, or die? Does its falsifier survive?]
3. [Contradictions between documents: rule on each.]
4. [Numbers: recompute the ones the conclusions rest on.]

Out of scope: [new designs, style, items another auditor covers: name them].

## Output

One record per finding:

```
quote:     exact text attacked, with file and line
problem:   what is wrong, in one or two sentences
severity:  blocker | major | minor
evidence:  the source text or record that shows it, with page or line
fix:       exact replacement text, or DELETE
```

Final message: counts by severity, then the five most important findings (severity, file:line, problem, fix), then
the path of the full file. Under [250] words.

[For an audit-and-fix variant, add:]
You are also a minimal fixer. Repair only the places that violate [the guardrails quoted above or the rules file], with the smallest edit that
restores compliance. Text that is compliant stays exactly as it is. Log every fix as before and after, with the
rule and the source line, in `[OUT]/fixes.md`.
