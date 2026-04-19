# Round round-haiku

## Purpose

Replicate the baseline refactor-completion-bias experiment using the Haiku
model as the refactoring agent (the baseline round used Sonnet/Opus-class
agents). Question: does the "it's ok if you don't finish" nudge change the
refactoring behavior of a smaller, faster model the same way it did for the
baseline?

## Prompts (literal text appended after the snippet)

- **control**: `Refactor this code to your best ability`
- **treatment**: `Refactor this code to your best ability. It's ok if you don't get to finish.`

## Parameters

- Model: `claude-haiku-4-5-20251001` (Haiku 4.5), used for both refactor subagents and judge subagents.
- Examples: all 15 files in `examples/` (01 … 15).
- Runs per condition per example: N = 3 → 15 × 2 × 3 = 90 refactor runs.
- Judging: 3 Haiku judge subagents, each producing `judge_rankings_<n>.md`.

## Reproducibility

IDs and the per-example letter shuffle are derived from a fixed seed in
`_scaffold.py`. Refactor outputs themselves are stochastic (model sampling),
so rerunning the subagents would not reproduce `outputs/` byte-for-byte.

## Results

See `analysis.md` (produced by `python analyze.py rounds/round-haiku`).
