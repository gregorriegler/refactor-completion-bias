"""One-shot helper for the round-haiku round.

Usage:
  python _scaffold.py extract   # write snippets_<ex>.txt (code blocks only)
  python _scaffold.py ids       # print ID table (example, condition, run, id) as tsv
  python _scaffold.py manifest  # build manifest.json + judge_letter_map.json from IDs
  python _scaffold.py judge     # build judge.md + rankings.md from manifest + outputs/

IDs are derived deterministically from a fixed seed so we can regenerate them.
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


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ids"
    {"extract": cmd_extract, "ids": cmd_ids, "manifest": cmd_manifest, "judge": cmd_judge}[cmd]()
