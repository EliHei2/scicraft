# Words

The rule, stated by the author after reading a deck written for them: "In every slide and all text you are only
allowed to use text that I have used in my previous slides or poster or paper." The source of the author's poster states the same
rule for itself: all prose is pasted from the manuscript, shortened only by cutting, and bold marks key phrases.

Why it holds for any author: a talk is given in the first person. Sentences composed by someone else, however
polished, are not how the speaker makes the argument, and they drift from it (a careful introduction became
one flat sentence, which the speaker called a reduction). Their own sentences are already approved by them.

## Contents
1. Procedure
2. Cutting, with examples
3. Dictated lines
4. Terms, numbers, names
5. Words inside pictures and clips
6. Speaker notes
7. What reads as machine-written
8. When no sentence exists

## 1. Procedure

1. Build the corpus: `corpus_extract.py build/corpus paper=<tex folder> poster=<poster.tex> book=<...> <talks folder>`.
   It reads TeX, PDF, PowerPoint and Keynote files without opening any application. Give it everything they wrote.
2. For each slide of the outline, search the corpus for the sentence that makes the slide's point (grep the corpus
   folder for the key nouns). Prefer the paper's abstract and introduction, the poster's bold captions, and titles
   of their earlier slides.
3. Paste the sentence and cut it to fit (section 2). Give its source in the builder:
   `s.head('...', 'paper, abstract')`, `s.say('...', 'poster, caption of the corpus block', ...)`.
4. Run `own_words_deck.py`. It accepts a sentence when its words occur in order as at most four uninterrupted pieces of
   one paragraph of the corpus, which is what pasting and cutting produces and paraphrasing does not.
5. Report what is not a sentence of theirs by kind: names, numbers and units, labels of data, lines they dictated.

## 2. Cutting

Allowed: deleting words, phrases and clauses; keeping one clause of a long sentence; dropping a leading connective.
Not allowed: replacing a word with a synonym, changing tense or number, merging two sentences, adding "we",
"thus", "in short", turning a statement into a question.

Original (paper): "Existing tabular models typically flatten each table into a fixed set of columns, rows, or
summary features before encoding."

| Version | Verdict |
|---|---|
| "Existing tabular models flatten each table into columns, rows." | cut: fine |
| "Models flatten each table into a fixed set before encoding." | cut, four pieces: fine |
| "Current methods squash tables into vectors first." | paraphrase: not theirs |
| "Flattening discards structure, so we do not flatten." | two sentences merged, a connective added: not theirs |

A cut must leave a true sentence. If cutting changes what is claimed (dropping "typically", dropping a condition),
choose another sentence.

Line breaks are yours: the builder breaks lines by measured width and balances them. Bind words that must not
separate (a number and its unit, a two-word term) with a no-break space (`deck.NBSP`).

## 3. Dictated lines

What the author types or dictates in the conversation for a slide is their text, and it goes on the slide as given.

- Fix what is plainly a typing or speech-to-text slip (spelling, a doubled word). Do not improve the phrasing, the
  word order or the punctuation. Rearranging a dictated sentence counted as "writing it yourself".
- Give its source as `'dictated <date>'`; `own_words_deck.py` lists such lines apart instead of searching the corpus.
- When a dictated line is ambiguous, take the most literal reading, apply it, and say in the report which reading
  you took ("I read 'research day*' as the event's name"). A wrong literal reading is corrected in one note;
  a clever one hides the question.
- When a note is a correction of wording ('is chosen' -> "should be"), change exactly those words.
- Before discarding any line as not the author's, search their typed messages in the session transcript
  (`requests_ledger.py`). In the original project three statements were removed as website copy; they were the
  author's own lines from the chat, and they asked for them again.
- A dictated line can break a general limit (an eleven-word title). Their specific line wins; the audit will name
  it and the report says so.

## 4. Terms, numbers, names

- **The work's own term** (for example "masked tabular pretraining" or "probe maps") is in italic wherever it stands: titles, body,
  band, labels inside pictures. Pass it as `key_terms` to the builder; the audit checks every occurrence. Nothing
  else is italic.
- **One name per thing.** Use the term as the paper prints it; never alternate with synonyms. Internal names
  (variants of the method, ablation arms, working labels) do not appear on slides or in notes for the audience.
- **Numbers** come from the records, rounded as the paper rounds them, each with its unit, and the real total of
  the thing named (the dataset's full count, not the sample a rendering drew). Bind number and unit. Each number
  has one rounding everywhere it appears: slides, notes, script, pictures.
- **Data stages are named.** "Pretrained on" and "evaluated on" are different claims. A sentence with "only",
  "alone" or "all" about data says which stage it covers (`check.md` section 6).
- **Spelling variety** is the paper's. Pass `--spelling american` or `british` to the audit.
- **No dashes or middle dots between phrases**, no double spaces, straight quotation marks as the paper has them.
- **Names of people** are spelled as on their institute's or lab's page, with diacritics. The author's own lists
  can carry typos; check each. Affiliations are current (someone who moved has the new one, or both). Roles are
  the author's words and nobody is promoted: a co-author is not a "supervisor".
- **The event** is named as its organizers name it. If the author corrects the name, change it everywhere: title
  slide, band, notes, script, and the names of the delivered files (the starter derives all of them from one
  constant). Tell the author that the files have new names.

## 5. Words inside pictures and clips

Labels drawn into a picture are part of the slide's text. They follow the same rule and the same sizes.

- Keep every string that is drawn into a clip or a rendered panel in one file, and give `own_words_deck.py` a JSON of
  them: `{"sourced": [...], "dictated": [...], "labels": [...]}` (`--clip-words`). Labels are names of data: types
  of the annotation, names of structures, units.
- Count the words visible at once in a clip and pass that as `words=` to `s.clip()`.
- Prefer a label the paper already uses for the thing ("expert cell-type annotations", "cosine similarity").

## 6. Speaker notes

- First `[40 s]`, then what is said: the author's sentences from the paper or poster, chosen so that the spoken
  text explains what the slide shows.
- A second paragraph in [brackets] holds your cues: what is on screen, what to say if asked, where a number comes
  from, what was chosen by eye. Brackets are skipped by the own-words check.
- Notes go to `build/notes/NN.txt` and into `TALK_SCRIPT.md`. Writing them into the .pptx is optional
  (`notes_in_file=True`): Keynote refuses to import a deck whose notes python-pptx wrote.

## 7. What reads as machine-written

Authors named these on slides. None of them survives the own-words rule, but check dictated lines and your own cues:

- two versions of one statement side by side (a question and its answer as a statement; a claim and a rephrased
  punchline under it);
- "not X but Y" contrasts, staged openers ("Here is the thing"), one-line closers;
- triads of abstract nouns, chains joined by "·" or "×", taglines over a title;
- inflated words (`unlock`, `seamless`, `powerful`, `novel`, `cutting-edge`, `paradigm`);
- a caption that restates the title in smaller type;
- hedges and filler (`it is worth noting`, `in summary`).

For anything you do compose (messages to the author, bracketed cues, a sources sheet), run the `humanizer` skill
on it. Never run it on the author's own sentences: they stay as written.

## 8. When no sentence exists

Sometimes the slide the author asked for has no sentence in the corpus. In order of preference:

1. a shorter cut of a nearby sentence;
2. a title of one of their earlier slides or a section title of the paper;
3. a line they said in this conversation about that slide;
4. ask: "Slide 9 needs one line for what the host institute gains; what would you say?" One question, with the slide named.

Never fill the gap yourself and never leave a stand-in in a delivered file: `own_words_deck.py` reports every line whose
source is `STAND-IN`.
