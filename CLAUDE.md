# Refactor Completion Bias Experiment

## Hypothesis
Telling a model "it's okay if you don't finish" may produce better refactoring than a plain refactor prompt, because the latter pressures the model toward shallow but complete edits.

## Design
- 10 Python examples in `examples/` (one file per snippet).
- 2 conditions per example:
  - **control**: plain "refactor this code" prompt.
  - **treatment**: same prompt plus "It's okay if you don't finish."
- 3 runs per condition per example.
- Total: 60 outputs.

## Files
- `examples/` — one markdown file per Python snippet (already written).
- `outputs/` — one markdown file per run, named by anonymous ID (e.g. `outputs/a1f3.md`). Contents: the refactored code and any brief notes, with no hint of which condition produced it.
- `manifest.json` — maps anonymous IDs to `(example_id, condition, run)`. Kept secret from the human judge until ranking is done.
- `judge.md` — blind judging package: per example, lists the 6 anonymous IDs in shuffled order and asks the human to rank them 1..6 (1 = best).
- `rankings.md` — the human fills in their rankings in this file.
- `analysis.md` — computed after rankings are in; reports mean rank per condition, Wilcoxon sign test per example, and overall conclusions.

## Orchestrator procedure
1. Spawn 60 subagents (10 × 2 × 3). Each receives only its snippet and its prompt — no knowledge of the experiment.
2. Collect each output, assign a random 4-hex-char ID, and write it to `outputs/<id>.md`.
3. Write `manifest.json` mapping ID → (example, condition, run).
4. Write `judge.md` with shuffled IDs per example, suitable for blind ranking.
5. Wait for the human to fill in `rankings.md`.
6. Un-blind using `manifest.json` and write `analysis.md`.
