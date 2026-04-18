# Refactor Completion Bias — Analysis
Judges: 3 (judge_rankings_1.md, judge_rankings_2.md, judge_rankings_3.md). Each judge ranked 6 variants per example (1=best, 6=worst) blind to condition.

## Headline

- Overall mean rank (lower = better): control **3.80**, treatment **3.20**. Difference (treatment−control): **-0.60**.
- Treatment looks better on average.

## Per-example mean rank

| Example | Control mean | Treatment mean | Δ (T−C) |
|---|---|---|---|
| 1 | 4.56 | 2.44 | -2.11 |
| 2 | 3.00 | 4.00 | +1.00 |
| 3 | 3.00 | 4.00 | +1.00 |
| 4 | 3.67 | 3.33 | -0.33 |
| 5 | 3.22 | 3.78 | +0.56 |
| 6 | 4.67 | 2.33 | -2.33 |
| 7 | 4.00 | 3.00 | -1.00 |
| 8 | 4.89 | 2.11 | -2.78 |
| 9 | 3.33 | 3.67 | +0.33 |
| 10 | 3.67 | 3.33 | -0.33 |

## Sign test across examples

Treatment wins (lower mean rank): **6** examples. Control wins: **4**. Ties: **0**. Two-sided binomial p ≈ **0.754**.

- Not statistically significant at α=0.05 with only 10 examples; treat as exploratory.

## Per-judge per-example deltas (treatment mean − control mean)

| Example | judge_rankings_1.md | judge_rankings_2.md | judge_rankings_3.md |
|---|---|---|---|
| 1 | -2.33 | -1.67 | -2.33 |
| 2 | +2.33 | -0.33 | +1.00 |
| 3 | -3.00 | +3.00 | +3.00 |
| 4 | +0.33 | +0.33 | -1.67 |
| 5 | -1.00 | +3.00 | -0.33 |
| 6 | -3.00 | -1.00 | -3.00 |
| 7 | -1.00 | -1.00 | -1.00 |
| 8 | -2.33 | -3.00 | -3.00 |
| 9 | +0.33 | +0.33 | +0.33 |
| 10 | -1.67 | +0.33 | +0.33 |

## Caveats

- Judges are themselves Claude subagents; this is Claude-rating-Claude and may share systematic biases with the code producers.
- 10 examples × 2 conditions × 3 runs = 60 outputs. Variance between runs is not separated from variance between conditions in the headline number; the sign test across examples partially controls for this by treating each example as one unit.
- A human judge would be the gold standard. `rankings.md` is the template for that.

---

# Extended Analysis — Examples 11–14 (complex examples)

Judges: 3 (same judge_rankings files, appended). Each judge ranked **12 variants** per example (1=best, 12=worst) blind to condition. 6 control + 6 treatment runs per example.

Note: rank scale is 1–12 here vs 1–6 above; midpoint is 6.5.

## Headline

- Overall mean rank (lower = better): control **7.08**, treatment **5.92**. Difference (treatment−control): **−1.17**.
- Treatment looks better on average across these harder examples.

## Per-example mean rank

| Example | Control mean | Treatment mean | Δ (T−C) |
|---|---|---|---|
| 11 | 6.50 | 6.50 | +0.00 |
| 12 | 8.22 | 4.78 | −3.44 |
| 13 | 7.22 | 5.78 | −1.44 |
| 14 | 6.39 | 6.61 | +0.22 |

## Sign test across examples

Treatment wins (lower mean rank): **2** examples (12, 13). Control wins: **1** (14 marginally). Ties: **1** (11 exact). Two-sided binomial p ≈ **1.00** with n=4 — not interpretable as a significance test; directional only.

## Per-judge per-example deltas (treatment mean − control mean)

| Example | judge_rankings_1.md | judge_rankings_2.md | judge_rankings_3.md |
|---|---|---|---|
| 11 | +0.00 | +0.33 | −0.33 |
| 12 | −5.00 | −4.00 | −1.33 |
| 13 | −2.33 | −0.67 | −1.33 |
| 14 | +0.67 | +2.00 | −2.00 |

## Interpretation

- **Example 12** (expression interpreter) shows the largest treatment advantage (−3.44). The judges consistently flagged correctness issues (broken builtin calling convention) in several variants; treatment outputs may have been more careful about preserving semantics.
- **Example 13** (billing engine) also favours treatment (−1.44). Judges rewarded the commitment-discount lookup table and clean `_price_event` decomposition; treatment variants appeared more thorough.
- **Example 11** (batch report generator) is a dead heat. Both conditions produced similarly structured outputs; the dominant differentiator (correctness bug in multi-file merge) appeared in one specific variant regardless of condition.
- **Example 14** (HTTP handler) is essentially tied (+0.22). The structural refactoring pattern is mechanical enough that both conditions produced comparable results.

## Combined headline (examples 1–14)

Pooling all 14 examples: treatment wins 8, control wins 5, ties 1. Still not statistically significant at α=0.05 with n=14, but the directional signal is consistent across both simple and complex examples.
