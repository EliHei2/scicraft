# The note to the area chair or editor

Written when one reviewer's rating cannot be reconciled with the reviewer's own written assessment, or rests on a
request outside the venue's scope. Private (readers: area chairs and program chairs). It took about 15 versions to
reach the form below; versions were rejected as "weak and whiny and aggressive", "too weak now, as if it's just ask
for one raise in score", and "the AC had way better evidence before and now it's just words".

## Register

- From higher ground: "more general, stronger, more confident", "calm and confident tone", "first build evidence of
  our work plus [the reviewer's] contradictions, then [their] new point".
- Human and helpful: "really human and sympathetic, not arrogant, come from position of help".
- Firm and brief: "you don't have to be too nice". Blunt sentences belong here and nowhere public.
- "leave no trace of not success": the note states results; it does not plead.

## Order

The author's final note, which was the target form:

1. Thanks and the request for attention. "We fully respect the reviewer's right to ask questions." The follow-up
   "names no gap and asks for no concrete evidence", and "its text does not match its score".
2. One sentence placing the rating against the other reviews.
3. Two block quotes of the reviewer's most positive sentences, short and exact, key phrases in bold (say that the
   emphasis is added, or do not add it).
4. One sentence: the rating now rests on a new request outside the venue's scope.
5. A table: original concern, the revision with line numbers, the reviewer's own words after the rebuttal.
6. One bold paragraph of the global results with line numbers.
7. Where the reviewer's statements tell only part of a result: three points at most, the reviewer's phrase in red
   beside the full result in dark green, one with a small table.
8. The venue's criterion, quoted verbatim from the official reviewer guideline, and "We would gladly provide
   evidence on any concrete point".
9. The other reviewers' positive words.
10. One request: "engage with the reviewer and request reconsideration, or otherwise weigh the rating against the
    reviewer's written assessment and the venue's criteria".

A shorter form that was accepted earlier as "way better": the result first ([where the paper stands, and how many
reviewers recommend acceptance]), then "We write about one matter that bears on how the reviews are
weighed", the contradiction in one sentence, the quotes, the concern table, the bold result, the red and green table
at the end ("don't make the table a simple decoration rather a work of art"), the criterion paragraph and the
request.

## The red and green device

```
Three statements of the follow-up tell only part of these results (reviewer in red, full result in green).

| | |
|---|---|
| $\color{red}{\textsf{"[reviewer's phrase]"}}$ | $\color{darkgreen}{\textsf{[the full result]}}$ (lines [[TOKEN]]) |
```

- Say outright that these are the reviewer's statements and that the contradiction is between their statements and
  the results the paper reports.
- Write "tell only part of these results", never "do not match": the reviewer's numbers came from the paper's own
  tables, and a chair who checks would see that.
- Keep each colored phrase short; MathJax boxes do not wrap.

## Quoting the venue's criteria

- Fetch the current guideline page and quote one sentence exactly. The sentence that helped: "this does not
  necessarily require state-of-the-art results", followed by one sentence stating where the paper stands all the
  same.
- Quote it only to the chair. In a public reply the same sentence sounds as if the paper does not win.
- Describe the reviewer's demand in the reviewer's own examples. A summary of the demand that went beyond the
  reviewer's words was called a strawman by an audit and was rewritten in the reviewer's terms.
- "Not a criterion of the venue" was wrong when significance is one; the heading became "not required by the venue".
- A request outside the venue's scope is named as such, without heat ("[The venue] is a venue for [its field]. It is
  not a [other field] journal."), and paired with the offer of evidence.

## Phrases

Used: "We would like to draw your attention to", "We fully respect the reviewer's right to ask questions", "names
no gap and asks for no concrete evidence", "its text does not match its score", "We kindly ask whether you could
engage with the reviewer", "We would simply appreciate it if you could have a look at this thread before the
discussion period ends".

Struck: "In short" (banned in the note on the last day; it may still open an answer in reply prose if the author
writes it), "outlier", "isolated", "moved", "new request" as a label, "unfair", "inconsistent reviewer", "we never claimed to be
best on every task", a second request, a self-title or headings over obvious content.

## Checks before sending

- Every quote verbatim (`check_replies.py --sources` with the follow-up, the original reviews, the paper text and
  the guideline text).
- Every phrase that characterizes the reviews survives the chair checking it. A relayed draft summary described the
  other ratings more favorably than the platform showed them; an audit found six such phrases and they were dropped.
- No sentence undoes an audit fix: an unprinted p value cited to an appendix, "addressed all initial concerns" two
  lines above the reviewer's own "several", emphasis added to quotes without saying so. When the author's own final
  text reintroduces one, list it with its cost in characters and let the author decide.
- Under the limit; quotes and tables kept, prose cut.

## To a journal editor

The journal campaign in the source material addressed one letter to "Editor and Reviewers" and wrote no separate
note about a reviewer, so there is no journal evidence for this note. Suggested, not yet tested in real work: the
same order fits a paragraph of the cover letter, with the request "we would be grateful if you could weigh this
report against the reviewer's own assessment and the journal's criteria".
