# Refactor Completion Bias

## The idea

When you ask a model to "refactor this code," it feels pressure to produce something complete and shippable within a single response. That pressure may bias it toward shallow, surface-level edits that finish cleanly, rather than deeper, riskier changes that might run long.

**Hypothesis:** explicitly telling the model that incomplete work is acceptable ("it's okay if you don't finish — partial, high-quality work is preferred over rushed completion") lets it spend its budget on quality instead of completion, producing better refactorings on average.

## What was done

- 10 Python snippets in `examples.md`, each a textbook refactor target (if/elif chains, feature envy, magic numbers, state flags, long parameter lists, etc.).
- Two conditions per example:
  - **control** — plain "refactor this code" prompt.
  - **treatment** — same prompt plus the "it's okay if you don't finish" line.
- 3 runs per condition per example → **60 outputs** in `outputs/`, each stored under a random 4-hex ID with no hint of its condition.
- Blind ranking: 3 Claude subagent judges each ranked the 6 variants per example (1 = best, 6 = worst), seeing only anonymized letters.
- Un-blinding and stats in `analyze.py` → `analysis.md`.

Files of interest:
- `examples.md` — the 10 snippets.
- `outputs/<id>.md` — one refactor per file.
- `manifest.json` — ID → (example, condition, run). Hidden from judges.
- `judge_letter_map.json` — per-example letter → ID shuffle used by judges.
- `judge_rankings_{1,2,3}.md` — the three judges' blind rankings.
- `analysis.md` — the computed results.

## Results

Mean rank, lower = better:

| Condition | Overall mean rank |
|---|---|
| control | 3.94 |
| treatment | **3.06** |

Treatment won 7 of 10 examples (sign-test p ≈ 0.34 — not significant at n = 10, but directionally consistent).

Per-example means:

| Example | Control | Treatment | Δ (T − C) |
|---|---|---|---|
| 1 | 4.11 | 2.89 | −1.22 |
| 2 | 5.00 | 2.00 | −3.00 |
| 3 | 3.22 | 3.78 | +0.56 |
| 4 | 4.11 | 2.89 | −1.22 |
| 5 | 3.33 | 3.67 | +0.33 |
| 6 | 3.33 | 3.67 | +0.33 |
| 7 | 3.78 | 3.22 | −0.56 |
| 8 | 3.67 | 3.33 | −0.33 |
| 9 | 4.33 | 2.67 | −1.67 |
| 10 | 4.56 | 2.44 | −2.11 |

### Caveats

- The judges are themselves Claude subagents — Claude-rating-Claude risks shared stylistic biases.
- Inter-judge Spearman correlation averages +0.69, with one example (6) where one judge disagreed with the other two. Judge 1 tended to miss behavior-changing bugs that Judges 2 and 3 caught.
- 10 examples is underpowered for a significance test.

## Human spot-check

As an informal check, a human (the repo owner) was shown three blind head-to-head comparisons — one control run vs. one treatment run — without being told which was which:

| Example | Human pick | Was treatment? |
|---|---|---|
| 4 (Invoice / feature envy) | X | ✓ |
| 6 (shipping if-elif chain) | X | ✓ |
| 8 (BMI magic numbers) | X | ✓ |

Three for three in favor of treatment. Small sample, same direction as the blind judges, same direction as the hypothesis. Worth noting: on Example 6 the human also implicitly caught a correctness issue in the control variant (a silent FedEx ordering change) that the treatment variant avoided; on Example 8 the treatment pick was an API break (enum string values changed), so the human preference there was against behavior-preservation — a reminder that "looks better" and "is better" can diverge.

Overall: the effect is small, directionally real in both machine and human judgements, and well short of statistical significance at this sample size. Treat as exploratory.
