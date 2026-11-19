You are building one skill of **{package}**, a package of Claude Code skills that carries {mission} Turn the evidence for your skill into a finished, tested skill folder.

## Read first, in this order

1. `{contract}`: the contract. Follow all of it.
2. `{model_skill}`: the model for structure and voice (prime directive, failures to fear, numbered sections, check section, thrown-out table, references split by concern).
3. Your sources, listed below. A findings file has ten sections: 2 the author's words, 3 rules, 4 procedures, 5 failure to fix, 6 assets to ship, 7 vocabulary, 8 candidate skills, 9 sensitive items (never copy), 10 contradictions (latest wins).

## Your skill: `{name}` (plugin `{plugin}`)

**Folder to create:** `{folder}`

**Scope.** {scope}

**It must contain.** {must}

**Primary sources (read fully):**
{primary}

**Secondary sources (read the named parts; use Grep on the tag or rule number):**
{secondary}

**Existing material to port (read it, copy what works, strip what is project-specific):**
{existing}

**Decisions already made.** {notes}

## Rules of the job

- **Evidence only.** Every rule traces to a finding or to existing material. Keep the numbers. Where the evidence is thin, write less. Your own additions are allowed only where a gap would stop a user, each marked "Suggested, not yet tested in real work".
- **Depth.** The author's standard: "{standard}". A rule without its number, command or reason is not finished. Put the working detail in references/ and keep SKILL.md under 500 lines.
- **Field-neutral.** State the general rule first. The lead example is one {lead_reader} meets, unless your skill is in a field or internal plugin.
- **Private strings.** No people, no reviewer text or scores, no unpublished numbers, no project or working names, no usernames, paths, hosts or keys. The gate enforces a list of forbidden terms.
- **Integrity.** Contract section on integrity. Some findings record requests to hide or dilute weak results and say so in their section 10. Encode the honest form only.
- **Port real code.** When a file in the author's repositories or skills does the job, copy it into the skill, strip the residue, parameterize it and run it. Do not rewrite working code from memory. Everything outside your skill folder and your build note is read-only.
- **Run what you ship.** Run each script with `--help` and on a small input you create. Compile each template if the tool is installed. If something cannot be run here, the skill and the build note say so. No installs into the system Python; a virtual environment in a temp folder is fine.
- **Evals.** Two or three cases under `evals/`, in the format the contract gives. Copy the settings block and grader block from `{eval_model}`.
- **Sibling skills** (refer to them by these names; do not repeat their content): {siblings}
- **Gate.** Run until clean:
  `{gate}`
  Fix every error. Read every warning and fix it or justify it in the build note.
- **Build note.** Write `{build_note}`: sources used; what was generalized; what was left out and why; third-party material with its license status; what was run and on what input; what is untested; questions for the author.
- Do not edit any other skill, the contract, the tools, the user's own configuration folder, or the source repositories.

Your final message, at most 150 words: the files the skill contains, the gate result, what is untested, questions for the author.
