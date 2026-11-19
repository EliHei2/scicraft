# The paragraph loop: title, draft one, three rounds, then the next

The author's instruction, after three rejected passes on one chapter: "generate one paragraph by one
paragraph, then audit it as a Nature editor asking if this is AI or really each sentence have unique
piece of info delivering". Never draft a whole section and audit it afterwards. "A defect that
survives into paragraph five has been imitated four times."

```
0 TITLE    one declarative sentence per paragraph, all of them, in the narrative block
           needs "and"            -> two paragraphs
           no title writable      -> the paragraph does not exist
           two share a title      -> one paragraph
           delete test: if the argument still holds without it, it goes
1 DRAFT    one paragraph, never two
2 ROUND 1  smooth      T7
3 ROUND 2  clear       T1, T4, T6
4 ROUND 3  scientific  T2, T3, T5
5 NEXT     only now
```

**The order of the rounds is part of the method.** Round 3 is the one most often used as a
substitute for the other two, and a paragraph can be flawless in register while carrying no
argument. A paragraph that fails round 1 cannot be judged for clarity, because the reader is still
assembling the order. Before drafting, read one page of the register target (the author's own best
methods or results text).

## The tests

**T0. A paragraph exists because one message can title it.** "each paragraph exists because it could
be titled with one unique message, very clear message, that if not expressed the story would not be
as good." Write the title. Delete the paragraph in your head: if a later paragraph becomes
unsupported, name what; that dependency is its reason to exist. Kill the orphan: a one-sentence
framing paragraph becomes the first sentence of the paragraph it introduces (four shipped in one
chapter; none could be titled).

**Paragraph architecture.** A paragraph runs topic, support, generalization, payoff, in 4 to 7
sentences and, in motivating prose, under about 140 words. It carries one finding per system, one
number pair, one generalization and one payoff. A second instance of the same phenomenon gets one
sentence and no numbers: "Two evidenced instances is not twice as convincing, it is twice as long."

**Merge short neighbors after the rounds.** When every paragraph of a section has passed, read them
in a row. Two neighbors of three sentences or fewer that carry one message become one paragraph,
whose title is still one sentence. A chapter of many short paragraphs reads as a list of notes; the
author, on a finished chapter: "we have so many small paragraphs, could you merge neighboring ones".

**T1. Every sentence carries a fact no other sentence carries.** A number, a threshold, a named
method or tool, a mechanism, a decision, a limit or a falsifiable claim. A sentence carrying none is
deleted, not rewritten. Two sentences carrying one fact: delete one, do not merge. "Jibber jabber"
in the author's usage is "a sentence whose fact is already carried by its neighbour".
Fails: "Three properties of this design matter for the argument." (names no property)

**T2. The subject of each sentence is a thing that exists.** The measured object, the method, the
data, the software, or the author. The tell is an abstract noun with a verb of agency: *bounds,
closes, fixes, governs, renders, carries the weight, does the work, is what makes*.

| Fails | Passes |
|---|---|
| "That last property bounds the class of question this benchmark can address." | "The benchmark holds no dataset above 50,000 rows, so it cannot test scaling." |
| "Each control closes a route by which leakage reaches the score." | "Duplicate rows were removed at three stages." |

De-slop passes breed their own tic here: short transitive verbs on inanimate subjects (one corpus
showed *decides* at 117 times its reference rate). Repair by restructuring, never by swapping in
another verb of the same shape.

**T3. No sentence describes the document.** No "This section reports", "The strongest evidence here
is", "will discuss", "is organized as". One roadmap sentence per paper (or per chapter) and one
handoff sentence are allowed. A pointer carries the finding: "Section 5 presents X, a model that
does Y".

**T4. Every quantity is present, scoped to the register.** In a results or methods passage, if a
threshold, rank or count exists in the source, it is in the sentence.

| Fails | Passes |
|---|---|
| "with a temperature controlling sharpness" | "with temperature 0.07, as in the released code" |
| "a large index" | "an index of 2.1 million rows" |

In motivating prose (abstract, introduction) a number stays only when it is the argument. Applying
the results rule to an introduction produced 26.6 numerals per 1,000 words, "a review article with
a [claim] attached". The rule is symmetric: deleting an argument-carrying number is also a defect.

**T5. The register is the field's best papers, not a technology blog.** No product register
(`unlocks`, `enables` as a flourish, `powerful`, `leverages`, "the key to"), no consultancy
abstractions ("the class of question", "a set of properties"), no slogan closers. The closer states
what is now established and stops.

**T6. The heading names its content.** `references/headings-and-terms.md`.

**T7. Every sentence lays the floor for the one after it.** The author's rule: "every sentence should
set floor the one after it." Write the paragraph as a numbered list; beside each sentence, write the
question a reader now holds. A gap is a question nothing answers. A mismatch is an answer to a
question nobody asked. Bridges are short, state a fact and carry no citation. Order is not free:
"Same sentences, different order, and only one of them is a chain."

## The output of an audit

One table per paragraph. A paragraph failing any test is rewritten and audited again, not patched.

| # | Sentence opens | Fact carried | Verdict |
|---|---|---|---|
| 1 | "On the 40-dataset benchmark, retrieval..." | 0.84 against 0.81 | pass |
| 2 | "This is a strong result that..." | none | T1 fail, delete |
| 3 | "The gain holds on 31 of..." | 31 of 40, 9 where baseline ahead | pass |

## Worked example (illustrative numbers)

Draft:

<!-- voice-lint: off -->
> Retrieval is an increasingly important paradigm in tabular learning. In order to assess its value,
> we conducted comprehensive experiments. Notably, our method achieves strong performance: it reaches
> 0.84 accuracy. This demonstrates the power of retrieval.

Audit: sentence 1 carries no fact (T1, delete). Sentence 2 describes the work and uses filler (T1,
T3, delete). Sentence 3 has a filler opener, a mid-sentence colon, an evaluative adjective, and a
number with no comparator (T4: "meaningless" in the author's word). Sentence 4 is a slogan (T5).

After:

> On the 40-dataset benchmark, retrieval over training rows reaches 0.84 mean accuracy against 0.81
> for the gradient-boosted baseline (Table 1). The gain holds on 31 of the 40 datasets. It is largest
> below 1,000 training rows and absent above 50,000, where the baseline sees enough data to fit the
> same decision boundaries.

Three sentences, three facts, each raising the question the next answers (where? how often? when
not?), and the closer states a mechanism and stops.

## The cut pass

A separate pass with one success criterion: a shorter text that has lost no fact, number, citation
or claim.

- Target 15 to 25 percent fewer words on a first draft, fact set unchanged. A pass that lengthens has
  failed.
- Never add a fact or a citation in a cut pass. A density pass that inserted a bare number into an
  abstract is what produced "meaningless"; "the repair for a thin sentence is usually a mechanism,
  not a decimal".
- The four cuts that recover the most: throat-clearing, over-justification (justify once, where a
  reader would be surprised), duplicate scaffolding ("as described above", "recall that"),
  abstraction stacks (`a principled representational learning framework` becomes "a
  representation").
- Zero repeated caveats. "A caveat repeated stops being a caveat and becomes a mood." The second
  occurrence becomes a cross-reference.
- No section ends with a recap paragraph. If the recap carried the claim, the claim becomes the
  heading (one chapter had 11 recap paragraphs, 5.5 percent of its words).
- Terse is not clipped. Compress by stacking noun phrases without restatement, never by three-word
  sentences. Compaction by agents once produced 112 broken sentences that four audits then repaired.
  After any length pass, check that every sentence reads on its own.
- Fronted method participles appear when one-fact-per-sentence, method-plus-result-plus-citation and
  a falling word budget are pushed at once: "Running the benchmark at 1,000 features, only 93 columns
  were shared" (the columns did not run anything). Repair in order: the study as subject with two
  finite verbs; the finding as subject with a by-phrase; two sentences. The convention participle
  the reader performs ("Writing Σ for the covariance, ...") is exempt.
- Three related constructions go the same way. A `which` that refers to a whole clause becomes a
  new sentence with a named subject. Bold on method names inside body sentences is removed, because
  it "turns a paragraph into a catalog entry". Inanimate possessives (measured at 5.4 times the
  reference rate in one book) become "of" phrases or compounds: "the profile of the cell", "the
  cell profile".
