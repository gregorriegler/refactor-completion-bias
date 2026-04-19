```python
import csv
import json
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Constants
VALID_REGIONS = ("NA", "EU", "APAC", "LATAM")
TAX_RATES = {"EU": 0.19, "NA": 0.07, "APAC": 0.10, "LATAM": 0.0}
VALID_HEADER = ["date", "region", "sku", "qty", "price"]
DATE_FORMAT = "%Y-%m-%d"


@dataclass
class SalesRow:
    date: datetime
    region: str
    sku: str
    qty: int
    price: float
    file: str
    gross: float = None
    net: float = None
    tax: float = None

    def __post_init__(self):
        if self.gross is None:
            self.gross = self.qty * self.price
        if self.net is None or self.tax is None:
            self._calculate_net_and_tax()

    def _calculate_net_and_tax(self):
        tax_rate = TAX_RATES.get(self.region, 0.0)
        divisor = 1 + tax_rate if tax_rate > 0 else 1
        self.net = self.gross / divisor
        self.tax = self.gross - self.net

    def apply_discount(self, discount_config: dict):
        """Apply SKU-based discount if applicable."""
        if not discount_config or self.sku not in discount_config:
            return
        disc = discount_config[self.sku]
        if disc.get("type") == "pct":
            self.net = self.net * (1 - disc["value"])
        elif disc.get("type") == "flat":
            self.net = max(0, self.net - disc["value"])


class SalesReportGenerator:
    def __init__(self, input_dir: str, output_dir: str, config: dict, run_date: Optional[datetime] = None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config = config
        self.run_date = run_date or datetime.now()
        self.validate_paths()
        
        self.all_rows: List[SalesRow] = []
        self.regions: Dict[str, dict] = {}
        self.errors: List[str] = []
        self.files_seen = 0

    def validate_paths(self):
        """Validate and prepare directories."""
        if not os.path.isdir(self.input_dir):
            raise ValueError("bad input dir")
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

    def validate_header(self, header: Optional[List[str]], fname: str) -> bool:
        """Validate CSV header."""
        if header is None or header[:5] != VALID_HEADER:
            self.errors.append(f"bad header in {fname}")
            return False
        return True

    def validate_and_parse_row(self, row: List[str], fname: str, line_no: int) -> Optional[dict]:
        """Validate and parse a CSV row. Returns parsed row data or None on error."""
        if len(row) < 5:
            self.errors.append(f"{fname}:{line_no} short row")
            return None

        # Parse date
        try:
            d = datetime.strptime(row[0], DATE_FORMAT)
        except Exception:
            self.errors.append(f"{fname}:{line_no} bad date")
            return None

        # Validate region
        region = row[1].strip().upper()
        if region not in VALID_REGIONS:
            self.errors.append(f"{fname}:{line_no} bad region {region}")
            return None

        # Parse SKU
        sku = row[2].strip()

        # Parse numeric fields
        try:
            qty = int(row[3])
            price = float(row[4])
        except Exception:
            self.errors.append(f"{fname}:{line_no} bad number")
            return None

        # Validate numeric constraints
        if qty <= 0 or price < 0:
            self.errors.append(f"{fname}:{line_no} non-positive")
            return None

        return {"date": d, "region": region, "sku": sku, "qty": qty, "price": price}

    def process_csv_file(self, fname: str):
        """Process a single CSV file."""
        path = os.path.join(self.input_dir, fname)
        with open(path, "r") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if not self.validate_header(header, fname):
                return

            for line_no, row in enumerate(reader, start=2):  # Line numbering starts at 2 (after header)
                parsed = self.validate_and_parse_row(row, fname, line_no)
                if parsed is None:
                    continue

                sales_row = SalesRow(**parsed, file=fname)
                sales_row.apply_discount(self.config.get("discount_skus"))
                self.all_rows.append(sales_row)
                self._aggregate_row(sales_row)

    def _aggregate_row(self, row: SalesRow):
        """Aggregate row into regional and SKU buckets."""
        region = row.region
        if region not in self.regions:
            self.regions[region] = {
                "rows": [],
                "total_net": 0,
                "total_tax": 0,
                "by_sku": {}
            }

        self.regions[region]["rows"].append(row)
        self.regions[region]["total_net"] += row.net
        self.regions[region]["total_tax"] += row.tax

        sku_bucket = self.regions[region]["by_sku"].setdefault(row.sku, {"qty": 0, "net": 0})
        sku_bucket["qty"] += row.qty
        sku_bucket["net"] += row.net

    def generate_reports(self) -> dict:
        """Process all CSV files and generate reports."""
        for fname in sorted(os.listdir(self.input_dir)):
            if not fname.endswith(".csv"):
                continue
            self.files_seen += 1
            self.process_csv_file(fname)

        self._write_text_report()
        self._write_json_report()

        return {"rows": len(self.all_rows), "errors": len(self.errors), "summary": self._get_summary_path("txt")}

    def _get_summary_path(self, ext: str) -> str:
        """Get the summary file path for the given extension."""
        filename = f"summary_{self.run_date.strftime('%Y%m%d')}.{ext}"
        return os.path.join(self.output_dir, filename)

    def _write_text_report(self):
        """Write summary report to text file."""
        with open(self._get_summary_path("txt"), "w") as out:
            out.write(f"SALES REPORT {self.run_date.strftime('%Y-%m-%d')}\n")
            out.write(f"files: {self.files_seen} rows: {len(self.all_rows)}\n")
            out.write("=" * 40 + "\n")

            grand_net, grand_tax = 0, 0
            for region in VALID_REGIONS:
                if region not in self.regions:
                    out.write(f"{region}: no data\n")
                    continue

                rd = self.regions[region]
                out.write(f"{region} net={rd['total_net']:.2f} tax={rd['total_tax']:.2f}\n")
                grand_net += rd["total_net"]
                grand_tax += rd["total_tax"]

                # Top 3 SKUs by net revenue
                top = sorted(rd["by_sku"].items(), key=lambda kv: kv[1]["net"], reverse=True)[:3]
                for sku, s in top:
                    out.write(f"  {sku} qty={s['qty']} net={s['net']:.2f}\n")

            out.write("=" * 40 + "\n")
            out.write(f"TOTAL net={grand_net:.2f} tax={grand_tax:.2f}\n")

            if self.errors:
                out.write("ERRORS:\n")
                for e in self.errors:
                    out.write(f"  {e}\n")

    def _write_json_report(self):
        """Write summary report to JSON file."""
        payload = {"run_date": self.run_date.strftime("%Y-%m-%d"), "regions": {}}
        for r, rd in self.regions.items():
            payload["regions"][r] = {
                "total_net": round(rd["total_net"], 2),
                "total_tax": round(rd["total_tax"], 2),
                "skus": {
                    sku: {"qty": s["qty"], "net": round(s["net"], 2)}
                    for sku, s in rd["by_sku"].items()
                },
            }
        payload["errors"] = self.errors

        with open(self._get_summary_path("json"), "w") as jf:
            json.dump(payload, jf)


def generate_sales_report(input_dir, output_dir, config, run_date=None):
    """Generate sales report from CSV files."""
    generator = SalesReportGenerator(input_dir, output_dir, config, run_date)
    return generator.generate_reports()
```

## Refactoring Notes

**Key improvements:**

1. **Extracted constants** — Tax rates, valid regions, date format, and header validation are now at module level, eliminating magic numbers and making configuration easy.

2. **Introduced dataclass** — `SalesRow` encapsulates row data and its validation/calculation logic, replacing ad-hoc dictionaries.

3. **Separated concerns** — Created `SalesReportGenerator` class to handle orchestration, file processing, aggregation, and output generation, breaking up the monolithic function.

4. **Reduced duplication** — Tax calculation (EU/NA/APAC branching) is now centralized in `SalesRow._calculate_net_and_tax()`.

5. **Extracted validation methods** — `validate_header()`, `validate_and_parse_row()` make the row-processing loop cleaner and testable.

6. **Improved formatting** — Switched to f-strings for better readability and maintainability.

7. **Clearer aggregation** — `_aggregate_row()` consolidates the region/SKU bucketing logic.

8. **Better encapsulation** — File path generation and report writing are now methods with clear responsibilities.

The refactored code maintains the original behavior while being more maintainable, testable, and extensible for future changes (e.g., adding new regions or discount types).
