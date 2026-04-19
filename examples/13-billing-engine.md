# Example 13: Multi-tenant billing engine (tangled pricing rules)

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
