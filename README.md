# Refactor Completion Bias

## The idea

When you ask a model to "refactor this code," it feels pressure to produce something complete and shippable within a single response. That pressure may bias it toward shallow, surface-level edits that finish cleanly, rather than deeper, riskier changes that might run long.

**Hypothesis:** explicitly telling the model that incomplete work is acceptable ("it's okay if you don't finish") lets it spend its budget on quality instead of completion, producing better refactorings on average.

## What was done

- 10 Python snippets in `examples/`, each a textbook refactor target (if/elif chains, feature envy, magic numbers, state flags, long parameter lists, etc.).
- Two conditions per example. The literal prompt text sent to each subagent (appended after the snippet) is:
  - **control** — `Refactor this code to your best ability`
  - **treatment** — `Refactor this code to your best ability. It's ok if you don't get to finish.`
- 3 runs per condition per example → **60 outputs** in `outputs/`, each stored under a random 4-hex ID with no hint of its condition.
- Blind ranking: 3 Claude subagent judges each ranked the 6 variants per example (1 = best, 6 = worst), seeing only anonymized letters.
- Un-blinding and stats in `analyze.py` → `analysis.md`.

Files of interest:
- `examples/` — one file per snippet.
- `outputs/<id>.md` — one refactor per file.
- `manifest.json` — ID → (example, condition, run). Hidden from judges.
- `judge_letter_map.json` — per-example letter → ID shuffle used by judges.
- `judge_rankings_{1,2,3}.md` — the three judges' blind rankings.
- `analysis.md` — the computed results.
- `rounds/` — future independent rounds live here (empty so far). See `CLAUDE.md` for the new-round runbook. Top-level files above are the frozen first-round baseline.

## Results

Mean rank, lower = better:

| Condition | Overall mean rank |
|---|---|
| control | 3.80 |
| treatment | **3.20** |

Treatment won 6 of 10 examples (sign-test p ≈ 0.75 — not significant at n = 10).

Per-example means:

| Example | Control | Treatment | Δ (T − C) |
|---|---|---|---|
| 1 | 4.56 | 2.44 | −2.11 |
| 2 | 3.00 | 4.00 | +1.00 |
| 3 | 3.00 | 4.00 | +1.00 |
| 4 | 3.67 | 3.33 | −0.33 |
| 5 | 3.22 | 3.78 | +0.56 |
| 6 | 4.67 | 2.33 | −2.33 |
| 7 | 4.00 | 3.00 | −1.00 |
| 8 | 4.89 | 2.11 | −2.78 |
| 9 | 3.33 | 3.67 | +0.33 |
| 10 | 3.67 | 3.33 | −0.33 |

The big treatment wins (Examples 1, 6, 8) and the modest losses (2, 3, 5) average out to a small directional effect. The largest gaps both ways come from real correctness or design differences the judges noticed in individual examples, not from a uniform shift.

### Caveats

- The judges are themselves Claude subagents — Claude-rating-Claude risks shared stylistic biases.
- 10 examples is underpowered for a significance test.
- An earlier run included two extra sentences in the treatment prompt ("partial, high-quality work is preferred over rushed completion. Focus on the most valuable structural improvements; a thoughtful partial refactor is better than a rushed complete one.") The numbers above are the rerun with the strict one-sentence treatment. The directional effect shrunk noticeably (Δ went from −0.88 to −0.60) — most of the apparent earlier benefit may have come from the focus instruction, not the permission-to-stop-early sentence.

## Human spot-check

As an informal check, a human (the repo owner) was shown three blind head-to-head comparisons — one control run vs. one treatment run — without being told which was which:

| Example | Human pick | Was treatment? |
|---|---|---|
| 4 (Invoice / feature envy) | X | ✓ |
| 6 (shipping if-elif chain) | X | ✓ |
| 8 (BMI magic numbers) | X | ✓ |

Three for three in favor of treatment. Small sample, same direction as the blind judges, same direction as the hypothesis. Worth noting: on Example 6 the human also implicitly caught a correctness issue in the control variant (a silent FedEx ordering change) that the treatment variant avoided; on Example 8 the treatment pick was an API break (enum string values changed), so the human preference there was against behavior-preservation — a reminder that "looks better" and "is better" can diverge.

Note: this spot-check was done against the original (three-sentence) treatment variants, before the strict-treatment rerun. The treatment outputs in `outputs/` have since been regenerated; the spot-check picks haven't been redone.

Overall: the effect is small, directionally real in both machine and human judgements, and well short of statistical significance at this sample size. Treat as exploratory.
