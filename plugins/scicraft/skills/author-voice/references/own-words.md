# Own words: display copy from the author's sentences

Display copy is any text that states the author's work in their name for readers who will not read the paper:
slides, a poster, a project page, a talk caption, a program abstract, the bold title of a figure. The rule is the
one the author applied to their own poster: pasted from the manuscript, shortened only by cutting.

## Why the rule is absolute

The incident that set it: a talk deck written in the agent's words, with one slide framing the work as "analysis
starts by drawing cells". The author called it a reduction of the problem and sent: "In every slide and all text
you are only allowed to use text that I have used in my previous slides or poster or paper text." The same week,
a reply rebuilt by agents "really killed my whole points". The author's sentences carry the argument the way they
make it; a paraphrase moves the emphasis even when every fact survives, and the author sees it at once.

## Procedure

1. **Build the corpus** (`scripts/corpus_extract.py`): paper sources, poster source, book, earlier decks, site
   copy they wrote, and a `dictated.txt` with lines they gave in the conversation, one per line.
2. **Choose before writing.** For each slot (a title, a line under it, a caption), search the corpus for the
   sentence that already says it. Titles come from section titles, bold captions, abstract sentences and earlier
   slide titles; for a talk, a title is one full sentence of at most 10 words.
3. **Cut, never add.** Remove clauses, appositives, citations and parentheses until the sentence fits. Remove a
   connective that dangles once the sentence leaves its paragraph ("Therefore", "In contrast", a leading "This").
   Keep the order of the words that remain.
4. **Record the source** of every line (file and paragraph, or "dictated").
5. **Run the check:**

```bash
python3 scripts/own_words.py COPY.md --corpus corpus --dictated dictated.txt
```

6. **Report by kind**: sentences found (with the source file), dictated lines, labels and numbers (not checked as
   sentences), and every sentence not found. Each problem is either replaced by a sentence of the author or named
   in the report with the reason it stays.

## The piece rule

`own_words.py` normalizes case, punctuation and British or American spelling, then asks whether the words of the
sentence occur, in order, as at most 4 uninterrupted pieces of one paragraph of the corpus (`--pieces` changes the
limit). Four pieces allow three cuts inside one sentence. Examples, with the corpus sentence "Missing cells are
dropped from the set, so the model never sees an imputed value":

| Display line | Pieces | Verdict |
|---|---|---|
| Missing cells are dropped from the set, so the model never sees an imputed value. | 1 | pasted |
| Missing cells are dropped, so the model never sees an imputed value. | 2 | cut, passes |
| The model never sees an imputed value because missing cells are dropped. | none | reordered, fails |
| Missing values are removed, so nothing is imputed. | none | paraphrase, fails |

Two sentences of one paragraph joined into one display line pass only if the joined words stay in order and within
four pieces; two sentences from different paragraphs never pass. That is intended: a merge is writing.

## Lines that are not sentences

A line of at most three words without a final period (a name, a unit, an axis label) and a number with its unit
("4,200 public tables") are counted apart and not checked as sentences. Names of people and labels of data are not
the author's prose, but they are still checked by eye: spelling as on the person's institute page, labels as in the
paper.

## Dictated lines

A line the author typed or said in the conversation is theirs. Keep it word for word, including its order. Speech
to text introduces errors (a place name heard as a phrase, a product name split in two); decode from context and
list every guess in the report so the author can correct it.

## When there is no corpus

On a round of notes on copy you did not build, the author's texts may not be at hand. Run `own_words.py` without
`--corpus`: it lists every sentence as unchecked. Say in the report that the own-words rule was not checked, and
ask for the sources.

## Display rules that came with it

- **One point per unit** (a slide, a panel, a section of a page), stated once.
- **No tagline** over a title, no result claim at the top of a page, no "A × B × C" chains, no middle dots, pipes
  or slashes between phrases. A site tagline built that way was called "cringe and vague and too AI slop".
- **Labels say what the number counts**, with the unit beside it.
- **Less is more**: "very selectively say sth, and when you say it should be best thing to say".
- **Every displayed number has a record behind it**, and a quoted sentence that is no longer the paper's (after a
  revision) is replaced from the new version.

## Integrity

Choosing which of the author's sentences to show is presentation. A count chosen so that its remainder disappears
is not. When a count invites the question about the rest ("the method wins on seven of nine datasets",
invented), find the author's sentence that is true of all items, or show the whole count; the per-item
numbers stay in the paper's table. Never cut a sentence so that it claims more than it did whole: cutting "on
wide tables" from "the lead is largest on wide tables" changes the claim.
