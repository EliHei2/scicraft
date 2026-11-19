# The terminology table

The author's nouns and verbs are part of their voice. Wrong words were the most frequent single complaint across
the year this skill comes from: "please use my terminology from my papers, I never used falsifiers or sth like
that"; "'instrument' no one calls it like that, look up [the vendors'] websites, and other papers, really name these
stuff liek the field does"; "you are aloud to use words/concepts/phrases only if the publicaiton has used it, of
course do not copy paste, but it's extremely important not to genate ai/slop terminology".

## Building the table

1. **Corpus**: the author's published and submitted main texts and supplements, from the source. Keep registers
   apart; a word native to one paper may be absent from another, so do not ban a word without checking which
   register the passage belongs to.
2. **Find the imported words.** For each noun, verb and coined phrase in the draft that you suspect, count it in
   the draft and in the corpus:

```bash
grep -roiw -- "TERM" drafts/ | wc -l        # hits in the draft
grep -roiw -- "TERM" corpus/ | wc -l        # hits in the author's texts
```

3. **Fill the replacement table** (`assets/terminology_template.md`): imported word, hits, files, the author's word
   instead, and a verbatim quote from the corpus that licenses it.
4. **Fill the concept table**: each concept the text names, the author's noun phrase for it, the quote. Where the
   author owns the object (their method, their dataset), their noun wins; where the field owns it, the field's noun
   wins. Take the noun from the paper the sentence cites: in one audit, 12 of 15 wrong terms had the right word in
   a citation within three lines.
5. **Fill the verb table**: each operation, the author's verb with its count, the quote. One author wrote "assign"
   409 times and "allocate" never.
6. **Note register splits and unresolved conflicts** as notes, without deciding them.
7. **Wire every row into a grep gate** and run it before each handover. Rename labels and keys too: labels carry
   retired vocabulary into every cross-reference.

## Rows that recur across authors

These words entered drafts from machine writing and appeared zero times in the measured author's corpus. Check
your author's counts before using the row.

| Imported | Write instead |
|---|---|
| honest, honestly | delete; show the candor with a mechanism ("recorded rather than imputed") |
| the field (as an actor: "the field asks") | name the actor or the record |
| earns its keep | the mechanism, with "so" or "because" |
| buys, pays for, price, currency | "at the cost of", "a deliberate trade", cost, budget |
| symptom, knot, blind spot | failure mode, with "indicating" or "reflecting" on the observable |
| gatekeeper | gate in methods, results and headings; the author's own framing line in an introduction may keep it once |
| `load-bearing` | required, decisive, or name the dependency |
| hinge (noun) | name the control (the verb is fine) |
| rung, ladder (of scales) | scale, level, granularity, or the magnitudes |
| lens | axis, view |
| movement, spine, arc (as structure) | section, stage, step |
| registered claim | delete the noun; make the claim |
| instrument (for a commercial machine) | platform, as the vendors write it |

Metaphors stand in for nouns the field already has. Headings built on them ("the hinge", "Function follows
position", "One tree, read four times") were rejected three passes in a row: "no one will
ever understand this."

## Choosing per sentence

When the author bans a word, pick the precise word for each occurrence. One banned word ("anatomical", for
objects far below organ scale) had six context-dependent replacements: spatial context, physical context,
histological regions, morphological evidence, microanatomical structures, tissue landmarks. A blanket swap would
have put a new wrong word in most places.

## Renaming

When a model variant, a readout or a concept is renamed or demoted, erase the old name everywhere, "as if it never
existed": prose, captions, table rows, figure labels, site data keys. Keep the mapping only in internal records.
Then grep for every spelling of the old name; a half-converted sweep is worse than none. A site build can assert
that the retired names do not appear.

## When the author questions a term

Answer with evidence: how the literature and the submitted text use it, with counts. Do not defend the earlier
choice. Let the author pick, then rename everywhere. One term was questioned twice on thin grounds before this was
done; the author's own pick replaced it the same night.

## Register and level

The field's headline word goes in titles, the precise term in body prose. A title says "pretraining for tabular data" where
the body says "a masked-cell objective over 4,200 tables" (invented); in a biology book, a chapter title said
"segmentation" where the body said "transcript-to-cell assignment". An abbreviation is defined at first use, including in a table of
contents.
