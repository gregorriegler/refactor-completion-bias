# Round round-haiku-loose

## Purpose

Full 15 × 2 × 3 round run under the *loose* harness, as a follow-up to
`round-haiku` (tight harness). The tight round pinned every agent to 5 model
turns / 2 tool calls, which fixes effort by fiat and prevents the hypothesised
"no completion pressure → iterate deeper → better refactor" mechanism from
operating. The pilot (`round-haiku-loose-pilot`) confirmed that under a loose
harness, effort does vary by condition: treatment averaged more turns and more
`Read` calls than control, consistent with the hypothesis.

This round replicates `round-haiku` at the same scale (15 examples, 2 conditions,
3 runs/condition, 3 Haiku judges) but with the loose prompt, so that:

1. Quality ranks can be compared to the tight round.
2. Effort metrics (turns, tool calls, output tokens) can be computed with full
   statistical power instead of the pilot's n=6 per condition.

## Prompts (literal text appended after the snippet)

- **control**: `Refactor this code to your best ability`
- **treatment**: `Refactor this code to your best ability. It's ok if you don't get to finish.`

## Parameters

- Model: Haiku 4.5 for both refactor agents and judge agents.
- Harness: *loose* — see `rounds/round-haiku/_scaffold.py` `LOOSE_PROMPT_TEMPLATE`.
- Examples: all 15 files in `examples/`.
- Runs per condition per example: N = 3 → 15 × 2 × 3 = 90 refactor runs.
- Variants per example: 6 (letters A-F).
- Judging: 3 Haiku judges producing `judge_rankings_<n>.md`.

## Results

- `analysis.md` — quality ranks (produced by `python analyze.py rounds/round-haiku-loose`).
- `effort.md` — per-condition turn/tool/token aggregates plus a tight-vs-loose comparison.
