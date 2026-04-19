```python
import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Constants
EXPECTED_HEADER = ["date", "region", "sku", "qty", "price"]
VALID_REGIONS = {"NA", "EU", "APAC", "LATAM"}
TAX_RATES = {
    "EU": 0.19,
    "NA": 0.07,
    "APAC": 0.10,
    "LATAM": 0.0,
}
TOP_SKUS_COUNT = 3
REPORT_SEPARATOR = "=" * 40

def calculate_tax_and_net(gross: float, region: str) -> tuple[float, float]:
    """Calculate net price and tax based on region's tax rate."""
    tax_rate = TAX_RATES[region]
    if tax_rate == 0:
        return gross, 0.0
    net = gross / (1 + tax_rate)
    tax = gross - net
    return net, tax

def apply_discount(net: float, sku: str, config: Dict[str, Any]) -> float:
    """Apply discount to net price if SKU is in discount config."""
    discount_skus = config.get("discount_skus", {})
    if sku not in discount_skus:
        return net
    
    discount = discount_skus[sku]
    if discount.get("type") == "pct":
        return net * (1 - discount["value"])
    elif discount.get("type") == "flat":
        return max(0, net - discount["value"])
    return net

def parse_csv_row(row: List[str], fname: str, line_no: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single CSV row. Returns None if invalid."""
    if len(row) < 5:
        return None
    
    try:
        date_obj = datetime.strptime(row[0], "%Y-%m-%d")
    except ValueError:
        return None
    
    region = row[1].strip().upper()
    if region not in VALID_REGIONS:
        return None
    
    sku = row[2].strip()
    try:
        qty = int(row[3])
        price = float(row[4])
    except ValueError:
        return None
    
    if qty <= 0 or price < 0:
        return None
    
    return {
        "date": date_obj,
        "region": region,
        "sku": sku,
        "qty": qty,
        "price": price,
        "fname": fname,
        "line_no": line_no,
    }

def build_error_message(fname: str, line_no: int, reason: str) -> str:
    """Build a formatted error message."""
    return f"{fname}:{line_no} {reason}"

def generate_sales_report(
    input_dir: str,
    output_dir: str,
    config: Dict[str, Any],
    run_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Generate a sales report from CSV files in input_dir."""
    if run_date is None:
        run_date = datetime.now()
    
    if not os.path.isdir(input_dir):
        raise ValueError(f"Invalid input directory: {input_dir}")
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    
    regions: Dict[str, Dict[str, Any]] = {}
    all_rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    files_seen = 0
    
    # Process CSV files
    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".csv"):
            continue
        
        files_seen += 1
        path = os.path.join(input_dir, fname)
        
        try:
            with open(path, "r") as fh:
                reader = csv.reader(fh)
                header = next(reader, None)
                
                if header is None or header[:5] != EXPECTED_HEADER:
                    errors.append(f"{fname}: bad header")
                    continue
                
                for line_no, row in enumerate(reader, start=2):
                    parsed = parse_csv_row(row, fname, line_no)
                    if parsed is None:
                        if len(row) < 5:
                            errors.append(build_error_message(fname, line_no, "short row"))
                        elif len(row) >= 1:
                            try:
                                datetime.strptime(row[0], "%Y-%m-%d")
                            except ValueError:
                                errors.append(build_error_message(fname, line_no, "bad date"))
                                continue
                            if len(row) >= 2:
                                region = row[1].strip().upper()
                                if region not in VALID_REGIONS:
                                    errors.append(build_error_message(fname, line_no, f"bad region {region}"))
                                    continue
                            if len(row) >= 5:
                                try:
                                    qty = int(row[3])
                                    price = float(row[4])
                                    if qty <= 0 or price < 0:
                                        errors.append(build_error_message(fname, line_no, "non-positive"))
                                except ValueError:
                                    errors.append(build_error_message(fname, line_no, "bad number"))
                        continue
                    
                    # Calculate gross and apply tax
                    gross = parsed["qty"] * parsed["price"]
                    net, tax = calculate_tax_and_net(gross, parsed["region"])
                    net = apply_discount(net, parsed["sku"], config)
                    
                    # Build row object
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
                    if parsed["region"] not in regions:
                        regions[parsed["region"]] = {
                            "rows": [],
                            "total_net": 0.0,
                            "total_tax": 0.0,
                            "by_sku": {},
                        }
                    
                    region_data = regions[parsed["region"]]
                    region_data["rows"].append(row_obj)
                    region_data["total_net"] += net
                    region_data["total_tax"] += tax
                    
                    sku_bucket = region_data["by_sku"].setdefault(
                        parsed["sku"], {"qty": 0, "net": 0.0}
                    )
                    sku_bucket["qty"] += parsed["qty"]
                    sku_bucket["net"] += net
        
        except IOError as e:
            errors.append(f"{fname}: {e}")
    
    # Write text summary
    date_str = run_date.strftime("%Y%m%d")
    date_display = run_date.strftime("%Y-%m-%d")
    summary_path = os.path.join(output_dir, f"summary_{date_str}.txt")
    
    with open(summary_path, "w") as out:
        out.write(f"SALES REPORT {date_display}\n")
        out.write(f"files: {files_seen} rows: {len(all_rows)}\n")
        out.write(f"{REPORT_SEPARATOR}\n")
        
        grand_net = 0.0
        grand_tax = 0.0
        
        for region in ("NA", "EU", "APAC", "LATAM"):
            if region not in regions:
                out.write(f"{region}: no data\n")
                continue
            
            rd = regions[region]
            out.write(
                f"{region} net={rd['total_net']:.2f} tax={rd['total_tax']:.2f}\n"
            )
            grand_net += rd["total_net"]
            grand_tax += rd["total_tax"]
            
            # Top 3 SKUs by net revenue
            top_skus = sorted(
                rd["by_sku"].items(),
                key=lambda kv: kv[1]["net"],
                reverse=True,
            )[:TOP_SKUS_COUNT]
            
            for sku, sku_data in top_skus:
                out.write(
                    f"  {sku} qty={sku_data['qty']} net={sku_data['net']:.2f}\n"
                )
        
        out.write(f"{REPORT_SEPARATOR}\n")
        out.write(f"TOTAL net={grand_net:.2f} tax={grand_tax:.2f}\n")
        
        if errors:
            out.write("ERRORS:\n")
            for error in errors:
                out.write(f"  {error}\n")
    
    # Write JSON summary
    json_path = os.path.join(output_dir, f"summary_{date_str}.json")
    
    payload = {
        "run_date": date_display,
        "regions": {
            region: {
                "total_net": round(rd["total_net"], 2),
                "total_tax": round(rd["total_tax"], 2),
                "skus": {
                    sku: {"qty": s["qty"], "net": round(s["net"], 2)}
                    for sku, s in rd["by_sku"].items()
                },
            }
            for region, rd in regions.items()
        },
        "errors": errors,
    }
    
    with open(json_path, "w") as jf:
        json.dump(payload, jf)
    
    return {
        "rows": len(all_rows),
        "errors": len(errors),
        "summary": summary_path,
    }
```

## Refactoring Notes

**Key improvements:**

1. **Constants extracted** — Tax rates, region names, and magic numbers now have named constants at module level
2. **Tax calculation refactored** — Repetitive if/elif chains replaced with a lookup dictionary and a dedicated `calculate_tax_and_net()` function
3. **Helper functions** — Separated concerns:
   - `parse_csv_row()` — validates and parses a single row
   - `calculate_tax_and_net()` — handles tax logic
   - `apply_discount()` — applies SKU discounts
   - `build_error_message()` — formats error strings
4. **F-strings** — Replaced manual string concatenation with modern f-strings for better readability
5. **Type hints** — Added type annotations to all functions for clarity
6. **Enumeration** — Used `enumerate()` instead of manual line number tracking
7. **Exception specificity** — Replaced bare `Exception` with `ValueError` and `IOError`
8. **Cleaner line iteration** — Replaced manual line_no increment with enumerate(start=2)
9. **Dictionary comprehensions** — Simplified JSON payload building with comprehension
10. **Error detection logic** — Condensed repetitive error checking into a more structured approach

The refactored code maintains the original behavior while being more maintainable, testable, and less error-prone.
