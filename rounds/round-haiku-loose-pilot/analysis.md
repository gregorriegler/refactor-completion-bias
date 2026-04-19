# Refactor Completion Bias — Analysis (round-haiku-loose-pilot)
Judges: 3 (judge_rankings_1.md, judge_rankings_2.md, judge_rankings_3.md). Examples: 3. Variants per example: 4. Ranks are 1=best, highest=worst, blind to condition.

## Headline

- Overall mean rank (lower = better): control **2.56**, treatment **2.44**. Difference (treatment−control): **-0.11**.
- Treatment looks better on average.

## Per-example mean rank

| Example | Control mean | Treatment mean | Δ (T−C) |
|---|---|---|---|
| 11 | 2.17 | 2.83 | +0.67 |
| 13 | 3.00 | 2.00 | -1.00 |
| 14 | 2.50 | 2.50 | +0.00 |

## Sign test across examples

Treatment wins (lower mean rank): **1** examples. Control wins: **1**. Ties: **1**. Two-sided binomial p ≈ **1.000**.

- Not statistically significant at α=0.05 with n=3 examples; treat as exploratory.

## Per-judge per-example deltas (treatment mean − control mean)

| Example | judge_rankings_1.md | judge_rankings_2.md | judge_rankings_3.md |
|---|---|---|---|
| 11 | +2.00 | +1.00 | -1.00 |
| 13 | -1.00 | -2.00 | +0.00 |
| 14 | +1.00 | -1.00 | +0.00 |

## Caveats

- If judges are Claude subagents, this is Claude-rating-Claude and may share systematic biases with the code producers.
- 3 examples × 2 conditions × runs per condition. Variance between runs is not separated from variance between conditions in the headline number; the sign test across examples partially controls for this by treating each example as one unit.
- A human judge would be the gold standard. `rankings.md` is the template for that.
