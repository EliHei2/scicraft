# Build state (working file for the loop; delete when the package is done)

<!-- The lead keeps this file current so the build survives context resets and compaction. After any
reset, read this file before anything else. Update it after every launch, every finished agent and
every decision. Keep it under about 150 lines: it is an index, the detail lives in the files it names. -->

Package: [package folder] (shareable) and [internal package folder] (institute only).
Private workspace: [this folder] (digests, findings, briefs, build_notes, coverage, tools). Never ship it.
Launch prompt for any brief: "Read your full assignment at [brief] and carry it out exactly. It names the
contract to read first, your sources, the folder to create, the gate to pass and the build note to write."
Model [model]; at most [20] agents at once.

## What the user asked (in order)
1. [Each request in the user's words, numbered, dated when it came later. Every item here must end in a
   skill, a section of a skill, or a stated reason why not.]

## Mining
Done: [N first-wave miners (findings/)].
Running: [codes and one line each].
Second wave: [gap checks and late slices, with the skill each one feeds].

## Writers (briefs/W_[skill].md; generator tools/make_briefs.py; [N] briefs)
Done and gate-clean: [skill names; mark revisions: "data-figures (revision 2 after the author's visual review: done)"].
Running (as of [time]): [skill names].
QUEUE, in this order (launch as slots free): [skill names].
When launching [skill], add: [the late finding or decision that arrived after its brief was written].

## After the writers
1. Integrate late findings: [findings code] to [skill] (revision agent or message to its writer).
2. Coverage audit: one auditor per findings file (tools/coverage.py write), then aggregate, then gap-fill
   agents per skill. Items to check by name: [the user's named requests that might have fallen through].
3. License fixes: [borrowed pieces whose license forbids redistribution: rewrite independently].
4. Review: full gate; read the flagship SKILL.md files; one adversarial reviewer per skill; fix.
5. Decisions already taken from evidence: [one line each, so no writer re-litigates them].
6. Package: README, THIRD_PARTY.md, index, install test in an isolated config folder, plugin validation.
7. Portfolio numbers: [the scale script and the with/without eval, if the user wants numbers].
8. Sharing recommendation: [options and the ownership question].

## To tell the user at the end
- Secrets found in the history: [kind and date only, never the value]. Told once already: [yes or no].
  Rotate them; a redacted digest does not revoke a key.
- Integrity: requests in the history to hide or dilute weak results were encoded in their honest form only.
- License not chosen; third-party pieces in THIRD_PARTY.md.
- [Anything of theirs at risk found on the way, for example own files untracked inside a third-party clone.]
- Open questions from writers are in build_notes/*.md under "Questions for the author".
