"""Un-blind rankings and compute statistics for a refactor-completion-bias round.

Usage:
    python analyze.py [<round-dir>]

If <round-dir> is omitted, defaults to the current working directory. The
directory is expected to contain `manifest.json`, `judge_letter_map.json`,
zero or more `judge_rankings_*.md` files, and optionally `rankings.md`.
Writes `<round-dir>/analysis.md`.
"""
import json
import math
import pathlib
import re
import sys
from collections import defaultdict


def load_letter_map(raw: dict) -> dict[int, dict[str, str]]:
    """Normalize the letter map into {example_int: {letter: id}}.

    Supports both legacy flat form (`"<ex>.<letter>": "<id>"`) and the
    nested form (`"<ex>": {"<letter>": "<id>"}`).
    """
    by_ex: dict[int, dict[str, str]] = defaultdict(dict)
    for key, value in raw.items():
        if isinstance(value, dict):
            by_ex[int(key)] = dict(value)
        else:
            ex_str, letter = key.split(".")
            by_ex[int(ex_str)][letter] = value
    return dict(by_ex)


def parse_ranking_file(path: pathlib.Path) -> dict[int, dict[str, int]]:
    """Parse a rankings file into {example: {letter: rank}}."""
    text = path.read_text()
    result: dict[int, dict[str, int]] = {}
    current_ex: int | None = None
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"##\s*Example\s+(\d+)", line)
        if m:
            current_ex = int(m.group(1))
            result[current_ex] = {}
            continue
        m = re.match(r"-?\s*([A-Z])\s*=\s*(\d+)", line)
        if m and current_ex is not None:
            letter, rank = m.group(1), int(m.group(2))
            result[current_ex][letter] = rank
    return result


def validate(
    rankings: dict[int, dict[str, int]],
    letter_map: dict[int, dict[str, str]],
    source: str,
) -> list[str]:
    """Check ranks for examples that appear in both the judge file and the
    letter map. Missing examples (judge didn't rank that example) are not an
    error — they're just skipped during aggregation.
    """
    errs: list[str] = []
    for ex, letters in letter_map.items():
        if ex not in rankings:
            continue
        expected_letters = set(letters.keys())
        expected_ranks = list(range(1, len(expected_letters) + 1))
        r = rankings[ex]
        if set(r.keys()) != expected_letters:
            errs.append(
                f"{source}: Example {ex} has keys {sorted(r.keys())}, "
                f"expected {sorted(expected_letters)}"
            )
        if sorted(r.values()) != expected_ranks:
            errs.append(
                f"{source}: Example {ex} ranks {sorted(r.values())}, "
                f"expected {expected_ranks}"
            )
    return errs


def sign_test_p(n_plus: int, n_minus: int) -> float:
    """Two-sided binomial sign test with p=0.5."""
    n = n_plus + n_minus
    if n == 0:
        return 1.0
    k = min(n_plus, n_minus)
    tail = sum(math.comb(n, i) for i in range(0, k + 1))
    return min(1.0, 2.0 * tail / (2 ** n))


def main() -> int:
    if len(sys.argv) > 2:
        print(__doc__)
        return 2
    round_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) == 2 else pathlib.Path.cwd()
    round_dir = round_dir.resolve()

    manifest_path = round_dir / "manifest.json"
    letter_map_path = round_dir / "judge_letter_map.json"
    if not manifest_path.exists() or not letter_map_path.exists():
        print(
            f"expected manifest.json and judge_letter_map.json in {round_dir}",
            file=sys.stderr,
        )
        return 2

    manifest = json.loads(manifest_path.read_text())
    letter_map = load_letter_map(json.loads(letter_map_path.read_text()))
    examples = sorted(letter_map.keys())

    candidates = sorted(round_dir.glob("judge_rankings_*.md"))
    human = round_dir / "rankings.md"
    if human.exists():
        filled = re.findall(r"(?m)^-\s*[A-Z]\s*=\s*\d", human.read_text())
        if filled:
            candidates.append(human)

    if not candidates:
        print("no ranking files found; fill rankings.md or wait for judge subagents")
        return 1

    per_judge: dict[str, dict[int, dict[str, int]]] = {}
    errs: list[str] = []
    for p in candidates:
        r = parse_ranking_file(p)
        errs.extend(validate(r, letter_map, p.name))
        per_judge[p.name] = r

    if errs:
        print("VALIDATION ERRORS:")
        for e in errs:
            print(" -", e)
        return 2

    condition_ranks_per_example: dict[int, dict[str, list[int]]] = {
        ex: {"control": [], "treatment": []} for ex in examples
    }
    condition_ranks_overall: dict[str, list[int]] = {"control": [], "treatment": []}
    deltas_by_judge_ex: dict[str, dict[int, float]] = defaultdict(dict)

    for judge_name, rankings in per_judge.items():
        for ex in examples:
            if ex not in rankings:
                continue
            for letter, rank in rankings[ex].items():
                anon_id = letter_map[ex][letter]
                cond = manifest[anon_id]["condition"]
                condition_ranks_per_example[ex][cond].append(rank)
                condition_ranks_overall[cond].append(rank)
            ctrl = [
                rank
                for letter, rank in rankings[ex].items()
                if manifest[letter_map[ex][letter]]["condition"] == "control"
            ]
            treat = [
                rank
                for letter, rank in rankings[ex].items()
                if manifest[letter_map[ex][letter]]["condition"] == "treatment"
            ]
            if ctrl and treat:
                deltas_by_judge_ex[judge_name][ex] = (
                    sum(treat) / len(treat) - sum(ctrl) / len(ctrl)
                )

    lines: list[str] = []
    lines.append(f"# Refactor Completion Bias — Analysis ({round_dir.name})\n")
    variants_per_example = {ex: len(letter_map[ex]) for ex in examples}
    variant_summary = (
        f"{next(iter(variants_per_example.values()))}"
        if len(set(variants_per_example.values())) == 1
        else "variable"
    )
    lines.append(
        f"Judges: {len(per_judge)} ({', '.join(per_judge)}). "
        f"Examples: {len(examples)}. Variants per example: {variant_summary}. "
        "Ranks are 1=best, highest=worst, blind to condition.\n\n"
    )

    lines.append("## Headline\n\n")
    ctrl_mean = sum(condition_ranks_overall["control"]) / len(
        condition_ranks_overall["control"]
    )
    treat_mean = sum(condition_ranks_overall["treatment"]) / len(
        condition_ranks_overall["treatment"]
    )
    lines.append(
        f"- Overall mean rank (lower = better): control **{ctrl_mean:.2f}**, "
        f"treatment **{treat_mean:.2f}**. Difference (treatment−control): "
        f"**{treat_mean - ctrl_mean:+.2f}**.\n"
    )
    if treat_mean < ctrl_mean:
        lines.append("- Treatment looks better on average.\n")
    elif treat_mean > ctrl_mean:
        lines.append("- Control looks better on average.\n")
    else:
        lines.append("- Tie on average.\n")
    lines.append("\n")

    lines.append("## Per-example mean rank\n\n")
    lines.append("| Example | Control mean | Treatment mean | Δ (T−C) |\n")
    lines.append("|---|---|---|---|\n")
    per_ex_deltas: list[float] = []
    for ex in examples:
        c = condition_ranks_per_example[ex]["control"]
        t = condition_ranks_per_example[ex]["treatment"]
        if not c or not t:
            lines.append(
                f"| {ex} | "
                f"{'—' if not c else f'{sum(c)/len(c):.2f}'} | "
                f"{'—' if not t else f'{sum(t)/len(t):.2f}'} | — |\n"
            )
            continue
        cm = sum(c) / len(c)
        tm = sum(t) / len(t)
        d = tm - cm
        per_ex_deltas.append(d)
        lines.append(f"| {ex} | {cm:.2f} | {tm:.2f} | {d:+.2f} |\n")
    lines.append("\n")

    n_treatment_wins = sum(1 for d in per_ex_deltas if d < 0)
    n_control_wins = sum(1 for d in per_ex_deltas if d > 0)
    n_ties = sum(1 for d in per_ex_deltas if d == 0)
    p = sign_test_p(n_treatment_wins, n_control_wins)
    n_scored = n_treatment_wins + n_control_wins + n_ties
    lines.append("## Sign test across examples\n\n")
    lines.append(
        f"Treatment wins (lower mean rank): **{n_treatment_wins}** examples. "
        f"Control wins: **{n_control_wins}**. Ties: **{n_ties}**. "
        f"Two-sided binomial p ≈ **{p:.3f}**.\n\n"
    )
    if p >= 0.05:
        lines.append(
            f"- Not statistically significant at α=0.05 with n={n_scored} examples; "
            "treat as exploratory.\n\n"
        )
    else:
        lines.append("- Statistically significant at α=0.05.\n\n")

    lines.append("## Per-judge per-example deltas (treatment mean − control mean)\n\n")
    lines.append("| Example | " + " | ".join(per_judge.keys()) + " |\n")
    lines.append("|---" * (1 + len(per_judge)) + "|\n")
    for ex in examples:
        row = [f"{ex}"]
        for judge_name in per_judge:
            d = deltas_by_judge_ex[judge_name].get(ex)
            row.append("—" if d is None else f"{d:+.2f}")
        lines.append("| " + " | ".join(row) + " |\n")
    lines.append("\n")

    lines.append("## Caveats\n\n")
    lines.append(
        "- If judges are Claude subagents, this is Claude-rating-Claude and may "
        "share systematic biases with the code producers.\n"
    )
    lines.append(
        f"- {len(examples)} examples × 2 conditions × runs per condition. Variance "
        "between runs is not separated from variance between conditions in the "
        "headline number; the sign test across examples partially controls for this "
        "by treating each example as one unit.\n"
    )
    lines.append(
        "- A human judge would be the gold standard. `rankings.md` is the template "
        "for that.\n"
    )

    (round_dir / "analysis.md").write_text("".join(lines))
    print(f"wrote {round_dir / 'analysis.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
