# Propose, score, judge

The loop for searching a space of configurations, prompts or designs with agents, used for an overnight
parameter search on a segmentation pipeline and transferable to any tuning job (hyperparameters of a training
recipe, thresholds of a filter, settings of a figure). Agents propose. A deterministic script scores. One
adversarial judge checks the winner for gaming. No agent ever scores its own output.

## 1. Before the first cycle

1. **The baseline is what the user already liked.** The search refines around it; it does not restart. The
   agents were told: "Stay LOCAL-ish to the champion (this is refinement, not rewrite)".
2. **The objective is a script**, with weights, hard disqualifiers and penalties written down before any
   proposal exists. The original:

   ```text
   score = 0.40 * coverage + 0.35 * enrichment_norm + 0.25 * purity_norm
   HARD:    any output object larger than 3000 units  -> score 0   (one giant merged object)
            zero outputs                              -> score 0
   PENALTY: largest object > 1500 units               -> score * 0.6
            coverage > 0.97                           -> score * 0.85 (suspiciously perfect: over-merge)
   ```

   The penalties exist because each term can be gamed: coverage by merging everything, purity by shattering
   into tiny fragments. Write the gaming route of every term next to it.
3. **The evaluator prints one parseable line** and caches its inputs so a config costs seconds:

   ```bash
   python3 eval_config.py '{"THRESHOLD_A": 0.7, "MAX_SIZE": 900}'
   # EVAL_RESULT {"score": 0.61, "coverage": 0.74, "enrichment": 1.21, "purity": 0.90, "max_size": 640}
   ```

4. **State on disk**: `state.json` holds `champion_config`, `champion_score`, `baseline_score`, `cycle`,
   `history`; every evaluation appends one line to `history.jsonl`. A crash loses at most one cycle.

## 2. One cycle

1. **Propose.** Six agents in parallel, each with a distinct hypothesis. The set that was used:
   - raise the weakest term (recall was 0.72) without tripping the over-merge penalty;
   - raise the second weakest term with tighter settings;
   - balance the two settings that trade against each other;
   - a structural idea specific to the data (elongated objects);
   - history-guided: read the top five configs in `history.jsonl` and interpolate between them;
   - wildcard: four configs at the corners of the space (one per term maximized, one balanced), each inside
     the hard guards.

   Each agent returns three or four configs as JSON containing "ONLY the keys you change", under a schema.
2. **Score.** The main session (or a plain loop) runs the evaluator on every config. Agents never run it on
   their own proposals.
3. **Judge.** One agent reads the champion and its metrics and answers one question: "is the champion
   genuinely good, or is it gaming the objective (high coverage via near-over-merge, or high purity via tiny
   dust fragments)?" It returns a one-paragraph verdict and at most one config that would fix a weakness.
4. **Promote** a new champion only if it beats the current one on the guarded objective and passes the judge.

## 3. Chaining and stopping

- Chain cycles on the completion notification of the previous one, with a timed wake-up of about 1800 s as
  fallback in case a notification is lost.
- Stop after 3 cycles without improvement or at cycle 20, whichever comes first. Then build the deliverable
  from the champion.
- Every round must change something visible. A loop whose rounds differ only cosmetically was called
  inefficient ("I don't see big changes between 1 and 3"). Save each round's output as `round_k.png` (or the
  equivalent) so the change can be checked, and have each critic name the one to three worst problems that the
  next round must fix.
- Do not let the loop run past what the user can look at: render an output early, so a cutoff still leaves
  something to see in the morning.

## 4. The workflow skeleton

Ported from the script that ran the search, with the domain stripped. It assumes a harness that provides
`phase`, `parallel`, `agent` and `log` (Claude Code's workflow scripts do). Replace every bracket.

```javascript
export const meta = {
  name: 'propose-judge',
  description: 'Agents propose configs for a scripted objective; one judge checks the champion for gaming',
  phases: [
    { title: 'Propose', detail: '[N] agents, one hypothesis each' },
    { title: 'Judge', detail: 'adversarial check of the current champion' },
  ],
}

const RUN = '[absolute path to the search folder]'
const CTX = `
SEARCH for [what is being tuned]. A config is a JSON object of overrides of these settings
(current value, direction of effect):
  [NAME_A]=[value]  ([what raising it does])
  [NAME_B]=[value]  ([what raising it does])
OBJECTIVE (maximize): [formula]. HARD: [disqualifiers]. PENALTY: [penalties].
Baseline score [value]. The champion is in ${RUN}/state.json; past evaluations are in
${RUN}/history.jsonl. Stay close to the champion (refinement, not rewrite), but a jump that
targets a named weakness is welcome.`

const HYPOTHESES = [
  { k: '[short-key]', h: '[the weakness this agent attacks and the settings it may move]' },
  { k: 'history-guided', h: 'Read history.jsonl, find the top 5 configs, propose configs between them.' },
  { k: 'wildcard', h: 'Propose 4 configs at the corners of the space, each inside the hard guards.' },
]

phase('Propose')
const proposals = (await parallel(HYPOTHESES.map((H) => () =>
  agent(CTX + '\n\nYOUR HYPOTHESIS: ' + H.h + '\n\nReturn 3 to 4 configs. Each config holds ONLY the keys you change.',
    { label: 'propose:' + H.k, phase: 'Propose', model: '[model]', schema: {
      type: 'object', additionalProperties: false,
      properties: {
        rationale: { type: 'string' },
        configs: { type: 'array', items: { type: 'object', additionalProperties: true } },
      }, required: ['configs'],
    } })))).filter(Boolean)

const allConfigs = []
for (const p of proposals) for (const c of (p.configs || [])) if (c && typeof c === 'object') allConfigs.push(c)
log('proposed ' + allConfigs.length + ' configs from ' + proposals.length + ' hypotheses')

phase('Judge')
const verdict = await agent(
  'Read ' + RUN + '/state.json (champion config, score, metrics). Is the champion genuinely good, or is it '
  + 'gaming the objective ([name the gaming route of each term])? One paragraph, and at most ONE config (JSON) '
  + 'that would fix a weakness you see.' + CTX,
  { label: 'judge-champion', phase: 'Judge', model: '[model]' })

return { allConfigs, n: allConfigs.length, judge: String(verdict).slice(0, 800) }
```

The prompts above avoid backticks inside the template literal on purpose (SKILL.md section 3). The scoring
step is outside the script: the main session runs the evaluator on `allConfigs`, updates `state.json` and
`history.jsonl`, and starts the next cycle.

The skeleton was syntax-checked only after the domain was stripped; the original ran for several cycles on
real data. The evaluator and the promotion step are yours to write for your objective.
