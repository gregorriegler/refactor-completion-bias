"""Scaffold for round-haiku-loose (full 15 × 2 × 3 round, loose harness).

Self-contained (round-independence invariant).

Commands:
  python _scaffold.py extract   # write _snippets/<ex>.py
  python _scaffold.py ids       # print ID table as tsv
  python _scaffold.py manifest  # write manifest.json + judge_letter_map.json
  python _scaffold.py judge     # write judge.md + rankings.md from outputs/
  python _scaffold.py prompt <ex> <cond> <id>   # print loose-harness prompt
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
SEED = 20260421

N_RUNS = 3
CONDITIONS = ("control", "treatment")

CONDITION_PROMPTS = {
    "control": "Refactor this code to your best ability",
    "treatment": "Refactor this code to your best ability. It's ok if you don't get to finish.",
}

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
    out = []
    for f in sorted(EXAMPLES_DIR.glob("*.md")):
        m = re.match(r"(\d+)-", f.name)
        if m: out.append((int(m.group(1)), f))
    return out


def extract_snippet(path: pathlib.Path) -> str:
    text = path.read_text()
    m = re.search(r"```python\n(.*?)```", text, flags=re.DOTALL)
    if not m:
        raise ValueError(f"no python block in {path}")
    return m.group(1).rstrip() + "\n"


def cmd_extract():
    (ROOT/"_snippets").mkdir(exist_ok=True)
    for ex, path in list_examples():
        (ROOT/"_snippets"/f"{ex:02d}.py").write_text(extract_snippet(path))
    print(f"wrote {len(list_examples())} snippets")


def build_plan():
    rng = random.Random(SEED)
    used = set()
    plan = []
    for ex, _ in list_examples():
        for cond in CONDITIONS:
            for run in range(1, N_RUNS + 1):
                while True:
                    hid = f"{rng.randrange(16**4):04x}"
                    if hid not in used:
                        used.add(hid); break
                plan.append((ex, cond, run, hid))
    return plan


def cmd_ids():
    for ex, c, r, h in build_plan():
        print(f"{ex}\t{c}\t{r}\t{h}")


def cmd_manifest():
    plan = build_plan()
    manifest = {h: {"example": e, "condition": c, "run": r} for e, c, r, h in plan}
    (ROOT/"manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    rng = random.Random(SEED ^ 0xBEEF)
    by_ex = {}
    for e, c, r, h in plan:
        by_ex.setdefault(e, []).append(h)
    letter_map = {}
    for ex in sorted(by_ex):
        ids = list(by_ex[ex]); rng.shuffle(ids)
        letter_map[str(ex)] = {chr(ord("A")+i): h for i, h in enumerate(ids)}
    (ROOT/"judge_letter_map.json").write_text(json.dumps(letter_map, indent=2) + "\n")
    print(f"wrote manifest.json ({len(manifest)}) + judge_letter_map.json ({len(letter_map)} examples)")


def cmd_judge():
    letter_map = json.loads((ROOT/"judge_letter_map.json").read_text())
    lines_j = ["# Blind judging package — round-haiku-loose\n\n",
               "For each example you see the ORIGINAL snippet, then refactored VARIANTS\n",
               "labelled by letter. Rank the variants from best (1) to worst (highest)\n",
               "per example. Use each rank exactly once per example. You do NOT know\n",
               "which variant came from which prompt.\n\n"]
    lines_r = ["# Rankings — round-haiku-loose\n\n",
               "Fill in a rank (1=best) for every letter per example. Use each rank\n",
               "exactly once.\n\n"]
    for ex, path in list_examples():
        key = str(ex)
        if key not in letter_map: continue
        original = extract_snippet(path).rstrip()
        lines_j.append(f"## Example {ex}\n\n### Original\n\n```python\n{original}\n```\n\n")
        for L in sorted(letter_map[key]):
            hid = letter_map[key][L]
            body = (OUT_DIR/f"{hid}.md").read_text() if (OUT_DIR/f"{hid}.md").exists() else "(missing)\n"
            lines_j.append(f"### Variant {L}  (id {hid})\n\n{body}")
            if not body.endswith("\n"): lines_j.append("\n")
            lines_j.append("\n")
        lines_r.append(f"## Example {ex}\n\n")
        for L in sorted(letter_map[key]):
            lines_r.append(f"- {L}=\n")
        lines_r.append("\n")
    (ROOT/"judge.md").write_text("".join(lines_j))
    (ROOT/"rankings.md").write_text("".join(lines_r))
    print("wrote judge.md and rankings.md")


def cmd_prompt():
    ex = int(sys.argv[2]); cond = sys.argv[3]; hid = sys.argv[4]
    print(LOOSE_PROMPT_TEMPLATE.format(
        snippet_path=ROOT/"_snippets"/f"{ex:02d}.py",
        output_path=OUT_DIR/f"{hid}.md",
        condition_prompt=CONDITION_PROMPTS[cond]))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "manifest"
    {"extract": cmd_extract, "ids": cmd_ids, "manifest": cmd_manifest,
     "judge": cmd_judge, "prompt": cmd_prompt}[cmd]()
