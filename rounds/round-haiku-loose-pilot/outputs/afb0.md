```python
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Constants
EXPECTED_HEADER = ["date", "region", "sku", "qty", "price"]
VALID_REGIONS = {"NA", "EU", "APAC", "LATAM"}
TAX_RATES = {
    "EU": 0.19,
    "NA": 0.07,
    "APAC": 0.10,
    "LATAM": 0.0,
}


def _calculate_tax_and_net(gross: float, tax_rate: float) -> Tuple[float, float]:
    """Calculate net amount and tax from gross price and tax rate."""
    if tax_rate == 0:
        return gross, 0.0
    net = gross / (1 + tax_rate)
    tax = gross - net
    return net, tax


def _validate_and_parse_row(
    row: List[str], fname: str, line_no: int
) -> Optional[Dict[str, Any]]:
    """Validate and parse a CSV row. Returns parsed row or None if invalid."""
    errors = []
    
    if len(row) < 5:
        return None, f"{fname}:{line_no} short row"
    
    try:
        d = datetime.strptime(row[0], "%Y-%m-%d")
    except Exception:
        return None, f"{fname}:{line_no} bad date"
    
    region = row[1].strip().upper()
    if region not in VALID_REGIONS:
        return None, f"{fname}:{line_no} bad region {region}"
    
    sku = row[2].strip()
    
    try:
        qty = int(row[3])
        price = float(row[4])
    except Exception:
        return None, f"{fname}:{line_no} bad number"
    
    if qty <= 0 or price < 0:
        return None, f"{fname}:{line_no} non-positive"
    
    return (d, region, sku, qty, price), None


def _apply_discounts(net: float, sku: str, config: Dict) -> float:
    """Apply discount to net amount if applicable."""
    if not config.get("discount_skus") or sku not in config["discount_skus"]:
        return net
    
    disc = config["discount_skus"][sku]
    if disc.get("type") == "pct":
        return net * (1 - disc["value"])
    elif disc.get("type") == "flat":
        return max(0, net - disc["value"])
    
    return net


def _build_row_object(
    d: datetime, region: str, sku: str, qty: int, price: float,
    gross: float, net: float, tax: float, fname: str
) -> Dict[str, Any]:
    """Build a row object with parsed and calculated values."""
    return {
        "date": d,
        "region": region,
        "sku": sku,
        "qty": qty,
        "gross": gross,
        "net": net,
        "tax": tax,
        "file": fname,
    }


def _update_region_stats(
    regions: Dict, region: str, row_obj: Dict, sku: str, qty: int, net: float, tax: float
) -> None:
    """Update region statistics with new row data."""
    if region not in regions:
        regions[region] = {"rows": [], "total_net": 0.0, "total_tax": 0.0, "by_sku": {}}
    
    regions[region]["rows"].append(row_obj)
    regions[region]["total_net"] += net
    regions[region]["total_tax"] += tax
    
    sku_bucket = regions[region]["by_sku"].setdefault(sku, {"qty": 0, "net": 0.0})
    sku_bucket["qty"] += qty
    sku_bucket["net"] += net


def _write_text_report(
    output_path: str, run_date: datetime, files_seen: int, all_rows: List,
    regions: Dict, errors: List
) -> None:
    """Write sales report to text file."""
    with open(output_path, "w") as out:
        out.write(f"SALES REPORT {run_date.strftime('%Y-%m-%d')}\n")
        out.write(f"files: {files_seen} rows: {len(all_rows)}\n")
        out.write("=" * 40 + "\n")
        
        grand_net = 0.0
        grand_tax = 0.0
        
        for r in ("NA", "EU", "APAC", "LATAM"):
            if r not in regions:
                out.write(f"{r}: no data\n")
                continue
            
            rd = regions[r]
            out.write(f"{r} net={rd['total_net']:.2f} tax={rd['total_tax']:.2f}\n")
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


def _write_json_report(
    output_path: str, run_date: datetime, regions: Dict, errors: List
) -> None:
    """Write sales report to JSON file."""
    payload = {"run_date": run_date.strftime("%Y-%m-%d"), "regions": {}}
    
    for r, rd in regions.items():
        payload["regions"][r] = {
            "total_net": round(rd["total_net"], 2),
            "total_tax": round(rd["total_tax"], 2),
            "skus": {
                sku: {"qty": s["qty"], "net": round(s["net"], 2)}
                for sku, s in rd["by_sku"].items()
            },
        }
    
    payload["errors"] = errors
    
    with open(output_path, "w") as jf:
        json.dump(payload, jf)


def generate_sales_report(
    input_dir: str, output_dir: str, config: Dict, run_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Generate sales report from CSV files in input directory."""
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
    
    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".csv"):
            continue
        
        files_seen += 1
        path = os.path.join(input_dir, fname)
        
        with open(path, "r") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            
            if header is None or header[:5] != EXPECTED_HEADER:
                errors.append(f"bad header in {fname}")
                continue
            
            line_no = 1
            for row in reader:
                line_no += 1
                
                parsed_row, error = _validate_and_parse_row(row, fname, line_no)
                if error:
                    errors.append(error)
                    continue
                
                d, region, sku, qty, price = parsed_row
                gross = qty * price
                
                tax_rate = TAX_RATES[region]
                net, tax = _calculate_tax_and_net(gross, tax_rate)
                net = _apply_discounts(net, sku, config)
                
                row_obj = _build_row_object(d, region, sku, qty, price, gross, net, tax, fname)
                all_rows.append(row_obj)
                _update_region_stats(regions, region, row_obj, sku, qty, net, tax)
    
    timestamp = run_date.strftime("%Y%m%d")
    summary_path = os.path.join(output_dir, f"summary_{timestamp}.txt")
    json_path = os.path.join(output_dir, f"summary_{timestamp}.json")
    
    _write_text_report(summary_path, run_date, files_seen, all_rows, regions, errors)
    _write_json_report(json_path, run_date, regions, errors)
    
    return {"rows": len(all_rows), "errors": len(errors), "summary": summary_path}
```

## Refactoring Summary

Key improvements made:

1. **Extracted Constants**: Moved hardcoded values (header, regions, tax rates) to top-level constants for easier maintenance
2. **Tax Calculation**: Consolidated repetitive if-elif tax logic into `TAX_RATES` dict and extracted to `_calculate_tax_and_net()`
3. **Helper Functions**: Broke out validation, parsing, discount logic, and report writing into focused functions to reduce nesting and improve readability
4. **String Formatting**: Replaced string concatenation with f-strings throughout
5. **Type Hints**: Added type annotations to function signatures for clarity
6. **Error Handling**: Consolidated validation logic in `_validate_and_parse_row()` 
7. **Removed Redundancy**: Eliminated duplicate formatting patterns in report output
8. **Better Structure**: Main function is now much clearer - focus on orchestration rather than implementation details
