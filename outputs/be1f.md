```python
import csv
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

VALID_REGIONS = ("NA", "EU", "APAC", "LATAM")
REQUIRED_HEADER = ["date", "region", "sku", "qty", "price"]
TAX_RATES = {"EU": 1.19, "NA": 1.07, "APAC": 1.10}


@dataclass
class SkuStats:
    qty: int = 0
    net: float = 0.0


@dataclass
class RegionStats:
    total_net: float = 0.0
    total_tax: float = 0.0
    by_sku: dict[str, SkuStats] = field(default_factory=dict)

    def add(self, sku: str, net: float, tax: float, qty: int) -> None:
        self.total_net += net
        self.total_tax += tax
        if sku not in self.by_sku:
            self.by_sku[sku] = SkuStats()
        self.by_sku[sku].qty += qty
        self.by_sku[sku].net += net


def _apply_tax(gross: float, region: str) -> tuple[float, float]:
    divisor = TAX_RATES.get(region, 1.0)
    net = gross / divisor
    return net, gross - net


def _apply_discount(net: float, sku: str, discount_skus: dict) -> float:
    disc = discount_skus.get(sku)
    if not disc:
        return net
    if disc.get("type") == "pct":
        return net * (1 - disc["value"])
    if disc.get("type") == "flat":
        return max(0.0, net - disc["value"])
    return net


def _parse_row(row: list[str], fname: str, line_no: int, errors: list[str]):
    if len(row) < 5:
        errors.append(f"{fname}:{line_no} short row")
        return None

    try:
        date = datetime.strptime(row[0], "%Y-%m-%d")
    except ValueError:
        errors.append(f"{fname}:{line_no} bad date")
        return None

    region = row[1].strip().upper()
    if region not in VALID_REGIONS:
        errors.append(f"{fname}:{line_no} bad region {region}")
        return None

    sku = row[2].strip()

    try:
        qty = int(row[3])
        price = float(row[4])
    except ValueError:
        errors.append(f"{fname}:{line_no} bad number")
        return None

    if qty <= 0 or price < 0:
        errors.append(f"{fname}:{line_no} non-positive")
        return None

    return {"date": date, "region": region, "sku": sku, "qty": qty, "price": price}


def _process_file(
    path: str,
    fname: str,
    config: dict,
    regions: dict[str, RegionStats],
    all_rows: list,
    errors: list[str],
) -> None:
    discount_skus = config.get("discount_skus", {})
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None or header[:5] != REQUIRED_HEADER:
            errors.append(f"bad header in {fname}")
            return

        for line_no, row in enumerate(reader, start=2):
            parsed = _parse_row(row, fname, line_no, errors)
            if parsed is None:
                continue

            region, sku, qty = parsed["region"], parsed["sku"], parsed["qty"]
            gross = qty * parsed["price"]
            net, tax = _apply_tax(gross, region)
            net = _apply_discount(net, sku, discount_skus)

            row_obj = {
                "date": parsed["date"], "region": region, "sku": sku,
                "qty": qty, "gross": gross, "net": net, "tax": tax, "file": fname,
            }
            all_rows.append(row_obj)
            regions.setdefault(region, RegionStats()).add(sku, net, tax, qty)


def _write_text_summary(
    out_path: str,
    run_date: datetime,
    files_seen: int,
    all_rows: list,
    regions: dict[str, RegionStats],
    errors: list[str],
) -> None:
    with open(out_path, "w") as out:
        out.write(f"SALES REPORT {run_date:%Y-%m-%d}\n")
        out.write(f"files: {files_seen} rows: {len(all_rows)}\n")
        out.write("=" * 40 + "\n")

        grand_net = grand_tax = 0.0
        for region in VALID_REGIONS:
            if region not in regions:
                out.write(f"{region}: no data\n")
                continue
            rd = regions[region]
            out.write(f"{region} net={rd.total_net:.2f} tax={rd.total_tax:.2f}\n")
            grand_net += rd.total_net
            grand_tax += rd.total_tax
            top3 = sorted(rd.by_sku.items(), key=lambda kv: kv[1].net, reverse=True)[:3]
            for sku, s in top3:
                out.write(f"  {sku} qty={s.qty} net={s.net:.2f}\n")

        out.write("=" * 40 + "\n")
        out.write(f"TOTAL net={grand_net:.2f} tax={grand_tax:.2f}\n")
        if errors:
            out.write("ERRORS:\n")
            for e in errors:
                out.write(f"  {e}\n")


def _write_json_summary(
    out_path: str,
    run_date: datetime,
    regions: dict[str, RegionStats],
    errors: list[str],
) -> None:
    payload = {
        "run_date": run_date.strftime("%Y-%m-%d"),
        "regions": {
            r: {
                "total_net": round(rd.total_net, 2),
                "total_tax": round(rd.total_tax, 2),
                "skus": {sku: {"qty": s.qty, "net": round(s.net, 2)}
                         for sku, s in rd.by_sku.items()},
            }
            for r, rd in regions.items()
        },
        "errors": errors,
    }
    with open(out_path, "w") as jf:
        json.dump(payload, jf)


def generate_sales_report(
    input_dir: str,
    output_dir: str,
    config: dict,
    run_date: Optional[datetime] = None,
) -> dict:
    if run_date is None:
        run_date = datetime.now()
    if not os.path.isdir(input_dir):
        raise ValueError(f"input_dir does not exist: {input_dir!r}")
    os.makedirs(output_dir, exist_ok=True)

    regions: dict[str, RegionStats] = {}
    all_rows: list = []
    errors: list[str] = []
    files_seen = 0

    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".csv"):
            continue
        files_seen += 1
        _process_file(
            os.path.join(input_dir, fname), fname, config,
            regions, all_rows, errors,
        )

    date_tag = run_date.strftime("%Y%m%d")
    summary_path = os.path.join(output_dir, f"summary_{date_tag}.txt")
    _write_text_summary(summary_path, run_date, files_seen, all_rows, regions, errors)
    _write_json_summary(os.path.join(output_dir, f"summary_{date_tag}.json"),
                        run_date, regions, errors)

    return {"rows": len(all_rows), "errors": len(errors), "summary": summary_path}
```

- **Decomposed into focused helpers** — `_parse_row`, `_process_file`, `_write_text_summary`, and `_write_json_summary` each do one thing, making the main function a thin coordinator and each piece independently testable.
- **Introduced `RegionStats` / `SkuStats` dataclasses** — replaces ad-hoc nested dicts with typed, self-documenting structures; `RegionStats.add()` encapsulates the accumulation logic that was previously inline.
- **Extracted constants** — `VALID_REGIONS`, `REQUIRED_HEADER`, and `TAX_RATES` are defined once at module level, eliminating the scattered literals and making the EU/NA/APAC tax table easy to extend.
- **Used f-strings and format specifiers throughout** — replaced the string-concatenation approach in error messages and report lines with `f"{value:.2f}"` etc., improving readability.
- **`os.makedirs(..., exist_ok=True)`** — removed the redundant `isdir` guard before `makedirs`; the flag handles both the "already exists" and "needs creating" cases atomically.
