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
