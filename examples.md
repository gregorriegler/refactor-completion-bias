# Python Refactoring Examples

Ten Python snippets with real code smells. Each is self-contained and meant to be refactored.

---

## Example 1: Long function with nested conditionals

```python
def process_order(order, user, inventory, coupons):
    total = 0
    if order and order.get("items"):
        for item in order["items"]:
            if item.get("sku") in inventory:
                stock = inventory[item["sku"]]
                if stock["qty"] >= item["qty"]:
                    price = stock["price"] * item["qty"]
                    if user.get("is_member"):
                        if user["tier"] == "gold":
                            price *= 0.8
                        elif user["tier"] == "silver":
                            price *= 0.9
                    if order.get("coupon") and order["coupon"] in coupons:
                        c = coupons[order["coupon"]]
                        if c["min"] <= price:
                            if c["type"] == "percent":
                                price *= (1 - c["value"])
                            else:
                                price -= c["value"]
                    total += price
                else:
                    raise ValueError("out of stock: " + item["sku"])
            else:
                raise ValueError("unknown sku: " + item["sku"])
    if total > 1000:
        total *= 0.95
    if user.get("country") == "DE":
        total *= 1.19
    elif user.get("country") == "US":
        total *= 1.07
    return round(total, 2)
```

---

## Example 2: Class with too many responsibilities

```python
import smtplib
import sqlite3
from email.message import EmailMessage

class UserManager:
    def __init__(self, db_path, smtp_host):
        self.conn = sqlite3.connect(db_path)
        self.smtp_host = smtp_host

    def register(self, email, password):
        if "@" not in email:
            raise ValueError("bad email")
        if len(password) < 8:
            raise ValueError("password too short")
        hashed = "".join(reversed(password)) + "_salt"
        cur = self.conn.cursor()
        cur.execute("INSERT INTO users(email, pw) VALUES (?, ?)", (email, hashed))
        self.conn.commit()
        msg = EmailMessage()
        msg["Subject"] = "Welcome"
        msg["To"] = email
        msg.set_content("Thanks for registering, " + email)
        with smtplib.SMTP(self.smtp_host) as s:
            s.send_message(msg)
        with open("audit.log", "a") as f:
            f.write("registered " + email + "\n")

    def login(self, email, password):
        hashed = "".join(reversed(password)) + "_salt"
        cur = self.conn.cursor()
        cur.execute("SELECT pw FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        if not row or row[0] != hashed:
            with open("audit.log", "a") as f:
                f.write("failed login " + email + "\n")
            return False
        with open("audit.log", "a") as f:
            f.write("login " + email + "\n")
        return True
```

---

## Example 3: Duplicated code across functions

```python
def export_users_csv(users, path):
    with open(path, "w") as f:
        f.write("id,name,email\n")
        for u in users:
            name = u["name"].replace(",", " ").replace("\n", " ")
            email = u["email"].replace(",", " ").replace("\n", " ")
            f.write(f"{u['id']},{name},{email}\n")

def export_orders_csv(orders, path):
    with open(path, "w") as f:
        f.write("id,user,total\n")
        for o in orders:
            user = o["user"].replace(",", " ").replace("\n", " ")
            f.write(f"{o['id']},{user},{o['total']}\n")

def export_products_csv(products, path):
    with open(path, "w") as f:
        f.write("sku,name,price\n")
        for p in products:
            name = p["name"].replace(",", " ").replace("\n", " ")
            f.write(f"{p['sku']},{name},{p['price']}\n")
```

---

## Example 4: Feature envy / data clumps

```python
class Invoice:
    def __init__(self, customer_name, customer_street, customer_city,
                 customer_zip, customer_country, items):
        self.customer_name = customer_name
        self.customer_street = customer_street
        self.customer_city = customer_city
        self.customer_zip = customer_zip
        self.customer_country = customer_country
        self.items = items

    def format_address(self):
        return (self.customer_name + "\n" +
                self.customer_street + "\n" +
                self.customer_zip + " " + self.customer_city + "\n" +
                self.customer_country)

    def tax_rate(self):
        if self.customer_country == "DE":
            return 0.19
        if self.customer_country == "AT":
            return 0.20
        if self.customer_country == "US":
            return 0.07
        return 0.0

    def total(self):
        subtotal = sum(i["price"] * i["qty"] for i in self.items)
        return subtotal * (1 + self.tax_rate())
```

---

## Example 5: Long parameter list

```python
def create_report(title, author, start_date, end_date, include_charts,
                  include_tables, include_summary, include_appendix,
                  format_type, output_path, header_color, footer_color,
                  page_size, language, timezone):
    header = f"# {title}\nby {author} ({language})\n"
    header += f"Period: {start_date} - {end_date} ({timezone})\n"
    body = ""
    if include_summary:
        body += "## Summary\n...\n"
    if include_charts:
        body += "## Charts\n...\n"
    if include_tables:
        body += "## Tables\n...\n"
    if include_appendix:
        body += "## Appendix\n...\n"
    footer = f"<footer style='color:{footer_color}'>{page_size}</footer>"
    doc = header + body + footer
    if format_type == "html":
        doc = f"<html style='color:{header_color}'>{doc}</html>"
    with open(output_path, "w") as f:
        f.write(doc)
```

---

## Example 6: If-elif chain begging for polymorphism

```python
def calculate_shipping(package, carrier):
    if carrier == "ups":
        base = 5.0
        if package["weight"] > 10:
            base += (package["weight"] - 10) * 0.5
        if package["express"]:
            base *= 1.8
        return base
    elif carrier == "fedex":
        base = 6.0
        if package["weight"] > 5:
            base += (package["weight"] - 5) * 0.6
        if package["express"]:
            base *= 2.0
        if package["international"]:
            base += 15
        return base
    elif carrier == "dhl":
        base = 7.0
        if package["weight"] > 2:
            base += (package["weight"] - 2) * 0.7
        if package["international"]:
            base += 20
        if package["express"]:
            base *= 1.9
        return base
    elif carrier == "usps":
        base = 4.0
        if package["weight"] > 1:
            base += (package["weight"] - 1) * 0.4
        return base
    else:
        raise ValueError("unknown carrier")
```

---

## Example 7: Primitive obsession

```python
def schedule_meeting(start_hour, start_minute, duration_minutes, participants_csv):
    if start_hour < 0 or start_hour > 23:
        raise ValueError("bad hour")
    if start_minute < 0 or start_minute > 59:
        raise ValueError("bad minute")
    end_total = start_hour * 60 + start_minute + duration_minutes
    end_hour = (end_total // 60) % 24
    end_minute = end_total % 60
    parts = [p.strip() for p in participants_csv.split(",") if p.strip()]
    for p in parts:
        if "@" not in p:
            raise ValueError("bad email: " + p)
    return {
        "start": f"{start_hour:02d}:{start_minute:02d}",
        "end": f"{end_hour:02d}:{end_minute:02d}",
        "participants": parts,
    }

def overlaps(meeting_a_start_hour, meeting_a_start_min, meeting_a_duration,
             meeting_b_start_hour, meeting_b_start_min, meeting_b_duration):
    a_start = meeting_a_start_hour * 60 + meeting_a_start_min
    a_end = a_start + meeting_a_duration
    b_start = meeting_b_start_hour * 60 + meeting_b_start_min
    b_end = b_start + meeting_b_duration
    return a_start < b_end and b_start < a_end
```

---

## Example 8: Magic numbers and strings

```python
def classify_bmi(weight_kg, height_m):
    bmi = weight_kg / (height_m * height_m)
    if bmi < 18.5:
        return "U"
    elif bmi < 25:
        return "N"
    elif bmi < 30:
        return "O"
    else:
        return "OB"

def recommend(status, age):
    if status == "U":
        if age < 18:
            return "see pediatrician"
        return "gain weight"
    elif status == "N":
        return "maintain"
    elif status == "O":
        if age > 60:
            return "light exercise"
        return "exercise more"
    elif status == "OB":
        return "consult doctor"
```

---

## Example 9: State flags instead of state machine

```python
class Document:
    def __init__(self, text):
        self.text = text
        self.is_draft = True
        self.is_reviewed = False
        self.is_approved = False
        self.is_published = False
        self.is_archived = False

    def submit_for_review(self):
        if not self.is_draft:
            raise RuntimeError("cannot submit")
        self.is_draft = False
        self.is_reviewed = False

    def review(self, approved):
        if self.is_draft or self.is_approved or self.is_published or self.is_archived:
            raise RuntimeError("cannot review")
        self.is_reviewed = True
        if approved:
            self.is_approved = True

    def publish(self):
        if not self.is_approved or self.is_published or self.is_archived:
            raise RuntimeError("cannot publish")
        self.is_published = True

    def archive(self):
        if self.is_archived:
            raise RuntimeError("already archived")
        self.is_archived = True

    def status(self):
        if self.is_archived:
            return "archived"
        if self.is_published:
            return "published"
        if self.is_approved:
            return "approved"
        if self.is_reviewed:
            return "reviewed"
        if self.is_draft:
            return "draft"
        return "submitted"
```

---

## Example 10: Global state and side effects

```python
CACHE = {}
LOG = []
CONFIG = {"retries": 3, "timeout": 5}

def fetch(url):
    if url in CACHE:
        LOG.append("hit " + url)
        return CACHE[url]
    LOG.append("miss " + url)
    attempts = 0
    while attempts < CONFIG["retries"]:
        try:
            # pretend this is a real HTTP call
            data = "DATA:" + url
            CACHE[url] = data
            LOG.append("ok " + url)
            return data
        except Exception:
            attempts += 1
            LOG.append("retry " + url)
    LOG.append("fail " + url)
    return None

def clear_cache():
    global CACHE
    CACHE = {}
    LOG.append("cache cleared")

def set_retries(n):
    CONFIG["retries"] = n
    LOG.append("retries=" + str(n))
```

---

## Example 11: Legacy batch report generator (god function)

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

---

## Example 12: Mini expression interpreter (deep nesting, string dispatch)

```python
def tokenize(src):
    tokens = []
    i = 0
    while i < len(src):
        c = src[i]
        if c == " " or c == "\t" or c == "\n":
            i += 1
            continue
        if c in "+-*/()<>=,;":
            if c == "=" and i + 1 < len(src) and src[i+1] == "=":
                tokens.append(("op", "=="))
                i += 2
                continue
            if c == "<" and i + 1 < len(src) and src[i+1] == "=":
                tokens.append(("op", "<="))
                i += 2
                continue
            if c == ">" and i + 1 < len(src) and src[i+1] == "=":
                tokens.append(("op", ">="))
                i += 2
                continue
            tokens.append(("op", c))
            i += 1
            continue
        if c.isdigit():
            j = i
            while j < len(src) and (src[j].isdigit() or src[j] == "."):
                j += 1
            num = src[i:j]
            tokens.append(("num", float(num) if "." in num else int(num)))
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            word = src[i:j]
            if word in ("if", "then", "else", "let", "in", "and", "or", "not", "true", "false"):
                tokens.append(("kw", word))
            else:
                tokens.append(("id", word))
            i = j
            continue
        if c == '"':
            j = i + 1
            while j < len(src) and src[j] != '"':
                j += 1
            tokens.append(("str", src[i+1:j]))
            i = j + 1
            continue
        raise SyntaxError("bad char " + c)
    tokens.append(("eof", None))
    return tokens

def evaluate(src, env=None):
    if env is None:
        env = {}
    tokens = tokenize(src)
    pos = [0]
    def peek():
        return tokens[pos[0]]
    def eat():
        t = tokens[pos[0]]
        pos[0] += 1
        return t
    def parse_expr():
        if peek()[0] == "kw" and peek()[1] == "if":
            eat()
            cond = parse_expr()
            if not (peek()[0] == "kw" and peek()[1] == "then"):
                raise SyntaxError("expected then")
            eat()
            a = parse_expr()
            if not (peek()[0] == "kw" and peek()[1] == "else"):
                raise SyntaxError("expected else")
            eat()
            b = parse_expr()
            return cond if False else (a if _truthy(cond) else b)
        if peek()[0] == "kw" and peek()[1] == "let":
            eat()
            if peek()[0] != "id":
                raise SyntaxError("expected id")
            name = eat()[1]
            if not (peek()[0] == "op" and peek()[1] == "="):
                raise SyntaxError("expected =")
            eat()
            val = parse_expr()
            if not (peek()[0] == "kw" and peek()[1] == "in"):
                raise SyntaxError("expected in")
            eat()
            old = env.get(name)
            had = name in env
            env[name] = val
            try:
                return parse_expr()
            finally:
                if had:
                    env[name] = old
                else:
                    del env[name]
        return parse_or()
    def parse_or():
        left = parse_and()
        while peek()[0] == "kw" and peek()[1] == "or":
            eat()
            right = parse_and()
            left = 1 if (_truthy(left) or _truthy(right)) else 0
        return left
    def parse_and():
        left = parse_cmp()
        while peek()[0] == "kw" and peek()[1] == "and":
            eat()
            right = parse_cmp()
            left = 1 if (_truthy(left) and _truthy(right)) else 0
        return left
    def parse_cmp():
        left = parse_add()
        if peek()[0] == "op" and peek()[1] in ("==", "<", ">", "<=", ">="):
            op = eat()[1]
            right = parse_add()
            if op == "==": return 1 if left == right else 0
            if op == "<":  return 1 if left < right else 0
            if op == ">":  return 1 if left > right else 0
            if op == "<=": return 1 if left <= right else 0
            if op == ">=": return 1 if left >= right else 0
        return left
    def parse_add():
        left = parse_mul()
        while peek()[0] == "op" and peek()[1] in ("+", "-"):
            op = eat()[1]
            right = parse_mul()
            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    left = str(left) + str(right)
                else:
                    left = left + right
            else:
                left = left - right
        return left
    def parse_mul():
        left = parse_unary()
        while peek()[0] == "op" and peek()[1] in ("*", "/"):
            op = eat()[1]
            right = parse_unary()
            if op == "*":
                left = left * right
            else:
                left = left / right
        return left
    def parse_unary():
        if peek()[0] == "op" and peek()[1] == "-":
            eat()
            return -parse_unary()
        if peek()[0] == "kw" and peek()[1] == "not":
            eat()
            v = parse_unary()
            return 0 if _truthy(v) else 1
        return parse_atom()
    def parse_atom():
        t = eat()
        if t[0] == "num": return t[1]
        if t[0] == "str": return t[1]
        if t[0] == "kw" and t[1] == "true": return 1
        if t[0] == "kw" and t[1] == "false": return 0
        if t[0] == "id":
            if peek()[0] == "op" and peek()[1] == "(":
                eat()
                args = []
                if not (peek()[0] == "op" and peek()[1] == ")"):
                    args.append(parse_expr())
                    while peek()[0] == "op" and peek()[1] == ",":
                        eat()
                        args.append(parse_expr())
                if not (peek()[0] == "op" and peek()[1] == ")"):
                    raise SyntaxError("expected )")
                eat()
                if t[1] == "min": return min(args)
                if t[1] == "max": return max(args)
                if t[1] == "abs": return abs(args[0])
                if t[1] == "len": return len(args[0])
                raise NameError("unknown fn " + t[1])
            if t[1] not in env:
                raise NameError("undefined " + t[1])
            return env[t[1]]
        if t[0] == "op" and t[1] == "(":
            v = parse_expr()
            if not (peek()[0] == "op" and peek()[1] == ")"):
                raise SyntaxError("expected )")
            eat()
            return v
        raise SyntaxError("unexpected " + str(t))
    def _truthy(v):
        if v == 0 or v == 0.0 or v == "" or v is None or v is False:
            return False
        return True
    return parse_expr()
```

---

## Example 13: Multi-tenant billing engine (tangled pricing rules)

```python
from datetime import datetime, timedelta

class BillingEngine:
    def __init__(self, tenants, plans, usage_log, coupons, fx_rates, tax_rules):
        self.tenants = tenants
        self.plans = plans
        self.usage_log = usage_log
        self.coupons = coupons
        self.fx_rates = fx_rates
        self.tax_rules = tax_rules
        self.invoices = []
        self.audit = []

    def run_for_period(self, year, month):
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        for tid, tenant in self.tenants.items():
            if tenant.get("status") == "cancelled":
                if tenant.get("cancelled_at") and tenant["cancelled_at"] < period_start:
                    self.audit.append("skip cancelled " + tid)
                    continue
            plan = self.plans.get(tenant["plan"])
            if not plan:
                self.audit.append("no plan " + tid)
                continue
            lines = []
            base = plan["base_price"]
            if tenant.get("status") == "trial":
                if tenant.get("trial_ends") and tenant["trial_ends"] >= period_end:
                    base = 0
                    lines.append({"desc": "trial", "amount": 0})
                else:
                    days_paid = (period_end - tenant["trial_ends"]).days
                    pro = base * (days_paid / 30.0)
                    base = round(pro, 2)
                    lines.append({"desc": "partial base (post-trial)", "amount": base})
            else:
                lines.append({"desc": plan["name"] + " base", "amount": base})
            usage_total = 0
            for event in self.usage_log:
                if event["tenant"] != tid:
                    continue
                if event["ts"] < period_start or event["ts"] > period_end:
                    continue
                kind = event["kind"]
                if kind == "api_call":
                    included = plan.get("included_api", 0)
                    over = max(0, event["count"] - included)
                    rate = plan.get("api_overage", 0.001)
                    cost = over * rate
                    usage_total += cost
                    if cost > 0:
                        lines.append({"desc": "api overage " + str(over), "amount": cost})
                elif kind == "storage_gb":
                    included = plan.get("included_storage", 0)
                    over = max(0, event["gb"] - included)
                    rate = plan.get("storage_overage", 0.1)
                    cost = over * rate
                    usage_total += cost
                    if cost > 0:
                        lines.append({"desc": "storage " + str(over) + "GB", "amount": cost})
                elif kind == "seats":
                    included = plan.get("included_seats", 1)
                    over = max(0, event["seats"] - included)
                    rate = plan.get("seat_price", 10)
                    cost = over * rate
                    usage_total += cost
                    if cost > 0:
                        lines.append({"desc": str(over) + " extra seats", "amount": cost})
                elif kind == "bandwidth_gb":
                    included = plan.get("included_bw", 100)
                    over = max(0, event["gb"] - included)
                    rate = plan.get("bw_overage", 0.02)
                    cost = over * rate
                    usage_total += cost
                    if cost > 0:
                        lines.append({"desc": "bandwidth " + str(over) + "GB", "amount": cost})
                else:
                    self.audit.append("unknown usage kind " + kind + " for " + tid)
            subtotal = base + usage_total
            if tenant.get("coupon"):
                c = self.coupons.get(tenant["coupon"])
                if c and c.get("valid_until", period_end) >= period_end:
                    if c["type"] == "pct":
                        d = subtotal * c["value"]
                        subtotal -= d
                        lines.append({"desc": "coupon " + tenant["coupon"], "amount": -d})
                    elif c["type"] == "flat":
                        d = min(c["value"], subtotal)
                        subtotal -= d
                        lines.append({"desc": "coupon " + tenant["coupon"], "amount": -d})
            if tenant.get("commitment_discount"):
                if tenant["commitment_months"] >= 12:
                    d = subtotal * 0.1
                    subtotal -= d
                    lines.append({"desc": "annual commitment", "amount": -d})
                elif tenant["commitment_months"] >= 6:
                    d = subtotal * 0.05
                    subtotal -= d
                    lines.append({"desc": "6mo commitment", "amount": -d})
            country = tenant.get("country", "US")
            tax_rate = 0
            for rule in self.tax_rules:
                if rule["country"] == country:
                    if rule.get("region") and rule["region"] != tenant.get("region"):
                        continue
                    if rule.get("b2b") and not tenant.get("vat_id"):
                        continue
                    if rule.get("b2b") is False and tenant.get("vat_id"):
                        continue
                    tax_rate = rule["rate"]
                    break
            tax = subtotal * tax_rate
            total = subtotal + tax
            currency = tenant.get("currency", "USD")
            if currency != "USD":
                rate = self.fx_rates.get(currency)
                if rate is None:
                    self.audit.append("no fx " + currency + " for " + tid)
                else:
                    for ln in lines:
                        ln["amount"] = round(ln["amount"] * rate, 2)
                    subtotal = round(subtotal * rate, 2)
                    tax = round(tax * rate, 2)
                    total = round(total * rate, 2)
            inv = {
                "tenant": tid, "period": period_start.strftime("%Y-%m"),
                "lines": lines, "subtotal": round(subtotal, 2),
                "tax": round(tax, 2), "total": round(total, 2),
                "currency": currency,
            }
            self.invoices.append(inv)
            self.audit.append("invoiced " + tid + " " + str(inv["total"]))
        return self.invoices
```

---

## Example 14: Monolithic HTTP request handler

```python
import json
import hashlib
import time

SESSIONS = {}
USERS = {"admin": {"pw": "adminhash", "role": "admin"}}
POSTS = {}
COMMENTS = {}
RATE_LIMIT = {}

def handle_request(method, path, headers, body, db):
    now = time.time()
    ip = headers.get("x-forwarded-for", "unknown")
    bucket = RATE_LIMIT.setdefault(ip, [])
    bucket[:] = [t for t in bucket if now - t < 60]
    if len(bucket) >= 100:
        return 429, {"content-type": "application/json"}, json.dumps({"error": "rate limit"})
    bucket.append(now)
    auth = None
    if "authorization" in headers:
        token = headers["authorization"].replace("Bearer ", "")
        sess = SESSIONS.get(token)
        if sess and sess["expires"] > now:
            auth = sess["user"]
    try:
        parsed = json.loads(body) if body else {}
    except Exception:
        return 400, {"content-type": "application/json"}, json.dumps({"error": "bad json"})
    parts = [p for p in path.split("/") if p]
    if method == "POST" and parts == ["auth", "login"]:
        u = parsed.get("username")
        p = parsed.get("password")
        if not u or not p:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "missing"})
        user = USERS.get(u)
        h = hashlib.sha256(p.encode()).hexdigest()
        if not user or user["pw"] != h:
            return 401, {"content-type": "application/json"}, json.dumps({"error": "bad creds"})
        token = hashlib.sha256((u + str(now)).encode()).hexdigest()
        SESSIONS[token] = {"user": u, "expires": now + 3600}
        return 200, {"content-type": "application/json"}, json.dumps({"token": token})
    if method == "POST" and parts == ["auth", "logout"]:
        if "authorization" in headers:
            tok = headers["authorization"].replace("Bearer ", "")
            SESSIONS.pop(tok, None)
        return 204, {}, ""
    if method == "POST" and parts == ["users"]:
        u = parsed.get("username")
        p = parsed.get("password")
        e = parsed.get("email")
        if not u or not p or not e:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "missing"})
        if len(p) < 8:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "pw short"})
        if "@" not in e:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "bad email"})
        if u in USERS:
            return 409, {"content-type": "application/json"}, json.dumps({"error": "exists"})
        USERS[u] = {"pw": hashlib.sha256(p.encode()).hexdigest(), "role": "user", "email": e}
        db.execute("INSERT INTO users(name,email) VALUES (?,?)", (u, e))
        return 201, {"content-type": "application/json"}, json.dumps({"username": u})
    if method == "GET" and len(parts) == 1 and parts[0] == "posts":
        limit = int(headers.get("x-limit", "20"))
        offset = int(headers.get("x-offset", "0"))
        items = list(POSTS.values())
        items.sort(key=lambda p: p["created"], reverse=True)
        page = items[offset:offset+limit]
        return 200, {"content-type": "application/json"}, json.dumps({"items": page, "total": len(items)})
    if method == "GET" and len(parts) == 2 and parts[0] == "posts":
        pid = parts[1]
        post = POSTS.get(pid)
        if not post:
            return 404, {"content-type": "application/json"}, json.dumps({"error": "not found"})
        cs = [c for c in COMMENTS.values() if c["post"] == pid]
        return 200, {"content-type": "application/json"}, json.dumps({"post": post, "comments": cs})
    if method == "POST" and parts == ["posts"]:
        if not auth:
            return 401, {"content-type": "application/json"}, json.dumps({"error": "auth"})
        title = parsed.get("title")
        content = parsed.get("content")
        if not title or len(title) > 200:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "bad title"})
        if not content or len(content) > 10000:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "bad content"})
        pid = hashlib.sha256((auth + title + str(now)).encode()).hexdigest()[:12]
        POSTS[pid] = {"id": pid, "title": title, "content": content, "author": auth, "created": now}
        db.execute("INSERT INTO posts(id,author,title) VALUES (?,?,?)", (pid, auth, title))
        return 201, {"content-type": "application/json"}, json.dumps(POSTS[pid])
    if method == "DELETE" and len(parts) == 2 and parts[0] == "posts":
        if not auth:
            return 401, {"content-type": "application/json"}, json.dumps({"error": "auth"})
        pid = parts[1]
        post = POSTS.get(pid)
        if not post:
            return 404, {"content-type": "application/json"}, json.dumps({"error": "not found"})
        if post["author"] != auth and USERS[auth]["role"] != "admin":
            return 403, {"content-type": "application/json"}, json.dumps({"error": "forbidden"})
        del POSTS[pid]
        for cid in list(COMMENTS.keys()):
            if COMMENTS[cid]["post"] == pid:
                del COMMENTS[cid]
        db.execute("DELETE FROM posts WHERE id=?", (pid,))
        return 204, {}, ""
    if method == "POST" and len(parts) == 3 and parts[0] == "posts" and parts[2] == "comments":
        if not auth:
            return 401, {"content-type": "application/json"}, json.dumps({"error": "auth"})
        pid = parts[1]
        if pid not in POSTS:
            return 404, {"content-type": "application/json"}, json.dumps({"error": "no post"})
        text = parsed.get("text", "").strip()
        if not text or len(text) > 1000:
            return 400, {"content-type": "application/json"}, json.dumps({"error": "bad text"})
        cid = hashlib.sha256((auth + text + str(now)).encode()).hexdigest()[:12]
        COMMENTS[cid] = {"id": cid, "post": pid, "author": auth, "text": text, "created": now}
        return 201, {"content-type": "application/json"}, json.dumps(COMMENTS[cid])
    if method == "GET" and parts == ["admin", "stats"]:
        if not auth or USERS[auth]["role"] != "admin":
            return 403, {"content-type": "application/json"}, json.dumps({"error": "forbidden"})
        return 200, {"content-type": "application/json"}, json.dumps({
            "users": len(USERS), "posts": len(POSTS),
            "comments": len(COMMENTS), "sessions": len(SESSIONS),
        })
    return 404, {"content-type": "application/json"}, json.dumps({"error": "no route"})
```

---

## Example 15: Turn-based combat simulator (tangled state machine)

```python
import random

class Combat:
    def __init__(self, players, enemies, terrain, seed=None):
        self.players = players
        self.enemies = enemies
        self.terrain = terrain
        self.turn = 0
        self.round = 1
        self.log = []
        self.effects = []
        self.loot = []
        self.phase = "setup"
        self.rng = random.Random(seed)
        self.initiative = []

    def start(self):
        if self.phase != "setup":
            raise RuntimeError("already started")
        for p in self.players:
            p["hp"] = p["max_hp"]
            p["mp"] = p.get("max_mp", 0)
            p["alive"] = True
            p["status"] = []
            p["init"] = self.rng.randint(1, 20) + p.get("dex", 0)
        for e in self.enemies:
            e["hp"] = e["max_hp"]
            e["alive"] = True
            e["status"] = []
            e["init"] = self.rng.randint(1, 20) + e.get("dex", 0)
        self.initiative = [("p", i) for i in range(len(self.players))] + \
                          [("e", i) for i in range(len(self.enemies))]
        def init_key(ref):
            side, idx = ref
            return -(self.players[idx]["init"] if side == "p" else self.enemies[idx]["init"])
        self.initiative.sort(key=init_key)
        self.phase = "active"
        self.log.append("combat start: " + str(len(self.players)) + "v" + str(len(self.enemies)))

    def current_actor(self):
        if self.phase != "active":
            return None
        return self.initiative[self.turn % len(self.initiative)]

    def take_turn(self, action):
        if self.phase != "active":
            raise RuntimeError("not active")
        side, idx = self.current_actor()
        actor = self.players[idx] if side == "p" else self.enemies[idx]
        if not actor["alive"]:
            self.turn += 1
            self._maybe_end_round()
            return
        for eff in list(actor["status"]):
            if eff["kind"] == "poison":
                actor["hp"] -= eff["power"]
                self.log.append(actor["name"] + " takes " + str(eff["power"]) + " poison")
                eff["duration"] -= 1
                if eff["duration"] <= 0:
                    actor["status"].remove(eff)
                if actor["hp"] <= 0:
                    actor["alive"] = False
                    self.log.append(actor["name"] + " dies of poison")
                    self.turn += 1
                    self._check_end()
                    return
            elif eff["kind"] == "stun":
                eff["duration"] -= 1
                if eff["duration"] <= 0:
                    actor["status"].remove(eff)
                self.log.append(actor["name"] + " is stunned")
                self.turn += 1
                self._maybe_end_round()
                return
            elif eff["kind"] == "regen":
                heal = min(eff["power"], actor["max_hp"] - actor["hp"])
                actor["hp"] += heal
                self.log.append(actor["name"] + " regens " + str(heal))
                eff["duration"] -= 1
                if eff["duration"] <= 0:
                    actor["status"].remove(eff)
        kind = action.get("kind")
        if kind == "attack":
            target_side = "e" if side == "p" else "p"
            target_list = self.enemies if target_side == "e" else self.players
            tidx = action.get("target", 0)
            if tidx < 0 or tidx >= len(target_list) or not target_list[tidx]["alive"]:
                self.log.append(actor["name"] + " attacks invalid target")
            else:
                target = target_list[tidx]
                hit_roll = self.rng.randint(1, 20) + actor.get("atk", 0)
                ac = target.get("ac", 10)
                if self.terrain.get("cover") and target_side == "p":
                    ac += 2
                if self.terrain.get("high_ground") == side:
                    hit_roll += 2
                if hit_roll >= ac:
                    dmg = self.rng.randint(1, actor.get("dmg_die", 6)) + actor.get("dmg_bonus", 0)
                    if hit_roll - actor.get("atk", 0) == 20:
                        dmg *= 2
                        self.log.append("CRIT!")
                    resist = target.get("resist", {})
                    dtype = actor.get("dmg_type", "physical")
                    if dtype in resist:
                        dmg = int(dmg * (1 - resist[dtype]))
                    target["hp"] -= dmg
                    self.log.append(actor["name"] + " hits " + target["name"] + " for " + str(dmg))
                    if target["hp"] <= 0:
                        target["alive"] = False
                        self.log.append(target["name"] + " falls")
                        if target_side == "e":
                            self.loot.extend(target.get("drops", []))
                else:
                    self.log.append(actor["name"] + " misses " + target["name"])
        elif kind == "cast":
            spell = action.get("spell")
            cost = action.get("cost", 0)
            if actor.get("mp", 0) < cost:
                self.log.append(actor["name"] + " fizzles (no mp)")
            else:
                actor["mp"] -= cost
                if spell == "fireball":
                    for t in (self.enemies if side == "p" else self.players):
                        if t["alive"]:
                            dmg = self.rng.randint(10, 20)
                            if "fire" in t.get("resist", {}):
                                dmg = int(dmg * (1 - t["resist"]["fire"]))
                            t["hp"] -= dmg
                            self.log.append("fireball hits " + t["name"] + " for " + str(dmg))
                            if t["hp"] <= 0:
                                t["alive"] = False
                                if side == "p":
                                    self.loot.extend(t.get("drops", []))
                elif spell == "heal":
                    allies = self.players if side == "p" else self.enemies
                    tidx = action.get("target", idx)
                    tgt = allies[tidx]
                    heal = self.rng.randint(8, 16)
                    tgt["hp"] = min(tgt["max_hp"], tgt["hp"] + heal)
                    self.log.append(actor["name"] + " heals " + tgt["name"] + " for " + str(heal))
                elif spell == "poison_cloud":
                    for t in (self.enemies if side == "p" else self.players):
                        if t["alive"]:
                            t["status"].append({"kind": "poison", "power": 3, "duration": 3})
                            self.log.append(t["name"] + " is poisoned")
                else:
                    self.log.append("unknown spell " + str(spell))
        elif kind == "item":
            item = action.get("item")
            if item not in actor.get("inventory", {}):
                self.log.append(actor["name"] + " has no " + str(item))
            else:
                actor["inventory"][item] -= 1
                if actor["inventory"][item] <= 0:
                    del actor["inventory"][item]
                if item == "potion":
                    heal = 15
                    actor["hp"] = min(actor["max_hp"], actor["hp"] + heal)
                    self.log.append(actor["name"] + " drinks potion (+" + str(heal) + ")")
                elif item == "antidote":
                    actor["status"] = [s for s in actor["status"] if s["kind"] != "poison"]
                    self.log.append(actor["name"] + " uses antidote")
                elif item == "smoke_bomb":
                    self.terrain["cover"] = True
                    self.log.append("smoke fills the area")
                else:
                    self.log.append("unknown item " + str(item))
        elif kind == "flee":
            if side == "p":
                roll = self.rng.randint(1, 20)
                if roll >= 12:
                    self.phase = "fled"
                    self.log.append(actor["name"] + " flees successfully")
                    return
                else:
                    self.log.append(actor["name"] + " fails to flee")
            else:
                self.log.append("enemies don't flee")
        else:
            self.log.append("unknown action " + str(kind))
        self.turn += 1
        self._check_end()
        self._maybe_end_round()

    def _maybe_end_round(self):
        if self.turn > 0 and self.turn % len(self.initiative) == 0:
            self.round += 1
            self.log.append("round " + str(self.round))

    def _check_end(self):
        if not any(p["alive"] for p in self.players):
            self.phase = "defeat"
            self.log.append("party defeated")
        elif not any(e["alive"] for e in self.enemies):
            self.phase = "victory"
            self.log.append("victory! loot: " + str(self.loot))
```
