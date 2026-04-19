# Refactor Completion Bias Experiment

## Hypothesis
Telling a model "it's okay if you don't finish" may produce better refactoring than a plain refactor prompt, because the latter pressures the model toward shallow but complete edits.

## Experimental unit
- **Example**: one Python snippet in `examples/`, one file per snippet. Shared across rounds.
- **Condition**: the literal text appended after the snippet when sending to a refactoring subagent. The original study used:
  - **control**: `Refactor this code to your best ability`
  - **treatment**: `Refactor this code to your best ability. It's ok if you don't get to finish.`
  - A new round MAY use different prompts (e.g. a reworded treatment). Each round fixes and documents its own prompts in its own `README.md`.
- **Run**: one independent invocation of a subagent for a given (example, condition).
- **Round**: a complete, self-contained experiment — one fresh set of runs across all examples in `examples/`, under the prompts that round has fixed. Rounds are statistically independent: a new round never re-shows prior outputs to judges, and a new round's analysis is computed only from that round's data.

## Layout

### Shared
- `examples/` — one markdown file per Python snippet. Currently 14 examples (`01-…` … `15-…`, with `15-combat-simulator.md` present but not yet exercised by any complete round — see below). Add new example files here if new snippets are desired; they are automatically in scope for the next round.
- `analyze.py` — generic statistics script. Run it as `python analyze.py <round-dir>`; it reads `<round-dir>/manifest.json`, `<round-dir>/judge_letter_map.json`, and `<round-dir>/judge_rankings_*.md` (plus `<round-dir>/rankings.md` if filled) and writes `<round-dir>/analysis.md`.

### Baseline round (frozen, at top level)
The first completed experiment lives at top level and is frozen — do NOT modify it when running new rounds. It contains the simple-example study (examples 1–10, 3 runs/condition), the extension runs for examples 11–14 (6 runs/condition), and the extensibility re-judge. Files:
- `outputs/` — 108 output files from the baseline round.
- `manifest.json` — ID → (example, condition, run) for the 108 outputs.
- `judge.md`, `judge_letter_map.json`, `rankings.md`, `judge_rankings_{1,2,3}.md`, `judge_rankings_ext_{1,2,3}.md` — baseline blind-judging artifacts.
- `analysis.md` — computed baseline results (examples 1–10 primary analysis, plus extended analyses for 11–14 appended).
- `README.md` — human-facing summary of what was done and what was found.

### New rounds
Each new round lives under `rounds/<slug>/` with the same file layout (minus the shared `examples/` and `analyze.py`):
```
rounds/<slug>/
  README.md              # exact control prompt, treatment prompt, runs/condition, examples included
  outputs/<id>.md        # one file per run, random 4-hex id, no condition hint in the content
  manifest.json          # {id: {example, condition, run}} — kept secret from judges
  judge_letter_map.json  # {"<example>": {"A": "<id>", ...}} — per-example letter shuffle
  judge.md               # blind judging package (original snippet + shuffled variants)
  rankings.md            # empty template for human judge
  judge_rankings_*.md    # filled rankings (human or judge subagents)
  analysis.md            # produced by analyze.py from the above
```

## Procedure for a new round (agent runbook)

Assume a user has asked for "another round" and optionally specified the prompts (if not, default to the baseline control/treatment wording above) and N (runs per condition per example; default 3).

1. **Pick a slug** like `round-02` or `treatment-worded-differently`. Create `rounds/<slug>/` and `rounds/<slug>/outputs/`.
2. **Write `rounds/<slug>/README.md`** stating: the round's purpose, the literal control prompt, the literal treatment prompt, N (runs/condition), and the list of examples in scope (by default, every file in `examples/`).
3. **Enumerate jobs**: for each example × condition × run in 1..N, one subagent job. Total = `len(examples) * 2 * N`.
4. **Spawn subagents**, each given ONLY:
   - The contents of the snippet (the code block from the example file)
   - One of the two prompts appended on a new line
   - No knowledge of the experiment, the other condition, the round name, or prior rounds.
5. **Collect outputs**. For each finished job, pick a random 4-hex ID unique within this round. Write the refactored code (and any short agent notes) to `rounds/<slug>/outputs/<id>.md`. Never write the condition, run, or example number into the output file.
6. **Write `rounds/<slug>/manifest.json`**: `{"<id>": {"example": <int>, "condition": "control"|"treatment", "run": <int>}}`.
7. **Build `rounds/<slug>/judge_letter_map.json`**: for each example, shuffle its `2*N` IDs and assign consecutive letters starting at A. Structure: `{"<example>": {"A": "<id>", "B": "<id>", ...}}`.
8. **Build `rounds/<slug>/judge.md`**: for each example, print the original snippet and then, in letter order, each variant's code. Do NOT include condition or run info. Include the short hex ID beside each letter as a convenience tag.
9. **Write `rounds/<slug>/rankings.md`** as an empty template: per example, one line per letter (`- A=`, `- B=`, …) with the full letter range for that example. Tell the judge to rank 1..`2*N` with each rank used exactly once per example.
10. **Judging**: either wait for the human to fill `rankings.md`, or spawn judge subagents that each produce `rounds/<slug>/judge_rankings_<name>.md` in the same format. Judges see `judge.md` only; never `manifest.json` or `judge_letter_map.json`.
11. **Analyze**: run `python analyze.py rounds/<slug>` to write `rounds/<slug>/analysis.md`.

### Independence invariants
- Nothing in a new round's workflow reads files from the baseline top level or from other rounds. Each round is a sealed unit.
- IDs do not need to be globally unique across rounds (only within a round).
- Judges in a new round NEVER rank baseline outputs, and baseline judges never rank new-round outputs.

## Example 15 status
`examples/15-combat-simulator.md` exists but was never fully exercised in the baseline round (only partial treatment runs were produced, with no control counterpart). The orphan outputs and manifest entries have been removed. The example file is retained and is in-scope by default for any new round that takes "all examples in `examples/`".
