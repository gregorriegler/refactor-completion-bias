# Effort comparison — round-haiku-loose vs round-haiku (tight)

Recovered from Claude Code session logs under `/tmp/claude-0/.../tasks/`.

- tight refactor agents matched: **90** / 90
- loose refactor agents matched: **90** / 90

## Assistant turns (model round-trips per agent)

| cond | n | mean | median | min | max |
|---|---|---|---|---|---|
| tight / control | 45 | 5.00 | 5.0 | 5 | 5 |
| tight / treatment | 45 | 5.00 | 5.0 | 5 | 5 |
| loose / control | 45 | 5.42 | 5.0 | 5 | 10 |
| loose / treatment | 45 | 6.67 | 7.0 | 5 | 13 |

## Output tokens (model-generated) per agent

| cond | n | mean | median | min | max |
|---|---|---|---|---|---|
| tight / control | 45 | 1051 | 639 | 5 | 3834 |
| tight / treatment | 45 | 1111 | 828 | 5 | 3376 |
| loose / control | 45 | 1330 | 1076 | 9 | 4174 |
| loose / treatment | 45 | 1607 | 1241 | 9 | 4840 |

## Total tool calls per condition, broken down by tool

| cond | Read | Write | Edit | other | total |
|---|---|---|---|---|---|
| tight / control | 45 | 45 | 0 | 0 | 90 |
| tight / treatment | 45 | 45 | 0 | 0 | 90 |
| loose / control | 57 | 45 | 0 | 2 | 104 |
| loose / treatment | 75 | 45 | 3 | 5 | 128 |

## Per-example mean turns under the loose harness

| Ex | ctrl turns | trt turns | Δ |
|---|---|---|---|
| 1 | 5.33 | 8.33 | +3.00 |
| 2 | 5.00 | 5.67 | +0.67 |
| 3 | 5.67 | 6.33 | +0.67 |
| 4 | 5.00 | 8.33 | +3.33 |
| 5 | 5.00 | 5.00 | +0.00 |
| 6 | 6.67 | 5.67 | -1.00 |
| 7 | 5.33 | 6.33 | +1.00 |
| 8 | 5.00 | 5.67 | +0.67 |
| 9 | 5.00 | 6.33 | +1.33 |
| 10 | 5.00 | 6.33 | +1.33 |
| 11 | 6.00 | 6.33 | +0.33 |
| 12 | 6.67 | 6.33 | -0.33 |
| 13 | 5.00 | 7.00 | +2.00 |
| 14 | 5.33 | 9.67 | +4.33 |
| 15 | 5.33 | 6.67 | +1.33 |

## Thinking blocks

Always 0 across all 180 agents (90 tight + 90 loose). Haiku 4.5 emits
no `thinking` blocks without extended thinking enabled, and the `Agent`
tool does not expose that switch. Reasoning depth cannot be measured
from this data — only mechanical effort (turns, tool calls, tokens).

## Takeaway

The tight round pinned every agent to ~5 turns flat (means: control
5.00, treatment 5.00) — no room for the "iterate more when
no pressure to finish" mechanism to express itself. Under the loose
harness, effort does move, and it moves in the direction the hypothesis
predicts:

- **Assistant turns**: loose / control 5.42, loose / treatment 6.67 — treatment takes more model round-trips (Δ +1.24).
- **Total Read calls**: loose / control 57, loose / treatment 75 — treatment re-reads more.

Crucially, these effort differences **coincide with the quality signal**:
under the loose harness, treatment won 10/15 examples (vs 8/15 in tight)
and the overall rank delta widened from −0.11 to −0.48. The tight harness
muted both effort and quality signals; the loose harness lets both
surface and they point the same way.

Still n=15 examples so the sign-test p is 0.302 — directional, not
statistically significant at α=0.05. But the direction is now consistent
across both the quality and effort axes, which is what the hypothesis
actually predicts.
