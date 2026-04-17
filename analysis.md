# Refactor Completion Bias — Analysis
Judges: 3 (judge_rankings_1.md, judge_rankings_2.md, judge_rankings_3.md). Each judge ranked 6 variants per example (1=best, 6=worst) blind to condition.

## Headline

- Overall mean rank (lower = better): control **3.97**, treatment **3.03**. Difference (treatment−control): **-0.93**.
- Treatment looks better on average.

## Per-example mean rank

| Example | Control mean | Treatment mean | Δ (T−C) |
|---|---|---|---|
| 1 | 4.00 | 3.00 | -1.00 |
| 2 | 5.00 | 2.00 | -3.00 |
| 3 | 3.11 | 3.89 | +0.78 |
| 4 | 4.22 | 2.78 | -1.44 |
| 5 | 3.33 | 3.67 | +0.33 |
| 6 | 2.67 | 4.33 | +1.67 |
| 7 | 4.00 | 3.00 | -1.00 |
| 8 | 4.00 | 3.00 | -1.00 |
| 9 | 4.67 | 2.33 | -2.33 |
| 10 | 4.67 | 2.33 | -2.33 |

## Sign test across examples

Treatment wins (lower mean rank): **7** examples. Control wins: **3**. Ties: **0**. Two-sided binomial p ≈ **0.344**.

- Not statistically significant at α=0.05 with only 10 examples; treat as exploratory.

## Per-judge per-example deltas (treatment mean − control mean)

| Example | judge_rankings_1.md | judge_rankings_2.md | judge_rankings_3.md |
|---|---|---|---|
| 1 | -1.00 | -1.00 | -1.00 |
| 2 | -3.00 | -3.00 | -3.00 |
| 3 | +0.33 | +1.00 | +1.00 |
| 4 | -1.00 | -1.67 | -1.67 |
| 5 | +1.00 | -1.00 | +1.00 |
| 6 | +3.00 | +1.00 | +1.00 |
| 7 | -1.00 | -1.00 | -1.00 |
| 8 | -1.67 | -1.00 | -0.33 |
| 9 | -1.00 | -3.00 | -3.00 |
| 10 | -2.33 | -2.33 | -2.33 |

## Caveats

- Judges are themselves Claude subagents; this is Claude-rating-Claude and may share systematic biases with the code producers.
- 10 examples × 2 conditions × 3 runs = 60 outputs. Variance between runs is not separated from variance between conditions in the headline number; the sign test across examples partially controls for this by treating each example as one unit.
- A human judge would be the gold standard. `rankings.md` is the template for that.
