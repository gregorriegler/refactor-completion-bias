# Refactor Completion Bias — Analysis (round-haiku)
Judges: 3 (judge_rankings_1.md, judge_rankings_2.md, judge_rankings_3.md). Examples: 15. Variants per example: 6. Ranks are 1=best, highest=worst, blind to condition.

## Headline

- Overall mean rank (lower = better): control **3.56**, treatment **3.44**. Difference (treatment−control): **-0.11**.
- Treatment looks better on average.

## Per-example mean rank

| Example | Control mean | Treatment mean | Δ (T−C) |
|---|---|---|---|
| 1 | 4.33 | 2.67 | -1.67 |
| 2 | 2.56 | 4.44 | +1.89 |
| 3 | 3.44 | 3.56 | +0.11 |
| 4 | 3.89 | 3.11 | -0.78 |
| 5 | 3.56 | 3.44 | -0.11 |
| 6 | 2.67 | 4.33 | +1.67 |
| 7 | 3.44 | 3.56 | +0.11 |
| 8 | 3.78 | 3.22 | -0.56 |
| 9 | 3.67 | 3.33 | -0.33 |
| 10 | 3.33 | 3.67 | +0.33 |
| 11 | 4.22 | 2.78 | -1.44 |
| 12 | 3.78 | 3.22 | -0.56 |
| 13 | 4.00 | 3.00 | -1.00 |
| 14 | 3.44 | 3.56 | +0.11 |
| 15 | 3.22 | 3.78 | +0.56 |

## Sign test across examples

Treatment wins (lower mean rank): **8** examples. Control wins: **7**. Ties: **0**. Two-sided binomial p ≈ **1.000**.

- Not statistically significant at α=0.05 with n=15 examples; treat as exploratory.

## Per-judge per-example deltas (treatment mean − control mean)

| Example | judge_rankings_1.md | judge_rankings_2.md | judge_rankings_3.md |
|---|---|---|---|
| 1 | -2.33 | -1.00 | -1.67 |
| 2 | +1.00 | +2.33 | +2.33 |
| 3 | +1.00 | -0.33 | -0.33 |
| 4 | -3.00 | -1.00 | +1.67 |
| 5 | +1.00 | -0.33 | -1.00 |
| 6 | +1.00 | +3.00 | +1.00 |
| 7 | -3.00 | +3.00 | +0.33 |
| 8 | +0.33 | -1.00 | -1.00 |
| 9 | +1.67 | -1.67 | -1.00 |
| 10 | -1.67 | +1.00 | +1.67 |
| 11 | -3.00 | -0.33 | -1.00 |
| 12 | +1.00 | -1.67 | -1.00 |
| 13 | -1.67 | -1.67 | +0.33 |
| 14 | -1.67 | +1.00 | +1.00 |
| 15 | -1.67 | +1.67 | +1.67 |

## Caveats

- If judges are Claude subagents, this is Claude-rating-Claude and may share systematic biases with the code producers.
- 15 examples × 2 conditions × runs per condition. Variance between runs is not separated from variance between conditions in the headline number; the sign test across examples partially controls for this by treating each example as one unit.
- A human judge would be the gold standard. `rankings.md` is the template for that.
