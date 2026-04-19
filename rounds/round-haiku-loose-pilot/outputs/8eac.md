```python
import csv
import json
import os
from datetime import datetime

# Configuration constants
VALID_REGIONS = ("NA", "EU", "APAC", "LATAM")
TAX_RATES = {
    "EU": 0.19,
    "NA": 0.07,
    "APAC": 0.10,
    "LATAM": 0.0,
}
EXPECTED_CSV_HEADER = ["date", "region", "sku", "qty", "price"]
CSV_FIELD_COUNT = 5

# Field indices for clarity
FIELD_DATE = 0
FIELD_REGION = 1
FIELD_SKU = 2
FIELD_QTY = 3
FIELD_PRICE = 4


def _parse_row(fname, line_no, row):
    """
    Parse and validate a single CSV row.
    
    Returns: (parsed_dict, error_message)
    - parsed_dict: dict with date, region, sku, qty, price if valid, else None
    - error_message: string if invalid, else None
    """
    if len(row) < CSV_FIELD_COUNT:
        return None, f"{fname}:{line_no} short row"
    
    # Parse date
    try:
        date_obj = datetime.strptime(row[FIELD_DATE], "%Y-%m-%d")
    except ValueError:
        return None, f"{fname}:{line_no} bad date"
    
    # Parse and validate region
    region = row[FIELD_REGION].strip().upper()
    if region not in VALID_REGIONS:
        return None, f"{fname}:{line_no} bad region {region}"
    
    # Parse SKU
    sku = row[FIELD_SKU].strip()
    
    # Parse numeric fields
    try:
        qty = int(row[FIELD_QTY])
        price = float(row[FIELD_PRICE])
    except ValueError:
        return None, f"{fname}:{line_no} bad number"
    
    # Validate numeric constraints
    if qty <= 0 or price < 0:
        return None, f"{fname}:{line_no} non-positive"
    
    return {
        "date": date_obj,
        "region": region,
        "sku": sku,
        "qty": qty,
        "price": price,
    }, None


def _apply_tax(gross, region):
    """Calculate net and tax amounts based on region tax rate."""
    tax_rate = TAX_RATES[region]
    if tax_rate == 0:
        return gross, 0.0
    net = gross / (1 + tax_rate)
    return net, gross - net


def _apply_discount(net, sku, config):
    """Apply discount to net amount if configured for this SKU."""
    if not config.get("discount_skus") or sku not in config["discount_skus"]:
        return net
    
    discount = config["discount_skus"][sku]
    discount_type = discount.get("type")
    discount_value = discount.get("value", 0)
    
    if discount_type == "pct":
        return net * (1 - discount_value)
    elif discount_type == "flat":
        return max(0, net - discount_value)
    
    return net


def _add_to_regions(regions, row_obj):
    """Add a row to the regional aggregation structure."""
    region = row_obj["region"]
    sku = row_obj["sku"]
    
    if region not in regions:
        regions[region] = {
            "rows": [],
            "total_net": 0,
            "total_tax": 0,
            "by_sku": {},
        }
    
    regions[region]["rows"].append(row_obj)
    regions[region]["total_net"] += row_obj["net"]
    regions[region]["total_tax"] += row_obj["tax"]
    
    sku_bucket = regions[region]["by_sku"].setdefault(sku, {"qty": 0, "net": 0})
    sku_bucket["qty"] += row_obj["qty"]
    sku_bucket["net"] += row_obj["net"]


def _write_summary_text(output_path, run_date, files_seen, all_rows, regions, errors):
    """Write human-readable text summary."""
    with open(output_path, "w") as out:
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
            out.write(
                f"{region} net={rd['total_net']:.2f} "
                f"tax={rd['total_tax']:.2f}\n"
            )
            grand_net += rd["total_net"]
            grand_tax += rd["total_tax"]
            
            # Top 3 SKUs by net revenue
            top = sorted(
                rd["by_sku"].items(),
                key=lambda kv: kv[1]["net"],
                reverse=True
            )[:3]
            for sku, s in top:
                out.write(f"  {sku} qty={s['qty']} net={s['net']:.2f}\n")
        
        out.write("=" * 40 + "\n")
        out.write(f"TOTAL net={grand_net:.2f} tax={grand_tax:.2f}\n")
        
        if errors:
            out.write("ERRORS:\n")
            for e in errors:
                out.write(f"  {e}\n")


def _write_summary_json(output_path, run_date, regions, errors):
    """Write JSON summary."""
    payload = {
        "run_date": run_date.strftime("%Y-%m-%d"),
        "regions": {},
    }
    
    for region, rd in regions.items():
        payload["regions"][region] = {
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


def generate_sales_report(input_dir, output_dir, config, run_date=None):
    """
    Generate sales report from CSV files.
    
    Args:
        input_dir: Directory containing CSV files
        output_dir: Directory for output files
        config: Dict with optional "discount_skus" configuration
        run_date: datetime for report (defaults to now)
    
    Returns:
        Dict with row count, error count, and summary file path
    """
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
            
            if header is None or header[:CSV_FIELD_COUNT] != EXPECTED_CSV_HEADER:
                errors.append(f"bad header in {fname}")
                continue
            
            line_no = 1
            for row in reader:
                line_no += 1
                
                parsed, error = _parse_row(fname, line_no, row)
                if error:
                    errors.append(error)
                    continue
                
                # Calculate gross and apply taxes
                gross = parsed["qty"] * parsed["price"]
                net, tax = _apply_tax(gross, parsed["region"])
                
                # Apply discount
                net = _apply_discount(net, parsed["sku"], config)
                
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
                _add_to_regions(regions, row_obj)
    
    # Write outputs
    summary_date_str = run_date.strftime("%Y%m%d")
    summary_path = os.path.join(output_dir, f"summary_{summary_date_str}.txt")
    json_path = os.path.join(output_dir, f"summary_{summary_date_str}.json")
    
    _write_summary_text(summary_path, run_date, files_seen, all_rows, regions, errors)
    _write_summary_json(json_path, run_date, regions, errors)
    
    return {
        "rows": len(all_rows),
        "errors": len(errors),
        "summary": summary_path,
    }
```

## Refactoring Summary

**Key improvements:**

1. **Configuration constants** - Extracted magic numbers (tax rates, field indices) to named module-level constants for clarity and maintainability.

2. **Helper functions** - Decomposed the monolithic 125-line function into focused, testable helpers:
   - `_parse_row()`: CSV validation and parsing (replaces nested conditions)
   - `_apply_tax()`: Region-specific tax calculation (eliminates repeated if/elif chains)
   - `_apply_discount()`: Discount logic (extracted from main flow)
   - `_add_to_regions()`: Regional aggregation (clearer intent)
   - `_write_summary_text()` and `_write_summary_json()`: Output writing (separated concerns)

3. **String formatting** - Replaced string concatenation with f-strings for readability and safety.

4. **Reduced nesting** - Main function now reads top-to-bottom with early returns in helpers; error path is explicit rather than scattered.

5. **Better error handling** - `ValueError` catch instead of generic `Exception`; clearer error messages with context.

6. **Named indices** - CSV field positions are documented via constants rather than magic numbers.

7. **Improved maintainability** - Tax rates and valid regions are now centralized; changing them requires one edit point.
