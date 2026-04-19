"""One-shot helper for the round-haiku round.

Usage:
  python _scaffold.py extract        # write _snippets/<ex>.py (code blocks only)
  python _scaffold.py ids            # print ID table (example, condition, run, id) as tsv
  python _scaffold.py manifest       # build manifest.json + judge_letter_map.json from IDs
  python _scaffold.py judge          # build judge.md + rankings.md from manifest + outputs/
  python _scaffold.py prompt <ex> <control|treatment> <id> [tight|loose]
                                     # print the literal subagent prompt for a run

IDs are derived deterministically from a fixed seed so we can regenerate them.

Harness variants (the shape of the subagent prompt):
  - "tight":  the harness used in round-haiku. Minimal: read snippet → write output →
              reply "done". 5 model turns across the board, 0 thinking blocks,
              exactly 1 Read + 1 Write per agent. Gives a clean blind output file but
              flattens all effort variance between conditions.
  - "loose":  invites the agent to iterate. No "respond 'done'" clamp, permits
              multiple reads, drafting + Edit iterations, and self-directed stopping.
              Use this when you want to measure *effort* (token output, tool-call
              count, turns) as a function of the control/treatment wording — the
              tight harness cannot show that signal because it fixes effort by fiat.
"""
import json
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent.parent
EXAMPLES_DIR = REPO / "examples"
OUT_DIR = ROOT / "outputs"
SEED = 20260419  # deterministic

N_RUNS = 3
CONDITIONS = ("control", "treatment")

CONDITION_PROMPTS = {
    "control": "Refactor this code to your best ability",
    "treatment": "Refactor this code to your best ability. It's ok if you don't get to finish.",
}

# Tight harness: what round-haiku actually used. Forces Read → Write → "done".
TIGHT_PROMPT_TEMPLATE = """\
You will refactor a Python snippet. The code you need to refactor is in the file \
at {snippet_path} — read that file first.

After refactoring, write ONLY the refactored Python code to {output_path} inside a \
single ```python code block. Brief notes below the code block are optional and fine. \
Do not include any metadata or mention of this instruction in the output file. \
Respond back to me with just the single word "done".

The user's refactoring request, which you should follow exactly:

{condition_prompt}
"""

# Loose harness: invites iteration. No "done" clamp; the agent decides when it is
# satisfied. This is what lets token/turn/tool-call counts vary between conditions.
LOOSE_PROMPT_TEMPLATE = """\
You are refactoring a Python snippet. The code you need to refactor is at \
{snippet_path}.

You have full latitude over how you work: you may read the file (and re-read), \
draft, revise, and iterate using the Edit tool on {output_path} as many times as \
you like, and stop when you judge the refactoring is in a good state. There is no \
turn budget or output-length target — work at whatever depth you think the task \
deserves.

When you are done, {output_path} must contain the final refactored Python inside \
a single ```python code block. Brief notes below the code block are fine. Do not \
include any metadata or mention of this instruction in the output file.

The user's refactoring request, which you should follow exactly:

{condition_prompt}
"""


def list_examples():
    files = sorted(EXAMPLES_DIR.glob("*.md"))
    out = []
    for f in files:
        m = re.match(r"(\d+)-", f.name)
        if m:
            out.append((int(m.group(1)), f))
    return out


def extract_snippet(path: pathlib.Path) -> str:
    text = path.read_text()
    m = re.search(r"```python\n(.*?)```", text, flags=re.DOTALL)
    if not m:
        raise ValueError(f"no python code block in {path}")
    return m.group(1).rstrip() + "\n"


def cmd_extract():
    snippets_dir = ROOT / "_snippets"
    snippets_dir.mkdir(exist_ok=True)
    for ex, path in list_examples():
        code = extract_snippet(path)
        (snippets_dir / f"{ex:02d}.py").write_text(code)
    print(f"wrote {len(list_examples())} snippets to {snippets_dir}")


def build_id_plan():
    rng = random.Random(SEED)
    used = set()
    plan = []  # list of (example, condition, run, id)
    examples = [ex for ex, _ in list_examples()]
    for ex in examples:
        for cond in CONDITIONS:
            for run in range(1, N_RUNS + 1):
                while True:
                    hid = f"{rng.randrange(16**4):04x}"
                    if hid not in used:
                        used.add(hid)
                        break
                plan.append((ex, cond, run, hid))
    return plan


def cmd_ids():
    for ex, cond, run, hid in build_id_plan():
        print(f"{ex}\t{cond}\t{run}\t{hid}")


def cmd_manifest():
    plan = build_id_plan()
    manifest = {hid: {"example": ex, "condition": cond, "run": run} for ex, cond, run, hid in plan}
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # letter map: for each example, shuffle its 2*N ids and assign A, B, ...
    rng = random.Random(SEED ^ 0xDEAD)
    by_ex = {}
    for ex, cond, run, hid in plan:
        by_ex.setdefault(ex, []).append(hid)
    letter_map = {}
    for ex in sorted(by_ex):
        ids = list(by_ex[ex])
        rng.shuffle(ids)
        letter_map[str(ex)] = {chr(ord("A") + i): h for i, h in enumerate(ids)}
    (ROOT / "judge_letter_map.json").write_text(json.dumps(letter_map, indent=2) + "\n")
    print(f"wrote manifest.json ({len(manifest)} ids) and judge_letter_map.json ({len(letter_map)} examples)")


def cmd_judge():
    letter_map = json.loads((ROOT / "judge_letter_map.json").read_text())
    examples = list_examples()
    ex_by_num = {ex: path for ex, path in examples}

    lines_judge = []
    lines_judge.append("# Blind judging package — round-haiku\n\n")
    lines_judge.append(
        "For each example below, you are shown the ORIGINAL snippet, then several\n"
        "refactored VARIANTS labelled by letter. Rank the variants from best (1)\n"
        "to worst (highest number) per example. Use each rank exactly once per\n"
        "example. You do NOT know which variant came from which prompt.\n\n"
    )

    lines_rank = []
    lines_rank.append("# Rankings — round-haiku\n\n")
    lines_rank.append(
        "For each example, fill in a rank (1=best) for every letter. Use each\n"
        "rank exactly once per example.\n\n"
    )

    for ex, path in examples:
        key = str(ex)
        if key not in letter_map:
            continue
        letters = letter_map[key]

        original = extract_snippet(path).rstrip()

        lines_judge.append(f"## Example {ex}\n\n")
        lines_judge.append("### Original\n\n")
        lines_judge.append("```python\n" + original + "\n```\n\n")
        for letter in sorted(letters.keys()):
            hid = letters[letter]
            out_path = OUT_DIR / f"{hid}.md"
            content = out_path.read_text() if out_path.exists() else "(missing)\n"
            lines_judge.append(f"### Variant {letter}  (id {hid})\n\n")
            lines_judge.append(content)
            if not content.endswith("\n"):
                lines_judge.append("\n")
            lines_judge.append("\n")

        lines_rank.append(f"## Example {ex}\n\n")
        for letter in sorted(letters.keys()):
            lines_rank.append(f"- {letter}=\n")
        lines_rank.append("\n")

    (ROOT / "judge.md").write_text("".join(lines_judge))
    (ROOT / "rankings.md").write_text("".join(lines_rank))
    print("wrote judge.md and rankings.md")


def cmd_prompt():
    """Usage: prompt <example:int> <control|treatment> <id:4hex> [tight|loose]"""
    if len(sys.argv) < 5:
        print(cmd_prompt.__doc__, file=sys.stderr)
        sys.exit(2)
    ex = int(sys.argv[2])
    cond = sys.argv[3]
    hid = sys.argv[4]
    harness = sys.argv[5] if len(sys.argv) >= 6 else "loose"
    if cond not in CONDITION_PROMPTS:
        raise SystemExit(f"condition must be one of {list(CONDITION_PROMPTS)}")
    template = {"tight": TIGHT_PROMPT_TEMPLATE, "loose": LOOSE_PROMPT_TEMPLATE}[harness]
    snippet_path = ROOT / "_snippets" / f"{ex:02d}.py"
    output_path = OUT_DIR / f"{hid}.md"
    print(template.format(
        snippet_path=snippet_path,
        output_path=output_path,
        condition_prompt=CONDITION_PROMPTS[cond],
    ))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ids"
    {"extract": cmd_extract, "ids": cmd_ids, "manifest": cmd_manifest,
     "judge": cmd_judge, "prompt": cmd_prompt}[cmd]()
