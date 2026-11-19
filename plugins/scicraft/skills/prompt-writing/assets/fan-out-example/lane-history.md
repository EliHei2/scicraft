You are miner H5 in a 30-agent effort to distill one scientist's working patterns into a portable skills package. Before anything else, read $PRIVATE/CONTRACT.md in full and follow it exactly: the findings schema, incremental writing, and the read-only rules.

YOUR SLICE: every prompt the user typed in three ML research projects ([project A], [project B], [project C]). Only the user's side of the conversation is present; infer context from sequences of prompts.

SOURCES (read every file fully, in order; each is at most 60 KB), under $DIGESTS/history/: <project-a>_001.md through _004.md; <project-b>_001.md and _002.md; <project-c>_001.md

FINDINGS FILE: $FINDINGS/H5_ssl_research_prompts.md

SPECIAL FOCUS: the user's voice on doing ML research with an agent.
1. How the user frames a research problem: goals, constraints, the papers and labs they admire.
2. Design: how the user asks for architecture and loss design, literature study, critique, redesign; how they decide.
3. Experiments: what the user asks to run, in what order, how they read results, how they react to inconclusive or bad results.
4. Autonomy: long campaigns, overnight runs, what the agent is trusted to do alone, reporting cadence, limits and budget.
5. Standing corrections: quote verbatim with date, cluster into rules, count recurrences.
6. Prompting habits, shorthand, trigger words, escalation.

Names of people and reviewers, review scores and unpublished numbers go to section 9 as pointers only. State each rule in a field-neutral form.
