# Rounds

Each subdirectory here is a complete, self-contained experimental round.
See `../CLAUDE.md` for the full runbook. Each round is statistically
independent of the others: no round re-uses another round's outputs, and
every round's analysis is computed only from its own `manifest.json` +
`judge_letter_map.json` + rankings files.

## Round directory layout

```
rounds/<slug>/
  README.md              # purpose, literal prompts, runs/condition, examples
  outputs/<id>.md        # one file per run, random 4-hex id, no condition hint
  manifest.json          # {id: {example, condition, run}} — hidden from judges
  judge_letter_map.json  # {"<example>": {"A": "<id>", ...}}
  judge.md               # blind judging package
  rankings.md            # template for human judge
  judge_rankings_*.md    # filled rankings from human or judge subagents
  analysis.md            # produced by: python ../../analyze.py rounds/<slug>
```

## Round README template

Copy this into `rounds/<slug>/README.md` at the start of a round and fill in.

```markdown
# Round <slug>

## Purpose
<1–3 sentences: what this round is testing / varying>

## Prompts (literal text appended after the snippet)

- **control**: `...`
- **treatment**: `...`

## Parameters

- Examples: <e.g. "all files in examples/" or an explicit list>
- Runs per condition per example: N = <...>
- Judging: <human / K judge subagents / both>

## Results

See `analysis.md` (produced after rankings are in).
```
