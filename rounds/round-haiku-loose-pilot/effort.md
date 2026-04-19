# Effort comparison — round-haiku-loose-pilot vs tight baseline

Compares the subagent effort metrics under the **tight** harness (from
`round-haiku`, restricted to the same three examples 11/13/14) against the
**loose** harness used here. Data recovered from the Claude Code session
logs under `/tmp/claude-0/.../tasks/`.

- tight refactor agents matched: **18** (ex 11/13/14 only, from 90-agent round)
- loose refactor agents matched: **12** (this pilot)

## Assistant turns (model round-trips per agent)

| cond | n | mean | median | min | max |
|---|---|---|---|---|---|
| tight / control | 9 | 5.0 | 5.0 | 5 | 5 |
| tight / treatment | 9 | 5.0 | 5.0 | 5 | 5 |
| loose / control | 6 | 5.2 | 5.0 | 5 | 6 |
| loose / treatment | 6 | 6.5 | 7.0 | 5 | 7 |

## Output tokens (model-generated) per agent

| cond | n | mean | median | min | max |
|---|---|---|---|---|---|
| tight / control | 9 | 2533.8 | 2694.0 | 9 | 3417 |
| tight / treatment | 9 | 1286.2 | 94.0 | 5 | 3105 |
| loose / control | 6 | 2763.7 | 3294.0 | 9 | 3598 |
| loose / treatment | 6 | 2747.5 | 3246.5 | 200 | 3593 |

## Total tool calls per agent, broken down by tool

| cond | Read | Write | Edit | total |
|---|---|---|---|---|
| tight / control | 9 | 9 | 0 | 18 |
| tight / treatment | 9 | 9 | 0 | 18 |
| loose / control | 7 | 6 | 0 | 13 |
| loose / treatment | 11 | 6 | 0 | 17 |

Note on the bimodal tight/treatment output-tokens (median 94, max 3105): the
Anthropic API `output_tokens` counter sometimes does not attribute tool-call
parameter content to the same assistant turn it was generated on, so per-agent
output-token totals recovered from JSONL logs are not fully reliable. The
assistant-turns and tool-call counts are reliable because they are structural.

## Thinking blocks

Always 0 across all 30 agents. Haiku 4.5 does not emit `thinking` blocks
without extended thinking enabled, and the `Agent` tool doesn't expose that
switch. So reasoning effort cannot be measured from this data; only
mechanical effort (turns, tool calls, output tokens) can.

## Takeaway

The hypothesis is that removing completion pressure ("it's ok if you don't
finish") lets the model iterate deeper instead of pushing toward a shallow
but complete edit. That predicts **more** turns / tool calls / re-reads under
treatment, not fewer.

Under the tight harness every agent was pinned to ~5 turns / 2 tool calls /
0 thinking blocks — no effort variance at all, so the mechanism could not
operate. This is probably why the tight round's quality signal was weak:
both conditions were forced into one-shot Read → Write and the treatment
wording had no degree of freedom to spend.

Under the loose harness, effort does move, and it moves in the direction
the hypothesis predicts:

- loose / control: 5.2 turns mean, 7 total Read calls
- loose / treatment: 6.5 turns mean (median 7), **11** total Read calls

Treatment agents are re-reading the snippet and taking more round-trips.
Output tokens equalise at ~2750 (both conditions write full-sized
refactorings) rather than splitting 2:1 the way they did under tight — i.e.
under loose, treatment is no longer cutting the work short.

With only 6 agents per loose condition this is directional, not
statistically conclusive. What the pilot does establish is:

1. The loose harness *can* produce measurable effort variance, in the
   direction the hypothesis predicts.
2. The tight harness masks the hypothesised mechanism entirely by fixing
   effort, so using tight to measure this effect was a category error.

This justifies running the full 15 × 2 × 3 round under the loose harness to
get enough statistical power on both quality and effort.
