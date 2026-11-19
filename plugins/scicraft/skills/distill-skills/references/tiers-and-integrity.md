# Tiers, privacy, secrets, licenses, and requests that must not become rules

## Tiers

| Tier | Ships to | Gate |
|---|---|---|
| core | anyone; public repository | core terms file |
| field plugin | the field's labs; public | field terms file (allows the field's public tool, platform and gene names) |
| internal | members of the institution; a separate package in the institution's own git host | internal terms file plus `--internal` |
| personal | nobody | nothing personal is in any file; a skill that needs access details reads them from a local file the user keeps outside the package |

- **Infrastructure is internal even when it is useful.** Queue names, storage layout, group codes and
  hostnames of a cluster go to the internal plugin. The scheduler-neutral method (prepare files and
  exact commands, calibrate on one unit, pin the GPU model) goes to core.
- **Field names are not private; field results are.** A public method, platform or dataset may be
  named in a field plugin. Its numbers from unpublished work may not appear anywhere.

## Never in any tier

- names of supervisors, co-authors, reviewers and collaborators; reviewer text; review scores;
- results, benchmark numbers, claims, figure content or method details of unpublished work;
- usernames, home paths, cluster paths, group codes, hostnames, bucket names, private repository
  names, emails, keys and tokens;
- project names and internal working names (describe the work: "a segmentation benchmark", "a
  foundation-model paper");
- the author's name, except in the plugin manifest.

An incident number from debugging (a loss value, a file size, a timing) may stay when it teaches the
rule and identifies no dataset, model or paper.

## The forbidden-terms files

- **Build them from section 9 of every findings file**, plus the project, dataset and working names
  from the state file, the author's handles and machine names, and the institute's names.
- One term per line; `#` lines are comments. Matching ignores case and requires a non-letter on both
  sides, so short names do not fire inside longer words; very common first names may still need a
  judgment call (keep them if a collaborator has that name).
- **Keep the files in the private workspace.** The list itself names what must not leak.
- Institute paths and hosts are regexes in a separate file (`--internal-terms`), allowed only with
  `--internal`.
- Re-run the gate on every skill after a terms file grows. A late finding can add a name that an
  early skill already contains.

## Secrets

- The digest step redacts (`references/digests.md`). Redaction protects the miners and the
  workspace; it does not make the key safe.
- **Tell the owner to rotate every key found**: kind and date, never the value. Once when found, again
  in the final report. In the original build a miner found keys in prompts typed months before.
- Miners note any credential-like string in section 9 by place only. Writers never copy anything from
  section 9.
- Check the package's git history before first publication too: a key committed and then deleted is
  still in history.

## Third-party material

| Case | Handling in the original build |
|---|---|
| MIT-licensed skill merged | kept its license file in the skill folder and its credit in SKILL.md |
| a passage under a noncommercial license | rewritten independently from the findings, not from the passage |
| style ideas from public repositories whose license could not be verified offline | credited by name; listed as "license unverified" in the build note and `THIRD_PARTY.md` |
| a third-party skill whose examples invented facts | the method kept, the examples replaced by neutral ones |
| font files shipped with a page template | their license files kept beside them |
| the author's own skills found untracked inside a third-party clone | rescued into the package; a pull of the clone could have overwritten them |

## Requests that must not become rules

Research under deadline produces instructions that a shared skill must never teach. The flow:

1. **Miners record them** in section 10 (contradictions and changes), quoted and dated, as evidence.
2. **The lead names the guard** in the spec notes of every affected skill ("integrity guard: findings
   X and Y record requests to hide weak results; encode only the honest form").
3. **Writers encode the honest form** per the contract's integrity section:
   - choosing what to lead with is presentation; changing what the records support is misreporting;
   - a reporting threshold applies to every result alike and is stated in the document;
   - a result that contradicts a claim changes the claim; a weak or mixed result goes to the appendix
     or backup with its number, never out of the record;
   - a setting that differs from the default is reported where the result is reported;
   - emphasis by color, order or size only when the values themselves are printed or plotted to scale.
4. **The build note lists** each request and its encoded form; the final report tells the author that
   such requests were encoded in their honest form only.

Examples of the transformation (requests of this kind, not quotes):

| Request | Encoded as |
|---|---|
| hide p values above .01 that nobody asked for | print p values only below .01 for every result alike, say so in the caption, give all values in a table |
| mention ties and losses only if a reviewer asks | answer what was asked, with true and printed evidence; every omitted number remains available in the paper or appendix |
| text worded so a non-default setting is not noticed | the value actually run, stated where the result is reported |
| emphasize the method by color in a table where it is not best | color only marks values that are also printed |

The author's own material often supplies the honest form: in the original build the author's teaching
deck warned against selective reporting, and a release brief required every claim to be traceable to
a file. Cite those.

## Other things that are not rules

- **One-off decisions** with no lesson that transfers.
- **Project facts**, unless they illustrate a pattern.
- **Superseded preferences.** Latest wins. If the older rule still matters in some setting (an
  engineering job against a research campaign), name the setting.
- **Moods of the moment.** The author's appetite for fan-out size and model cost swung several times
  in a year; the rule is the latest standing one (solo unless asked; the size and model named), with
  the history as evidence.
- **Profanity.** It marks how strongly a preference is held. Record the rule; quote without it.
