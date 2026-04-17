"""Un-blind rankings and compute statistics for the refactor-completion-bias experiment."""
import json
import math
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).parent
MANIFEST = json.loads((ROOT / "manifest.json").read_text())
LETTER_MAP = json.loads((ROOT / "judge_letter_map.json").read_text())


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
        m = re.match(r"-?\s*([A-F])\s*=\s*(\d+)", line)
        if m and current_ex is not None:
            letter, rank = m.group(1), int(m.group(2))
            result[current_ex][letter] = rank
    return result


def validate(rankings: dict[int, dict[str, int]], source: str) -> list[str]:
    errs = []
    for ex in range(1, 11):
        if ex not in rankings:
            errs.append(f"{source}: missing Example {ex}")
            continue
        r = rankings[ex]
        if set(r.keys()) != set("ABCDEF"):
            errs.append(f"{source}: Example {ex} has keys {sorted(r.keys())}")
        if sorted(r.values()) != [1, 2, 3, 4, 5, 6]:
            errs.append(f"{source}: Example {ex} ranks {sorted(r.values())}")
    return errs


def sign_test_p(n_plus: int, n_minus: int) -> float:
    """Two-sided binomial sign test with p=0.5."""
    n = n_plus + n_minus
    if n == 0:
        return 1.0
    k = min(n_plus, n_minus)

    def binom(n, k):
        return math.comb(n, k)

    tail = sum(binom(n, i) for i in range(0, k + 1))
    p_two_sided = min(1.0, 2.0 * tail / (2 ** n))
    return p_two_sided


def main() -> int:
    # discover rankings files
    candidates = sorted(ROOT.glob("judge_rankings_*.md"))
    human = ROOT / "rankings.md"
    if human.exists():
        # include only if the human actually filled in at least one rank line
        # (strictly: a line beginning with "- X=" followed by a digit)
        filled = re.findall(r"(?m)^-\s*[A-F]\s*=\s*\d", human.read_text())
        if filled:
            candidates.append(human)

    if not candidates:
        print("no ranking files found; fill rankings.md or wait for judge subagents")
        return 1

    # parse + validate
    per_judge: dict[str, dict[int, dict[str, int]]] = {}
    errs: list[str] = []
    for p in candidates:
        r = parse_ranking_file(p)
        errs.extend(validate(r, p.name))
        per_judge[p.name] = r

    if errs:
        print("VALIDATION ERRORS:")
        for e in errs:
            print(" -", e)
        return 2

    # un-blind: for each judge × example × letter, look up (id, condition)
    # aggregate: per-condition mean rank per example and overall
    condition_ranks_per_example: dict[int, dict[str, list[int]]] = {
        ex: {"control": [], "treatment": []} for ex in range(1, 11)
    }
    condition_ranks_overall: dict[str, list[int]] = {"control": [], "treatment": []}

    # per-judge per-example deltas (treatment mean - control mean)
    deltas_by_judge_ex: dict[str, dict[int, float]] = defaultdict(dict)

    for judge_name, rankings in per_judge.items():
        for ex in range(1, 11):
            for letter, rank in rankings[ex].items():
                anon_id = LETTER_MAP[f"{ex}.{letter}"]
                cond = MANIFEST[anon_id]["condition"]
                condition_ranks_per_example[ex][cond].append(rank)
                condition_ranks_overall[cond].append(rank)
            ctrl = [
                rank
                for letter, rank in rankings[ex].items()
                if MANIFEST[LETTER_MAP[f"{ex}.{letter}"]]["condition"] == "control"
            ]
            treat = [
                rank
                for letter, rank in rankings[ex].items()
                if MANIFEST[LETTER_MAP[f"{ex}.{letter}"]]["condition"] == "treatment"
            ]
            deltas_by_judge_ex[judge_name][ex] = (
                sum(treat) / len(treat) - sum(ctrl) / len(ctrl)
            )

    # summary
    lines: list[str] = []
    lines.append("# Refactor Completion Bias — Analysis\n")
    lines.append(
        f"Judges: {len(per_judge)} ({', '.join(per_judge)}). "
        "Each judge ranked 6 variants per example (1=best, 6=worst) blind to condition.\n\n"
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
    per_ex_deltas = []
    for ex in range(1, 11):
        c = condition_ranks_per_example[ex]["control"]
        t = condition_ranks_per_example[ex]["treatment"]
        cm = sum(c) / len(c)
        tm = sum(t) / len(t)
        d = tm - cm
        per_ex_deltas.append(d)
        lines.append(f"| {ex} | {cm:.2f} | {tm:.2f} | {d:+.2f} |\n")
    lines.append("\n")

    # sign test across examples: count how many examples treatment beat control (delta < 0)
    n_treatment_wins = sum(1 for d in per_ex_deltas if d < 0)
    n_control_wins = sum(1 for d in per_ex_deltas if d > 0)
    n_ties = sum(1 for d in per_ex_deltas if d == 0)
    p = sign_test_p(n_treatment_wins, n_control_wins)
    lines.append("## Sign test across examples\n\n")
    lines.append(
        f"Treatment wins (lower mean rank): **{n_treatment_wins}** examples. "
        f"Control wins: **{n_control_wins}**. Ties: **{n_ties}**. "
        f"Two-sided binomial p ≈ **{p:.3f}**.\n\n"
    )
    if p >= 0.05:
        lines.append(
            "- Not statistically significant at α=0.05 with only 10 examples; "
            "treat as exploratory.\n\n"
        )
    else:
        lines.append("- Statistically significant at α=0.05.\n\n")

    lines.append("## Per-judge per-example deltas (treatment mean − control mean)\n\n")
    lines.append("| Example | " + " | ".join(per_judge.keys()) + " |\n")
    lines.append("|---" * (1 + len(per_judge)) + "|\n")
    for ex in range(1, 11):
        row = [f"{ex}"]
        for judge_name in per_judge:
            row.append(f"{deltas_by_judge_ex[judge_name][ex]:+.2f}")
        lines.append("| " + " | ".join(row) + " |\n")
    lines.append("\n")

    lines.append("## Caveats\n\n")
    lines.append(
        "- Judges are themselves Claude subagents; this is Claude-rating-Claude and "
        "may share systematic biases with the code producers.\n"
    )
    lines.append(
        "- 10 examples × 2 conditions × 3 runs = 60 outputs. Variance between runs is "
        "not separated from variance between conditions in the headline number; "
        "the sign test across examples partially controls for this by treating each "
        "example as one unit.\n"
    )
    lines.append(
        "- A human judge would be the gold standard. `rankings.md` is the template "
        "for that.\n"
    )

    (ROOT / "analysis.md").write_text("".join(lines))
    print("wrote analysis.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
