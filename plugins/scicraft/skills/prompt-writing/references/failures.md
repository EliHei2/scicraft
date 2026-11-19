# What made briefs fail, and the fix

Each entry gives the failure, what it cost, and the line that now goes into briefs. They are ordered by cost.

## Content of the brief

**The rebuild nobody asked for.** The author asked for their chat-log strategy to be carried out ("essentially rerun
my commands in the md file") and added "at the end don't fixate". The session ran about 3.5 hours with four
research agents, three adversarial agents, a final gate, then five to eight more auditors. It imported a
red-label format and produced drafts v1 to v13, plus a comment to a reviewer nobody had asked about and a 24 KB
preview builder. Auditors kept reporting on stale versions while the text moved under them. The verdict: "you made
it sooo weird ... the responses I made with chat were so much better ... just try to polish the edges". The causes:
the author's last versions were treated as material and not as the base; the auditors' criteria beat the author's strategic rules; a
style was borrowed from a link given for another purpose; the scope grew. **Fix**: a polish-pass brief with the
base file named, the allowed edits listed, and "Do NOT propose a rebuild, a new structure, new sections or a new
style". The fix took 10 minutes.

**The biased preamble.** A shared preamble asserted a mechanism "does NOT fix" a known blindness three lines above a
table showing that it did. Six agents reported the assertion
as CONFIRMED. **Fix**: diff every preamble assertion against the raw output; keep preambles to facts and the
question; put known corrections in with "do not report this as a finding".

**A rule stated too broadly.** "Never add positional encoding" was written as a trap. Its true scope was "in front
of a linear pool", and the broad version nearly killed the operator's correct idea. **Fix**: write each trap with
its exact scope and keep the counter-case. Tell "deferred on cost" apart from "refuted on mechanism".

**Advice treated as rules.** Auditors argued for printing a borderline value and for one sentence the author had
banned many times in the author's notes. The lead kept both and only "flagged" them. **Fix**: a rules file pulled from every
"never", "always" and "do not" in the author's log, given to every agent as binding. The rule wins over the agent.

**Internal words in reader text.** A summary carried run names and code words ("controls", "significance",
"changed, pool"), and a release package risked carrying internal run names. **Fix**: a vocabulary block that
defines terms and a banned-words list scanned on the built output.

**Wrong facts from another chat model.** Specifications produced with an online chat carried errors about published
methods (features, weights, model outputs). **Fix**: verify every external fact before building, and label a
citation from memory as an idea to verify.

**The governing request lost.** A summary drifted toward the last few small instructions, and the author said "I
don't know why you fixate on the little things I tell you and then you completely diverge from the whole point".
**Fix**: the brief restates the document's one purpose at the top, and every draft is checked against it, not only
against the latest message.

## Output and survival

**Synthesis died.** 21 of 25 agents died on a weekly limit, and in several audits the synthesis agents died while
the evidence agents had returned. **Fix**: an output path in every brief, a skeleton file in the first tool call,
and synthesis in the lead's own loop.

**Lost to /tmp.** Output written to a temporary folder or the scratchpad was gone after a reboot. **Fix**: a trap
line in every brief ("Do not write anything you care about to /tmp"), and output paths inside the project.

**"Completed" that was not.** A workflow that died on a token limit was reported as complete: "you say it's
completed but it didn't". A background agent can also report "completed" with an empty result, which is an
artifact of token exhaustion. The opposite happens too: an agent marked failed had already written its files at
full length. **Fix**: check the declared output path; report "N of M steps finished; the rest died at X".

**Report files blocked.** In some harness versions subagents could not write report files. **Fix**: the brief
allows a fallback, the full findings in the final message, and the lead saves them.

**Reports too long.** Answers came back at a median of 95 words and up to 165 against the cap. **Fix**: the cap in
the brief, measured with `wc -w`.

## Delivery

**The old prompt ran.** A remote agent ran an earlier and broader version of its prompt. **Fix**: a version line,
one live file, superseded files renamed.

**The same request to two sessions.** Two versions came back, and the author feared their download had overwritten
the writer's version. **Fix**: one writer; the other session gets "facts only, checked against your records,
findings in <file>. Do not edit the writer's files."

**Paste failures.** A two-line rsync pasted without its backslash overwrote a 9.9 GB file, and multi-line commands
failed three more times in one day ("why man??"). **Fix**: commands as one line each, or one `bash <script>` line;
the script creates its destination folders and prints a one-line outcome ("FETCH STOPPED: the expected files were
not found (nothing downloaded)").

**An empty glob in zsh.** zsh aborts the whole command when a glob matches nothing (the `nomatch` option), so a
cleanup line with one empty pattern deleted nothing and stopped the script. It happened during a document build
on macOS, where zsh is the default shell. **Fix**: name files explicitly, run the line under bash, or quote the
pattern for a tool that expands it itself (`find . -name '*.aux' -delete`).

**Hidden coupling.** A new config key was missing from the launcher's list of keys and kept its default in every
submitted job. **Fix**: the brief names the coupling and asks the training script to echo the resolved values into
its log.

## Integrity

A weak or mixed result is stated in the brief with its number and its scope, and the receiver is told to keep it
in the record. A brief may set scope (answer what was asked, lead with the strongest true evidence, keep side
facts out) and a reporting threshold applied to every result alike.
It may not tell an agent to drop an unfavorable number from the record, and it says: "Every sentence must be true
and printed in the source of record. A weak or mixed result goes to the appendix with its number." The audits
that caught overclaims ("nothing leaks" while the appendix said otherwise) are the reason the rule holds.
