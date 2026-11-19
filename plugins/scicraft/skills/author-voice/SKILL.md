---
name: author-voice
description: Writes and edits text that goes out under a named author (their paper draft, abstract, slides, poster, site copy, reply or message) so that it stays theirs. Use it whenever someone asks to polish, fix, shorten, update, humanize or reuse their own text, to turn a paper into display copy, to write a paragraph or a note in their voice, or complains "this is not how I write", "you butchered my text", "this reads as AI", "go back to my version", even when the skill is not named. Holds the two meta-rules (display copy is the author's sentences shortened only by cutting; polish their latest version, never rebuild it), a script that measures an author's voice from their own corpus, an own-words checker, a drift and numeric gate, the terminology table, the edit ledger, the contract for agents that touch an author's prose, and the form of short messages to senior colleagues. For de-slopping your own drafts use humanizer; for a reviewer reply use rebuttal; for building the deck use talk-slides.
---

# author-voice

How to write and edit text that goes out under someone else's name so that they recognize it as theirs. Distilled
from a year of one researcher's work with an agent on papers, a book, conference replies, a poster, a talk and a
project site. The costliest failures in that year were all of one kind: text that was correct, fluent and rejected
whole because the author did not write it. Every rule below comes from one of those rejections. Where the author
at hand says otherwise, they win: record their rule in the edit ledger (section 6) and follow it.

> **PRIME DIRECTIVE: text in an author's name is built from that author's own sentences, starting from their
> latest version, and changed only where it is wrong or where they asked.**

The failures that cost the most time. Guard against them from the first minute:

1. **Writing for the author.** Text composed for someone reads as machine-made to them however well it is edited.
   A talk deck written in the agent's words was thrown out with "you are only allowed to use text that I have
   used" (section 2).
2. **Rebuilding when asked to polish.** A three-hour rebuild of a reply the author had worked out over 37 chat
   turns, by eight agents in a new format, was rejected in full: "just try to polish the edges". A wholesale
   rewrite of book chapters with new headings and twelve humanizing editors was restored byte for byte from a
   snapshot the same day (section 3).
3. **Losing a correction.** Corrections that lived only in the conversation were made again, and rejected again, chapters later. "A rule
   learned at chapter 11 that is not applied to chapters 1 to 10 will be re-learned at chapter 12" (section 6).
4. **Letting agents loose on the prose.** One round of agent editing replaced 37 to 90 % of the author's
   sentences, measured against a snapshot; paraphrase agents doubled chapter lengths (section 7).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The author's own texts**: paper sources (TeX preferred), poster source, book, earlier decks, site copy, and
  lines they dictated in the conversation. These are the only source of words for display copy and the corpus for
  measuring their voice (section 1).
- **The latest version** of the text at hand. In a chat log it is the last turn the author wrote or accepted, not
  the first. In a repository it is the committed file, not an older `*_revised` draft. Read the last version
  before anything else.
- **Their written rules**: every "never", "always" and "do not" from their notes, memory files and earlier
  sessions, copied into one rules file. These are hard constraints. Advice from an audit or another agent never
  overrides them.
- **Their governing brief**, if they wrote one. It overrides earlier rules; keep a decisions log against it.
- **The deliverables**, named. Work only on those. An extra item is offered in one line, never built.

Then decide which kind of job this is, because each has its own rules:

| The request | The job | Section |
|---|---|---|
| slides, poster, site, abstract or captions made from their paper | paste and cut their sentences | 2 |
| "polish", "fix", "shorten", "update to the new numbers", "make it more human" on their text | polish their latest version | 3 |
| a new paragraph, reply or message that does not exist yet | write to their measured voice and terms | 4, 5 |
| they rewrote something you wrote | diff, write the rule, propagate it | 6 |
| several files, or any helper agent | the contract for agents | 7 |
| a short message to a supervisor or senior colleague | the message form | 8 |

Under a deadline the order holds: deliver the artifact first, then audits. "But first finalize the pdf and give
it to me" was said while the agent was still auditing.

## 1. The corpus

Everything below reads the same corpus: a folder with one `.txt` per source the author wrote or accepted.

```bash
python3 scripts/corpus_extract.py corpus paper=paper/tex poster=poster/poster.tex book=book.pdf talks/ --unwrap rev,new
```

It reads `.tex`, `.docx`, `.pdf` (PyMuPDF), `.pptx` (python-pptx), Keynote `.key`, `.md` and `.txt`, without
opening any application. `label=PATH` sets the prefix of the corpus file, which `own_words.py` uses to prefer the
paper and the poster.

- **Only text the author wrote or accepted goes in.** Machine-drafted notes and summaries about their work carry
  the register the corpus exists to keep out. In one project the author's main text had 2 em dashes in 225 lines;
  the agent-written briefs around it had 135 in 738.
- **Keep registers apart.** A journal paper edited by many co-authors, a solo conference paper and a book are
  different voices of one person. One author's journal register was three times more passive than their
  conference register and used "we" six times less often. Measure each with its own corpus.
- **A co-edited manuscript is weaker evidence than a solo text.** Editors and co-authors put in words the author
  rejected elsewhere. Prefer the author's solo writing as the voice reference.
- **The newest text and instruction win** over older ones when they disagree.

## 2. Display copy: their sentences, shortened only by cutting

This covers slides, posters, project sites, talk captions, abstracts for a program and figure titles: any text
whose job is to state their work in their name. The author of the original work stated the rule for their own
poster: "All prose and math are pasted from the manuscript (main text and appendix), shortened only by cutting."

- **Paste their sentence and cut.** Do not paraphrase, merge two sentences, add a connective or reorder. Even
  reordering a dictated sentence counts as writing it.
- **Titles come from their section titles, bold captions, abstract sentences and earlier slide titles.**
- **Emphasis is a bold key phrase inside their sentence**, never a new line written to carry the point.
- **Strip a connective that dangles** once the sentence leaves its paragraph ("Therefore", "This"), and nothing
  else.
- **Lines they dictated in the conversation go in as given**, recorded as dictated. People who dictate produce
  speech-to-text errors; decode them from context and list each guess in the report.
- **Read an ambiguous note literally** and say in the report how you read it.
- **Every number on display matches the records** and its source is written down.
- **Less is more.** No tagline over a title, no result claim at the top of a page, no "A × B × C" chains and no
  middle dots between phrases. A label says what its number counts, with the unit beside it ("12 of 12 datasets",
  not "12/12").
- **Check every sentence by script** and report what is not theirs by kind (names, numbers, data labels, dictated
  lines). A sentence passes when its words occur in order as at most 4 uninterrupted pieces of one paragraph of
  the corpus:

```bash
python3 scripts/own_words.py site/index.html poster/text.md --corpus corpus --dictated dictated.txt
```

Without the author's texts at hand, run it without `--corpus`: it lists every sentence as unchecked, and the
report must say so. `references/own-words.md` has the procedure, the piece rule and worked examples.

**Choosing what to lead with is presentation; dropping a result is misreporting.** Display copy may lead with the
strongest result and leave the weakest for the paper. It may not state a count in a way that hides a contrary
result, and it may not imply more than the records hold. When a count such as "the method wins on seven of
nine datasets" (invented) invites the question about the other two, write a sentence true of all nine instead ("The
method matches or beats the baseline on all nine datasets and is significantly better on seven"), with the
per-item numbers kept in the table.

## 3. Polish, never rebuild

"Make it better", "polish", "humanize", "update against the new version" and "make it shorter" all mean the
narrowest reading: small changes inside the author's latest text. The rejected alternatives cost hours each time.

- **Start from the latest version.** Find the last turn they wrote or accepted, or the committed file, and use it
  as the base file. The rejected rebuild treated the author's last chat versions as material for a new text.
- **Snapshot before touching anything**, and give the snapshot path in the first report, not the last. A copy taken
  before a rewrite made the restore byte-exact.
- **Change only what you can justify** as an error, a fact, a pointer, a hard limit (a page or character cap) or
  an explicit order. "Please change only if you must ... not for bettering it because you cant." Never change a
  sentence to improve it.
- **Make one-sentence surgeries and log each one**: file, old, new, and the source quote for a factual change.
  Keep the log as an ordered list of old to new pairs, each matching exactly once, applied to the snapshot by
  `scripts/apply_layer.py`; deleting an entry and re-applying restores the original.
- **Show the plan and stop before any change wider than one sentence.** A restructure, a re-title, a merge or a
  split is the author's decision alone.
- **Never re-title their sections.** "A heading [they] wrote is [their] voice even when a craft document would reject it,
  and a heading I write reads as machine-made to [them] even when it passes every rule."
- **Text the author supplies is placed, never improved.** Asked to put a supplied file into a chapter "and apply
  our aesthetics", an agent merged a 9,786-word file onto the house style and produced "a chapter [they] did not write
  and had not asked for". Paste it, fix only build-breaking keys, record any deviation in a header, and say so
  once. If following an instruction means rewriting more than moving, the instruction has been misread: ask.
- **A new version of the science means fact updates inside their sentences**: old value to new value, listed per
  file. Never new headings, a new spine or an editor fan-out.
- **A length budget is met by moving and deleting whole blocks**, never by rewording: floats and procedural
  paragraphs move verbatim to an appendix, restated caveats and recaps are deleted.
- **Keep their roughness.** Their final texts carry live slips and constructions a ban list would flag. Fix the
  typos they would fix; do not bend their constructions toward a style rule unless they ask. This rule is inferred
  from two sources and has not been tested against the author directly.
- **Do not borrow an outside template.** A public reply template linked "for the preview page" was applied to the
  reply itself and rejected: "keep our previous style".
- **If you think a rebuild is needed, say so in one line and wait.**

Report in a few lines: what changed (old to new), why, the snapshot path, and the numbered questions only the
author can answer. `references/polish-not-rebuild.md` has the incidents, the procedure for polishing from a chat
log, and the intake of text written outside the session.

## 4. Measure the voice

When new prose in the author's name cannot be avoided (a new paragraph, a reply, a section they have not written),
write it to their measured voice. Imitating from memory fails in a predictable way: uniform 15 to 22 word sentences,
discourse markers they never use, and a finish with no roughness.

```bash
python3 scripts/voice_fingerprint.py corpus --name "Author A" --out VOICE_PROFILE.md
python3 scripts/voice_fingerprint.py corpus --register solo=book.tex --out VOICE_PROFILE.md
python3 scripts/voice_fingerprint.py corpus --compare new_paragraph.md
```

The profile reports, per register, with rates per 10,000 words so corpora of any size compare:

| Measure | What it tells you |
|---|---|
| sentence-length bands (<=10, 11 to 20, 21 to 35, 36 to 55, >55 words), median, p25, p75, share over 45 | the rhythm; one measured author wrote a 30 to 50 word specification sentence plus a 4 to 10 word verdict at paragraph edges, and only 22 % in the 11 to 20 band |
| first, middle and last sentence of each paragraph: median length, share at 15 words or fewer | where the short sentences go |
| top sentence openers, share fronted by an adverbial | how sentences start; one author fronted 9 % and only for an exception, a paired regime or "For each" |
| tails (", indicating that", ", which", other ", -ing" tails) | where the length of a long sentence sits |
| passive, we, I | which voice carries what |
| semicolon, colon, dash, parentheses, question mark | punctuation as syntax |
| connectives, mid-sentence and sentence-initial | how sentences link; one author had zero "Moreover", "Furthermore", "Additionally" and "Notably" in 35,704 words |
| zero list | words and frames the author never uses |
| template candidates | real sentences carrying each recurring frame, to abstract into templates by hand |

- **Abstract templates by hand**: the source sentence, the form with slots, and a filled example whose numbers are
  attested or left as a slot. Never invent a number.
- **The profile describes; it does not license.** One author's corpus ran 80.7 semicolons per 10,000 words, and the
  same author banned mid-sentence semicolons and colons in new text. Their latest instruction wins over their
  corpus.
- **Match the cadence of the document you add to.** A harsh audit of revision text found a median of 29 words per
  sentence, 24 % over 45 words and 0.39 semicolons per sentence, against 17, 1 % and 0.03 in the submitted paper
  it was added to: "Cadence is the loudest giveaway." `--compare` prints these measures for a draft and flags
  each one outside the corpus range.
- **Small corpora are noisy.** The script warns under 30 sentences. Suggested, not yet tested in real work: treat
  rates from under about 5,000 words as indications only.

`references/voice-fingerprint.md` has the full procedure, how to read each measure, the template format and an
anonymized example profile.

## 5. The terminology table

The author's words are part of their voice, and wrong words were the most frequent single complaint: "please use
my terminology from my papers, I never used falsifiers or sth like that".

- **Mine the author's vocabulary with counts.** For each term your draft imports, record its hits in the draft,
  its count in their corpus, their word for the same thing, and a verbatim quote that licenses it. Columns:
  `Imported | Hits | Files | Their term instead | Quote`. Add a concept table (concept, their noun phrase, quote) and a
  verb table (operation, their verb with its count; one author wrote "assign" 409 times and "allocate" 0).
- **Reuse an existing term before inventing one.** Check the literature and the author's submitted text first.
  Never coin a term or a metaphor; a coined heading word was answered "no one will ever understand this".
- **One name per thing, everywhere**: text, figures, tables, replies, site, data keys readers see.
- **When a variant is renamed, erase the old name everywhere**, "as if it never existed". Keep the mapping only in
  internal records, and grep for every variant afterwards.
- **Choose the replacement per sentence.** When a word is banned, pick the precise word for each occurrence; a
  blanket swap with one replacement puts a new wrong word in half the places.
- **Match the term to the register**: the field's headline word in a title, the precise term in body prose. Take
  the noun from the paper the sentence cites, and check vendor pages for hardware names.
- **When the author questions a term, answer with evidence and let them pick.** Do not defend the earlier choice.
- **Wire every row into a grep gate.** A table that no check reads does nothing: in one project the gate grepped
  none of 30 rows, and the imported words sat in the chapters while the mechanical bans read clean.

`references/terminology.md` has the build procedure and the rows that recur across authors; the empty table is
`assets/terminology_template.md`.

## 6. The edit ledger

When the author rewrites or rejects something, the correction is worth more than the sentence. Write it down
before drafting anything else.

1. **Diff** their version against yours at sentence level (`git diff --word-diff`, or save yours as `before.md`
   and diff).
2. **Classify** every change: FACT, CLAIM, STRUCTURE, WORD, SYNTAX, CUT, HEDGE.
3. **Generalize**: find two more places the rule applies. Otherwise log it as local; three local fixes of the
   same shape are a rule nobody spotted.
4. **Write the entry** in `assets/edit_ledger_template.md`: trigger in their words, before, after, what it
   generalizes to (often a grep), how many instances were found and fixed, and where the durable rule now lives.
5. **Propagate backwards**: grep the whole document, fix every instance, record the counts.
6. **Promote** durable rules into the governing style file. "The ledger is the log; the craft documents are the
  law."

Do not thank and move on, do not fix only their sentence, and do not smooth their wording toward yours: "If [their]
replacement reads less fluent to me, my ear is wrong." `references/edit-ledger.md` has the classes, the signal
words and what each one means, and worked entries.

## 7. Agents that touch an author's prose

Any helper agent, script or fan-out that edits the author's text works under a written contract. The contract
that ended a run of rejected rewrites is `assets/agent_contract_template.md`:

- **No fan-out over the author's prose without asking.** Each editor fan-out was stopped by the author ("don't run
  another set of ... agents"). If they agree, it is on a named file, under this contract.
- **Snapshot first**, and tell every agent the snapshot is the restore point. Agents killed by usage limits
  mid-edit left half-edited files four times; the snapshots made recovery possible.
- **The author's text is the baseline, and drift is gated**: at least 80 % of their sentences same or near and at
  most 10 % lost, each lost sentence logged with its reason. One chapter went from 40 % lost to 1 % under this
  gate, a discussion from 90 % to 8 %.
- **Word caps come with a drift floor.** Caps alone made agents cut the author's own sentences: one chapter's
  kept-verbatim share fell from 73 % to 46 %.
- **Numbers, labels and citations are invariants.** The multiset of numeric tokens is unchanged except the updates
  asked for; label and citation sets are unchanged in both directions; a trim adds no sentence and no number.
- **Expected size changes.** A cut pass removes 15 to 25 % of words with the fact set unchanged. A de-slop pass on
  a manuscript grows it 3 to 5 %; if it shrank, facts were lost.
- **Audits propose; one writer applies.** Brief auditors: "This is a final polish. Do NOT propose a rebuild, a new
  structure, new sections or a new style." Check every proposed edit against the rules file; the rule wins.
- **Give voice its own pass.** Machine sentences survived three proofreading rounds that checked facts and
  references only, and the author caught them. Read the final text yourself, top to bottom, as a reader.
- **Relay the author's mid-task instructions to running agents verbatim**, with what changes for that file, and
  stop agents whose work is stale.
- **Agents return numbered questions for the author** instead of guesses.

```bash
python3 scripts/apply_layer.py _snapshots/r3/intro.tex edits/intro.json chapters/intro.tex
python3 scripts/drift_gate.py _snapshots/r3/chapters chapters --allow-numbers 0.84,0.86
```

`drift_gate.py` classes every snapshot sentence as same, near, edited or lost, lists the lost ones, diffs the
numbers, and fails when an author's heading changed. `references/agent-contract.md` has the full contract, the
audit brief and the relay format.

## 8. Short messages to senior colleagues

A message to a supervisor, a professor or a collaborator's lab head is in the author's voice and reads like a
person wrote it.

- **Short first-person paragraphs that tell the plan and where it leads**: what happens when, what comes after, the
  idea, the strategic point, one number where it matters.
- **Then at most three plain questions.**
- **No headings, no lettered options, no cost tables, no furniture metaphors** ("where it lives"). A draft with five
  headed points and a) b) options reads as machine-made.
- **Use the author's own images**, followed by what they concretely mean.
- **Kindly and briefly.** Ask plainly for the one thing needed, and carry the evidence; a soft or complaining note
  does not get it.
- **Check the word count before showing it.** One draft was cut from 505 to about 450 words.
- **Decode dictation** and flag each guess.

`references/messages.md` has the form with an example. For replies to reviewers and notes to an area chair use the
`rebuttal` skill.

## 9. Check before anything is handed over

In this order:

1. `own_words.py` on all display copy: zero problems, or each one named with its kind in the report.
2. `drift_gate.py` against the snapshot for any edit of the author's text: pass, with every lost sentence and
   every changed number accounted for.
3. `voice_fingerprint.py --compare` on every passage you wrote: no flag left unexplained.
4. The terminology greps and the greps from the edit ledger: zero hits, or each hit judged.
5. **Read the whole text yourself, top to bottom, as the reader.** Scripts and slice readers miss sentences about
   the document itself, logic that does not follow, and machine cadence inside correct facts.
6. Trace the deliverables: exactly those asked for, nothing extra.
7. Say what was not checked: no corpus at hand, a format the scripts could not read, a number without a record.

## 10. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| display copy written for the author | "you are only allowed to use text that I have used" | their sentences, cut, checked by script |
| a three-hour, eight-agent rebuild of a worked-out reply | "just try to polish the edges" | the last chat version, polished in ten minutes |
| rewritten chapters with new headings | "you really butchered my beautiful text, the titles were so nice and human" | byte-exact restore, fact updates only |
| rewording to improve | "not for bettering it because you cant" | changes justified as error, fact, pointer, limit or order |
| invented headings | "AI slop", "no one will ever understand this" | the author's headings, kept |
| a supplied file merged onto the house style | "I told you to literally copy-paste" | the file pasted, deviations noted in a header |
| an editor fan-out over the prose | "don't run another set of ... agents" | in-thread surgeries under a drift gate |
| words from outside the author's corpus | "I never used falsifiers or sth like that" | the terminology table, wired into a gate |
| "anatomical" swapped in everywhere | "choose your words very very wisely" | the precise word per sentence |
| an old variant name kept in places | "as if it never existed" | one name, swept everywhere |
| corrections kept in the chat | (re-rejected chapters later) | the edit ledger, propagated backwards |
| a message to a senior colleague with headed points and options | "make this message more human" | short first-person paragraphs, three questions |
| a site tagline with "×" and "·" | "cringe and vague" | no tagline, no separators |
| an outside template applied to the wrong artifact | "keep our previous style" | the narrow use they named |
| uniform 15 to 22 word sentences in added text | "Cadence is the loudest giveaway" | the measured cadence of the document |

## Reference files

- `references/own-words.md`: the paste-and-cut procedure, the piece rule, dictated lines, reporting by kind.
- `references/polish-not-rebuild.md`: the incidents, polishing from a chat log, intake of supplied text, version updates.
- `references/voice-fingerprint.md`: measuring a voice step by step, reading each measure, templates, an anonymized example.
- `references/terminology.md`: building the table from the corpus, recurring rows, rename sweeps.
- `references/edit-ledger.md`: the diff and classify procedure, signal words, worked entries.
- `references/agent-contract.md`: the contract, the drift and numeric gates, audit briefs, relays.
- `references/messages.md`: short messages to senior colleagues.
- `assets/edit_ledger_template.md`, `assets/terminology_template.md`, `assets/agent_contract_template.md`: files to copy into the project.
- `scripts/corpus_extract.py`, `scripts/own_words.py`, `scripts/voice_fingerprint.py`, `scripts/drift_gate.py`,
  `scripts/apply_layer.py`: Python 3.9 or later, standard library; PyMuPDF for PDFs and python-pptx for PowerPoint, only when such a file is read.
