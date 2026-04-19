# Example 11: Legacy batch report generator (god function)

```python
import csv
import json
import os
from datetime import datetime

def generate_sales_report(input_dir, output_dir, config, run_date=None):
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
            if header is None or header[:5] != ["date", "region", "sku", "qty", "price"]:
                errors.append("bad header in " + fname)
                continue
            line_no = 1
            for row in reader:
                line_no += 1
                if len(row) < 5:
                    errors.append(fname + ":" + str(line_no) + " short row")
                    continue
                try:
                    d = datetime.strptime(row[0], "%Y-%m-%d")
                except Exception:
                    errors.append(fname + ":" + str(line_no) + " bad date")
                    continue
                region = row[1].strip().upper()
                if region not in ("NA", "EU", "APAC", "LATAM"):
                    errors.append(fname + ":" + str(line_no) + " bad region " + region)
                    continue
                sku = row[2].strip()
                try:
                    qty = int(row[3])
                    price = float(row[4])
                except Exception:
                    errors.append(fname + ":" + str(line_no) + " bad number")
                    continue
                if qty <= 0 or price < 0:
                    errors.append(fname + ":" + str(line_no) + " non-positive")
                    continue
                gross = qty * price
                if region == "EU":
                    net = gross / 1.19
                    tax = gross - net
                elif region == "NA":
                    net = gross / 1.07
                    tax = gross - net
                elif region == "APAC":
                    net = gross / 1.10
                    tax = gross - net
                else:
                    net = gross
                    tax = 0.0
                if config.get("discount_skus") and sku in config["discount_skus"]:
                    disc = config["discount_skus"][sku]
                    if disc.get("type") == "pct":
                        net = net * (1 - disc["value"])
                    elif disc.get("type") == "flat":
                        net = max(0, net - disc["value"])
                row_obj = {
                    "date": d, "region": region, "sku": sku,
                    "qty": qty, "gross": gross, "net": net, "tax": tax,
                    "file": fname,
                }
                all_rows.append(row_obj)
                regions.setdefault(region, {"rows": [], "total_net": 0, "total_tax": 0, "by_sku": {}})
                regions[region]["rows"].append(row_obj)
                regions[region]["total_net"] += net
                regions[region]["total_tax"] += tax
                sku_bucket = regions[region]["by_sku"].setdefault(sku, {"qty": 0, "net": 0})
                sku_bucket["qty"] += qty
                sku_bucket["net"] += net
    summary_path = os.path.join(output_dir, "summary_" + run_date.strftime("%Y%m%d") + ".txt")
    with open(summary_path, "w") as out:
        out.write("SALES REPORT " + run_date.strftime("%Y-%m-%d") + "\n")
        out.write("files: " + str(files_seen) + " rows: " + str(len(all_rows)) + "\n")
        out.write("=" * 40 + "\n")
        grand_net = 0
        grand_tax = 0
        for r in ("NA", "EU", "APAC", "LATAM"):
            if r not in regions:
                out.write(r + ": no data\n")
                continue
            rd = regions[r]
            out.write(r + " net=" + format(rd["total_net"], ".2f") +
                      " tax=" + format(rd["total_tax"], ".2f") + "\n")
            grand_net += rd["total_net"]
            grand_tax += rd["total_tax"]
            top = sorted(rd["by_sku"].items(), key=lambda kv: kv[1]["net"], reverse=True)[:3]
            for sku, s in top:
                out.write("  " + sku + " qty=" + str(s["qty"]) +
                          " net=" + format(s["net"], ".2f") + "\n")
        out.write("=" * 40 + "\n")
        out.write("TOTAL net=" + format(grand_net, ".2f") +
                  " tax=" + format(grand_tax, ".2f") + "\n")
        if errors:
            out.write("ERRORS:\n")
            for e in errors:
                out.write("  " + e + "\n")
    json_path = os.path.join(output_dir, "summary_" + run_date.strftime("%Y%m%d") + ".json")
    with open(json_path, "w") as jf:
        payload = {"run_date": run_date.strftime("%Y-%m-%d"), "regions": {}}
        for r, rd in regions.items():
            payload["regions"][r] = {
                "total_net": round(rd["total_net"], 2),
                "total_tax": round(rd["total_tax"], 2),
                "skus": {sku: {"qty": s["qty"], "net": round(s["net"], 2)}
                         for sku, s in rd["by_sku"].items()},
            }
        payload["errors"] = errors
        json.dump(payload, jf)
    return {"rows": len(all_rows), "errors": len(errors), "summary": summary_path}
```
