# Measuring an author's voice

A voice fingerprint is a measured card of how one author writes: rhythm, sentence architecture, connectives, the
words they never use, and their recurring sentence shapes. It is built from their own texts, so any researcher can
build theirs and any agent writing in their name can be checked against it. The method below produced a card of
35,704 words of one author's journal prose and 9,077 words of their conference prose; the measures are general.

## Contents

1. Procedure
2. Reading each measure
3. Sentence templates
4. Using the card
5. Example card (anonymized)

## 1. Procedure

1. **Collect the corpus** with `scripts/corpus_extract.py`: the author's published and submitted main texts and
   supplements, from the source (TeX), plus their solo texts. Leave out machine-drafted wrappers around their work.
2. **Split registers.** A co-edited journal paper, a solo conference paper and a book are measured apart
   (`--register name=path`). Where the registers differ, the card says which one the task at hand needs.
3. **Run the script:**

```bash
python3 scripts/voice_fingerprint.py corpus --name "Author A" --register conference=conf_paper.tex --out VOICE_PROFILE.md
```

   It strips markup, splits sentences (protecting "e.g.", "et al.", "Fig." and decimals), drops headings (a
   paragraph under 12 words with no final period), and reports every measure per 10,000 words.
4. **Read the template candidates** it prints and abstract the recurring shapes by hand (section 3).
5. **Add what a script cannot count**, by reading 20 to 30 sentences: where the main verb falls (one author put it
   inside the first eight words, with the length trailing behind), what the active voice is reserved for (the
   software, the measured object, an abstraction with a short verb of operation), how a limitation is conceded,
   how a number is stated (in apposition, with the comparator named).
6. **Write the header**: "This card measures what the author writes; it does not license it." Add every instruction
   of the author that overrides their own habit (for example a ban on mid-sentence semicolons in new text).
7. **Record gaps as gaps.** A card that invents a preference is worse than one that admits it does not know.

## 2. Reading each measure

| Measure | How to read it |
|---|---|
| length bands and median | Imitations cluster in the 15 to 22 word band. If the author's median is near 29 with p25 19 and p75 42, new text with a median of 17 is audibly not theirs, and the reverse holds for a short-sentence writer. |
| share over 45 words | Long specification sentences are a signature of some authors and a defect of others; match the document. |
| first, middle, last sentence | Where the short sentences sit. One author's topic sentence was the shortest in the paragraph (median 22 words against 31 for body sentences); results paragraphs closed short (23 % at 15 words or fewer). |
| sentences per paragraph | The paragraph unit. A median of 4 means a seven-sentence paragraph is two. |
| openers | A definite noun phrase opening more than one sentence in five, "Each" and "For each" as frequent openers, fronted adverbials rare and reserved. |
| tails | ", indicating that" turns a result into a claim; a bare appositive welds the interpretation on; a gerund tail carries a cost or a scope. |
| passive, we, I | The register split. The first person may be mandated by an institution (a book in the first person singular); land it on acts of judgement, never on what the software did. |
| punctuation | Colons decompose, semicolons separate, parentheses carry provenance ("a margin of 64 rows (twice the batch size)", invented), never asides. |
| connectives | The ranked inventory. An author who writes `rather than` 24 times per 10,000 words and `not X but Y` once in the corpus corrects with the positive first. |
| sentence-initial connectives | Often near zero. Transitions then happen by repeating the noun the last sentence ended on, or by a distributive opener. |
| zero list | Words to keep out of their text: each is something a language model reaches for by default. |
| short sentences at paragraph edges | The verdicts. A 4 to 10 word sentence at a paragraph's first or last position carries the judgement the long sentences gave evidence for. Two in a row happen at most once per section; at two per paragraph they read as a performance. |

## 3. Sentence templates

For each recurring frame, write three lines: the author's source sentence, the abstracted form with slots, and a
filled example on new content whose numbers are attested or left as `[slot]`. Never invent a number. The forms
below came from one author; the source and filled sentences are invented for this example.

| Name | Form |
|---|---|
| the reframe | `[problem] is more accurately framed as [the author's formulation] than as [the field's formulation].` |
| mechanism, restriction, payoff | `[component] [takes part in A], but [B is restricted to C], so [each unit gets the guaranteed property].` |
| result with an inference tail | `[method] [verb]ed [object] [scope], including [the surprising sub-case], indicating that [mechanism] can [capability] when [condition].` |
| the parameter bracket | `The [value] [quantity] is [what it is] rather than [what it is not]: it is large enough to [capture A], yet small enough that [failure B does not occur].` |
| the deliberate trade | `This is a deliberate trade; it is what [secures the property] but it means [method] [scope limit] rather than [the larger claim].` |
| the exclusion with its reason | `[method or dataset] was excluded from [analysis]; [reason, one clause].` |
| the criterion closer | `[property] is therefore [a distinct axis], separate from [the neighboring property] and [needed for the named use].` |
| the evaluation rule | `[quantity] is computed from [correct source], not from [tempting source], so that a method cannot [improve the score] merely by [the cheap action].` |

Filled example of the mechanism template, invented: "Padding rows take part in batching and attention, but the
loss is taken only over observed cells, so each observed value is predicted once with its full row as context."

Each template is followed or preceded by a short verdict at the paragraph's edge. Without that, an imitation reads
uniformly dense, and uniform finish is itself a machine signal: good human texts ship small slips.

## 4. Using the card

- **Before drafting** new prose in the author's name, read the card and their two or three paragraphs closest in
  kind to what you will write.
- **After drafting**, run `voice_fingerprint.py corpus --compare draft.md`. It flags: median outside the corpus
  p25 to p75, the share over 45 words, the share in the 15 to 22 band, semicolons per sentence, dashes, fronted
  adverbials, words from the zero list and sentence-initial connectives absent from the corpus. Exit status 1 at
  two or more flags.
- **The card never overrides a written instruction of the author**, and never makes a claim true: writing their
  phrase `recorded rather than imputed` about something that was imputed is worse than any style defect.

## 5. Example card (anonymized)

Numbers measured on one author's corpus; every quoted sentence is invented for this example.

**Corpus.** Journal register: 35,704 words, 973 sentences, 160 multi-sentence paragraphs. Conference register:
9,077 words, 246 sentences.

| register | <=10 w | 11-20 w | 21-35 w | 36-55 w | >55 w | median | p25 | p75 |
|---|---|---|---|---|---|---|---|---|
| journal | 6 % | 22 % | 34 % | 28 % | 9 % | 29 | 19 | 42 |
| conference | 8 % | 22 % | 38 % | 22 % | 10 % | 28 | 19 | 38 |

| position | median words | share at 15 words or fewer |
|---|---|---|
| first sentence | 22 | 28 % |
| middle sentences | 31 | 13 % |
| last sentence | 30 | 14 % |

**Openers.** `The` 218, `A` 60, `Each` 35, `For` 35, `This` 23. Fronted adverbials 9 %, used for an exception
before its rule, a regime paired with its opposite, or a distributive unit ("For each row the encoder returns one
vector.").

**Register split, per 10,000 words.**

| measure | journal | conference |
|---|---|---|
| we | 9.8 | 58.4 |
| passive | 186.8 | 58.4 |
| ", so" | 23.5 | 70.5 |
| because | 11.8 | 3.3 |
| `rather than` | 24.1 | 13.2 |
| colon | 38.9 | 90.3 |

**Connectives, journal register, per 10,000 words.** semicolon 80.7, colon 38.9, when or where 26.0, `rather than`
24.1, ", so" 23.5, ", which" 14.6, but 13.7 (mid-sentence only), while 12.0, because 11.8, therefore 8.1 (always
after the verb).

**Never used, journal register.** `Moreover`, `Furthermore`, `Additionally`, `In contrast`, `On the other hand`,
`Nevertheless`, `Hence`, sentence-initial `Thus` and `Therefore`, `Notably`, `Crucially`, `Interestingly`,
`In summary`, `In conclusion`, `In other words`, `This means`, `Note that`, `we believe`, `In order to`,
`state-of-the-art`, `novel`, `crucial`, `a wide range of`, `various`, `aims to`, `seeks to`. Sentence-initial
`However` occurs twice and `Finally` four times in the whole corpus.

**Override recorded in the header.** The author banned mid-sentence semicolons and colons in new text although
their corpus uses both heavily. A colon before a display, a table or a list stays allowed.

**Verdicts, invented examples of the shape.** "The ranking reverses on small tables." "Pretraining is the expensive
step." "We evaluate frozen transfer only."
