# Refactor Completion Bias — Analysis (round-haiku-loose)
Judges: 3 (judge_rankings_1.md, judge_rankings_2.md, judge_rankings_3.md). Examples: 15. Variants per example: 6. Ranks are 1=best, highest=worst, blind to condition.

## Headline

- Overall mean rank (lower = better): control **3.74**, treatment **3.26**. Difference (treatment−control): **-0.48**.
- Treatment looks better on average.

## Per-example mean rank

| Example | Control mean | Treatment mean | Δ (T−C) |
|---|---|---|---|
| 1 | 4.00 | 3.00 | -1.00 |
| 2 | 3.44 | 3.56 | +0.11 |
| 3 | 4.56 | 2.44 | -2.11 |
| 4 | 4.11 | 2.89 | -1.22 |
| 5 | 2.78 | 4.22 | +1.44 |
| 6 | 2.89 | 4.11 | +1.22 |
| 7 | 4.00 | 3.00 | -1.00 |
| 8 | 3.67 | 3.33 | -0.33 |
| 9 | 4.00 | 3.00 | -1.00 |
| 10 | 3.44 | 3.56 | +0.11 |
| 11 | 3.00 | 4.00 | +1.00 |
| 12 | 3.78 | 3.22 | -0.56 |
| 13 | 4.33 | 2.67 | -1.67 |
| 14 | 4.00 | 3.00 | -1.00 |
| 15 | 4.11 | 2.89 | -1.22 |

## Sign test across examples

Treatment wins (lower mean rank): **10** examples. Control wins: **5**. Ties: **0**. Two-sided binomial p ≈ **0.302**.

- Not statistically significant at α=0.05 with n=15 examples; treat as exploratory.

## Per-judge per-example deltas (treatment mean − control mean)

| Example | judge_rankings_1.md | judge_rankings_2.md | judge_rankings_3.md |
|---|---|---|---|
| 1 | -1.00 | -1.67 | -0.33 |
| 2 | +0.33 | -1.00 | +1.00 |
| 3 | -3.00 | -0.33 | -3.00 |
| 4 | -1.00 | -1.67 | -1.00 |
| 5 | +2.33 | +1.67 | +0.33 |
| 6 | -0.33 | +2.33 | +1.67 |
| 7 | -0.33 | -1.00 | -1.67 |
| 8 | -0.33 | +1.00 | -1.67 |
| 9 | -0.33 | -0.33 | -2.33 |
| 10 | +1.67 | -0.33 | -1.00 |
| 11 | +3.00 | -1.00 | +1.00 |
| 12 | -1.00 | +1.67 | -2.33 |
| 13 | -3.00 | -1.00 | -1.00 |
| 14 | -1.00 | +0.33 | -2.33 |
| 15 | -2.33 | +1.67 | -3.00 |

## Caveats

- If judges are Claude subagents, this is Claude-rating-Claude and may share systematic biases with the code producers.
- 15 examples × 2 conditions × runs per condition. Variance between runs is not separated from variance between conditions in the headline number; the sign test across examples partially controls for this by treating each example as one unit.
- A human judge would be the gold standard. `rankings.md` is the template for that.
