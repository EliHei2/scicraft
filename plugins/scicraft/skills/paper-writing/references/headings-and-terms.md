# Headings and terms

## The heading rule

**Every heading is concrete, scientific and self-contained, one idea, a noun phrase or a
declarative claim.** A reader who has not read the body knows from the title what is in it, and a
specialist recognizes the terms as the subfield's own. The test: could this title sit over a section
of a Nature Methods paper without a reviewer querying it? Length is not the constraint; a longer
title carrying technical content beats a short one carrying an image.

This rule was set after three rejected heading passes. The author's verdict on the rejected set: "no one will ever understand
this."

### Rejected headings and why

| Rejected | Shape | What would pass |
|---|---|---|
| "the hinge" | metaphor standing in for a noun | name the control: "Temperature of the retrieval softmax" |
| "Retrieval beats fitting" | slogan, riddle | "Retrieval of training rows for small tabular datasets" |
| "What comes off the instrument" | question or conversational fragment | "Raw data format of the platform" |
| "The analysis stack" | metaphor, abstraction with no object | "Preprocessing and model fitting" |
| "What a neighbour is and is not" | riddle | "Definition of the retrieval set" |
| "One tree, read four times" | riddle, invented count | name the four readouts |
| "What would prove this wrong" | question | "Falsification tests" or "Predicted failure cases" |
| "Accuracy, tested on datasets the model never saw" | comma heading, narrative | "Accuracy on held-out datasets" |
| a run-in paragraph titled "Scale." | one abstract word | "Dataset size and compute" |
| "Four index types and one distance" | invented count, a heading the author did not write | the author's own heading, unchanged |
| "the four requirements", "three symptoms", "five reductions" | invented collective noun | name the things, or drop the count |
| "Ranking checks" | coined label | "Robustness analysis" |

Accepted shapes, for calibration: a noun phrase naming the problem as the field names it ("[Problem]
as the main error source of [task]"); a list of the concrete objects a section treats ("[Object A],
[object B] and [object C] at inference"); a results claim proved by the section's figure ("[Method]
removes [defect] without losing [property]"). An ML method section that worked: "[Concept]", "[Model] encoder", "Training [concept]
with [objective]", with run-ins such as "[First component]." and "[Second component]."

### The banned shapes

1. The riddle: a title whose meaning arrives only after reading the body.
2. The question or conversational fragment ("What the encoder learns", "Why the rest needs this").
3. The metaphor standing in for a noun ("the hinge", "the gatekeeper", "the stack", "the ladder").
4. The abstraction with no object ("What the design costs", "The methods that exist").
5. The invented collective noun or count: it promises a taxonomy the field does not have.
6. The non-standard term where the field has one ("a tissue slab" where the field says "section";
   "instrument" where vendors say "platform"). Check vendor pages and the papers you cite.
7. The precise term in the wrong register: the body says "transcript-to-cell assignment", the title
   says "segmentation". A title names the problem the way the field names it; the body says
   precisely what was done.

Mechanical rules: a colon or comma in a heading is an unsplit heading (the right side is the
section's own table of contents). Three heading levels, never four (a fourth level is unnumbered
and indistinguishable; use run-in paragraph heads). Sentence case. A claim heading only where a
figure or table in that section proves exactly that claim; a section with no result takes an
activity heading ("Model assessment"), with "Towards" or "Proposed" carrying the hedge. If a title
feels abstract, add an unnumbered run-in layer beneath a plain numbered head rather than a cleverer
title. The closing part is titled as the venue's papers close ("Discussion"). Literal structure
words ("Background", "Evidence") are left out when the order already implies them.

`prose_qa.py` catches colons, question marks, question-word openers, invented counts and a fourth
level. It cannot catch a metaphor or a riddle; read every heading against the table above.

**Never re-title the author's sections.** A heading the author wrote is their voice even when a
rule above would reject it, and a heading the agent writes reads as machine-made to them even when
it passes every rule. One rebuild that replaced the author's headings was rejected whole: "the
titles were so nice and human now you made it all AI slop".

## Term discipline

**One name per concept across text, figures, tables, captions, replies, website and any label a
reader sees.** The final proofread of one paper flagged "surrounding" against "enclosing" for the
same object as a defect.

1. **Reuse before inventing.** Before introducing a term, grep the submitted text and the cited
   papers for an existing one. "If we use it before then keep exactly that terminology and don't
   introduce new ones."
2. **The field's word for shared objects, your own word only for objects you built.** Take the noun
   from the paper the sentence cites: in one audit, 12 of 15 wrong terms had the right word in a
   citation within three lines. A neighboring field's word for a different object is worse than none,
   because a reader from that field reads the wrong claim. Where the cited paper has no noun, name
   the object; do not invent a category.
3. **Define or cite every term, probe, test and statistic at first use.** One terms audit found 49
   undefined, uncited or used-before-definition terms and 17 sets of duplicate names in one paper.
   Recover true definitions from code (a probe script's header), not memory. Coined labels become
   standard terms: "detectable" becomes "significant", "arm" becomes "ablation", "ranking checks"
   becomes "robustness analysis". Every abbreviation is defined at first use, including in a
   contents title.
4. **The core concept carries its full name.** Italic at introduction, then the same words
   everywhere; never a bare short form (the author corrected a bare short form back to the full
   concept name).
5. **Human names for code names.** "instead of A3 and A4 ... make such naming human and sensible."
   Keep a glossary mapping code identifiers to paper terms, and grep the manuscript for code
   identifiers before release.
6. **Fixed order for related variants.** Define and list them in one order everywhere, baseline
   first, new second, until a rename changes the set.
7. **Choose the precise term per sentence; never a blanket swap.** When a word is banned, pick the
   right replacement for each occurrence (one banned word had six context-specific replacements).
8. **Check meaning in the paper's domain.** Avoid words that mean something else there ("index"
   in a paper about database indexes, "section" in a paper about tissue sections).

### Renaming a concept or demoting a variant

The author's words: "don't call it even the pool anymore ... as if it never existed."

1. When the author questions a term, answer with evidence: counts in the submitted text, how the
   cited papers use it, a web check of the field's usage. Offer options with the recommended one
   first and its reason. Do not defend the earlier choice. The author picks.
2. Replace everywhere: prose, captions, table rows, figure labels, legends, appendix, replies,
   website copy and any data key a reader sees. Rename LaTeX labels too, because labels carry
   retired vocabulary into every reference.
3. Add the old name to the terms file (`assets/TERMS_TEMPLATE.txt`) so `prose_qa.py --terms` fails if
   it returns, and to the Retired list of the facts file.
4. Keep the old-to-new mapping only in internal records. Map old names when reading old result
   files; never rename the records themselves.
5. Where a figure must keep an older label for now, put that label in brackets in a reply so the
   reader can find the row, and list the figure for a fix.

### Words that come from the machine

Words the author's published corpus uses zero times, found in drafts dozens of times: "symptom" (38
hits in one draft), "the field" as an actor (33), "hinge" as a noun (18), "earns" (12), "rung",
"currency", "honest", `load-bearing`. Measuring which words are the author's is `author-voice`'s
job; this skill wires the result into the gate: every row of a terms table goes into the terms
file, because a table that the gate does not grep is why "the mechanical bans read clean while the
imported register sat in the chapters".

`gatekeeper` stays off headings and out of methods and results prose (write "gate"). In an
introduction or summary the author may keep it once as a framing image when they wrote it; an agent
never introduces it. The owner of this rule is the sibling skill `author-voice`
(`author-voice/references/terminology.md`).
