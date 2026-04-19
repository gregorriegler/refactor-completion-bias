# Round round-haiku-loose-pilot

## Purpose

Small pilot testing whether the *loose* harness (self-directed iteration, no
"respond done" clamp) produces measurable effort variance between the control
and treatment wordings. The tight harness used in `round-haiku` fixed effort
at 5 model turns, 2 tool calls, 0 thinking blocks per agent — it could not
measure an effort effect even if one existed.

If this pilot shows a real difference on turns / tool calls / output tokens /
Edit-iterations between control and treatment, it justifies running the full
15 × 2 × 3 round under the loose harness. If not, the loose template needs
sharper iteration nudges before committing the full round.

## Prompts (literal text appended after the snippet)

- **control**: `Refactor this code to your best ability`
- **treatment**: `Refactor this code to your best ability. It's ok if you don't get to finish.`

## Parameters

- Model: Haiku 4.5 for both refactor agents and judge agents.
- Harness: *loose* (see `rounds/round-haiku/_scaffold.py` `LOOSE_PROMPT_TEMPLATE`).
- Examples: 11 (batch-report), 13 (billing-engine), 14 (http-handler) —
  deliberately the long/complex snippets, where the tight round already
  showed the clearest length differences.
- Runs per condition per example: N = 2 → 3 × 2 × 2 = 12 refactor runs.
- Variants per example: 4 (letters A-D).
- Judging: 3 Haiku judges producing `judge_rankings_<n>.md`.

## What to look at in results

Beyond the usual rank analysis, `effort.md` reports per-condition and
per-example token / turn / tool-call / Edit-count aggregates recovered from
the subagent session logs. Those are the numbers this pilot exists to
produce.
