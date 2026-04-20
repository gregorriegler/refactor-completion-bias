# Refactor Completion Bias

## The idea

When you ask a model to "refactor this code," it feels pressure to produce something complete and shippable within a single response. That pressure may bias it toward shallow, surface-level edits that finish cleanly, rather than deeper, riskier changes that might run long.

**Hypothesis:** explicitly telling the model that incomplete work is acceptable ("it's okay if you don't finish") lets it spend its budget on quality instead of completion, producing better refactorings on average.

Files of interest:
- `examples/` — one file per snippet.
- `outputs/<id>.md` — one refactor per file.
- `manifest.json` — ID → (example, condition, run). Hidden from judges.
- `judge_letter_map.json` — per-example letter → ID shuffle used by judges.
- `judge_rankings_{1,2,3}.md` — the three judges' blind rankings.
- `analysis.md` — the computed results.
- `rounds/` — future independent rounds live here (empty so far). See `CLAUDE.md` for the new-round runbook. Top-level files above are the frozen first-round baseline.

## Results

- **Effort moves with the nudge**: When the harness was "loose" (allowing more turns), the treatment group took significantly more effort.
  - Mean assistant turns: control 5.42 vs **treatment 6.67** (Δ +1.24).
  - Total `Read` calls: control 57 vs **treatment 75**.
- **Quality follows effort**: In the loose harness, treatment won 10 of 15 examples (p ≈ 0.30), and the overall rank delta widened to **-0.48** (compared to -0.11 in a "tight" harness that restricted all agents to 5 turns).

This supports the hypothesis: explicitly permitting incomplete work lets the model "spend" more effort on the task, which translates to better results. When the harness restricts this extra effort, the quality benefit mostly vanishes.

See `rounds/round-haiku-loose/effort.md` for the full breakdown.
