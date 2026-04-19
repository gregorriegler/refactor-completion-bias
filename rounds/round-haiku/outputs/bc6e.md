```python
import csv
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

VALID_REGIONS = {"NA", "EU", "APAC", "LATAM"}
TAX_RATES = {"EU": 0.19, "NA": 0.07, "APAC": 0.10}


@dataclass
class SalesRow:
    date: datetime
    region: str
    sku: str
    qty: int
    gross: float
    net: float
    tax: float
    file: str


def _parse_and_validate_row(row: list, fname: str, line_no: int, errors: list) -> Optional[dict]:
    """Parse and validate a single CSV row. Returns dict on success, None on error."""
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


def _calculate_tax_and_net(gross: float, region: str) -> tuple[float, float]:
    """Calculate net and tax amounts based on region."""
    tax_rate = TAX_RATES.get(region, 0)
    if tax_rate == 0:
        return gross, 0.0
    net = gross / (1 + tax_rate)
    tax = gross - net
    return net, tax


def _apply_discount(net: float, sku: str, config: dict) -> float:
    """Apply discount to net amount if applicable."""
    discount_skus = config.get("discount_skus", {})
    if sku not in discount_skus:
        return net

    disc = discount_skus[sku]
    if disc.get("type") == "pct":
        return net * (1 - disc["value"])
    elif disc.get("type") == "flat":
        return max(0, net - disc["value"])
    return net


def generate_sales_report(input_dir: str, output_dir: str, config: dict, run_date: Optional[datetime] = None) -> dict:
    """Generate sales report from CSV files in input_dir."""
    if run_date is None:
        run_date = datetime.now()

    if not os.path.isdir(input_dir):
        raise ValueError("bad input dir")
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    regions = {}
    all_rows = []
    errors = []
    files_seen = 0

    # Process CSV files
    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".csv"):
            continue

        files_seen += 1
        path = os.path.join(input_dir, fname)

        with open(path, "r") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None or header[:5] != ["date", "region", "sku", "qty", "price"]:
                errors.append(f"bad header in {fname}")
                continue

            for line_no, row in enumerate(reader, start=2):
                parsed = _parse_and_validate_row(row, fname, line_no, errors)
                if parsed is None:
                    continue

                gross = parsed["qty"] * parsed["price"]
                net, tax = _calculate_tax_and_net(gross, parsed["region"])
                net = _apply_discount(net, parsed["sku"], config)

                row_obj = {
                    "date": parsed["date"],
                    "region": parsed["region"],
                    "sku": parsed["sku"],
                    "qty": parsed["qty"],
                    "gross": gross,
                    "net": net,
                    "tax": tax,
                    "file": fname,
                }
                all_rows.append(row_obj)

                # Update regional aggregates
                region_key = parsed["region"]
                if region_key not in regions:
                    regions[region_key] = {"rows": [], "total_net": 0, "total_tax": 0, "by_sku": {}}

                regions[region_key]["rows"].append(row_obj)
                regions[region_key]["total_net"] += net
                regions[region_key]["total_tax"] += tax

                sku_bucket = regions[region_key]["by_sku"].setdefault(parsed["sku"], {"qty": 0, "net": 0})
                sku_bucket["qty"] += parsed["qty"]
                sku_bucket["net"] += net

    # Write summary report
    _write_summary_report(output_dir, run_date, files_seen, all_rows, regions, errors)

    # Write JSON report
    _write_json_report(output_dir, run_date, regions, errors)

    return {"rows": len(all_rows), "errors": len(errors), "summary": os.path.join(output_dir, f"summary_{run_date.strftime('%Y%m%d')}.txt")}


def _write_summary_report(output_dir: str, run_date: datetime, files_seen: int, all_rows: list, regions: dict, errors: list) -> None:
    """Write human-readable summary report."""
    summary_path = os.path.join(output_dir, f"summary_{run_date.strftime('%Y%m%d')}.txt")

    with open(summary_path, "w") as out:
        out.write(f"SALES REPORT {run_date.strftime('%Y-%m-%d')}\n")
        out.write(f"files: {files_seen} rows: {len(all_rows)}\n")
        out.write("=" * 40 + "\n")

        grand_net = 0
        grand_tax = 0

        for region in VALID_REGIONS:
            if region not in regions:
                out.write(f"{region}: no data\n")
                continue

            rd = regions[region]
            out.write(f"{region} net={rd['total_net']:.2f} tax={rd['total_tax']:.2f}\n")
            grand_net += rd["total_net"]
            grand_tax += rd["total_tax"]

            top = sorted(rd["by_sku"].items(), key=lambda kv: kv[1]["net"], reverse=True)[:3]
            for sku, s in top:
                out.write(f"  {sku} qty={s['qty']} net={s['net']:.2f}\n")

        out.write("=" * 40 + "\n")
        out.write(f"TOTAL net={grand_net:.2f} tax={grand_tax:.2f}\n")

        if errors:
            out.write("ERRORS:\n")
            for e in errors:
                out.write(f"  {e}\n")


def _write_json_report(output_dir: str, run_date: datetime, regions: dict, errors: list) -> None:
    """Write JSON report."""
    json_path = os.path.join(output_dir, f"summary_{run_date.strftime('%Y%m%d')}.json")

    payload = {"run_date": run_date.strftime("%Y-%m-%d"), "regions": {}}
    for region, rd in regions.items():
        payload["regions"][region] = {
            "total_net": round(rd["total_net"], 2),
            "total_tax": round(rd["total_tax"], 2),
            "skus": {sku: {"qty": s["qty"], "net": round(s["net"], 2)} for sku, s in rd["by_sku"].items()},
        }
    payload["errors"] = errors

    with open(json_path, "w") as jf:
        json.dump(payload, jf)
```

Refactoring notes:
- Extracted tax calculation into a dedicated function with a constant-based tax rate lookup, replacing repetitive if/elif chains
- Created `_parse_and_validate_row()` to reduce nested parsing logic in the main loop
- Extracted discount application into a separate function for clarity
- Split report writing into `_write_summary_report()` and `_write_json_report()` helper functions to reduce main function size
- Added type hints for better code clarity
- Used f-strings instead of string concatenation for readability
- Introduced constants (`VALID_REGIONS`, `TAX_RATES`) to reduce magic strings and make region/tax logic more maintainable
