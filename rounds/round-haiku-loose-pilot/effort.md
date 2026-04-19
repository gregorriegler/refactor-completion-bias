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

Under the tight harness every agent was pinned to ~5 turns / 2 tool
calls / 0 thinking blocks — no effort variance at all. Under the loose
harness, effort does move: loose / control stays at 5.2 turns but
loose / treatment averages 6.5 turns and issues noticeably more `Read`
calls. That's the opposite direction from the hypothesis — the "it's ok if
you don't get to finish" wording did not reduce measurable effort here; if
anything it increased it slightly, while equalising the output token counts
that the tight harness had driven apart.

With only 6 agents per loose condition this is directional, not
statistically conclusive. What it does clearly show is that the loose
harness *can* produce effort variance (tight cannot), so it is the right
harness for a full-round effort study.
