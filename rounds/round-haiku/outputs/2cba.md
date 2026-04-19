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
        period_end = self._get_period_end(year, month)
        
        for tid, tenant in self.tenants.items():
            invoice = self._process_tenant(tid, tenant, period_start, period_end)
            if invoice:
                self.invoices.append(invoice)
        
        return self.invoices

    def _get_period_end(self, year, month):
        """Calculate the last moment of the given month."""
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        return datetime(next_year, next_month, 1) - timedelta(seconds=1)

    def _process_tenant(self, tid, tenant, period_start, period_end):
        """Process billing for a single tenant."""
        # Check if tenant is cancelled before period
        if tenant.get("status") == "cancelled":
            if tenant.get("cancelled_at") and tenant["cancelled_at"] < period_start:
                self.audit.append(f"skip cancelled {tid}")
                return None
        
        # Validate plan exists
        plan = self.plans.get(tenant["plan"])
        if not plan:
            self.audit.append(f"no plan {tid}")
            return None
        
        lines = []
        base = self._calculate_base_price(plan, tenant, period_start, period_end, lines)
        usage_total = self._calculate_usage(tid, plan, period_start, period_end, lines)
        
        subtotal = base + usage_total
        subtotal = self._apply_coupon(tenant, subtotal, lines)
        subtotal = self._apply_commitment_discount(tenant, subtotal, lines)
        
        tax_rate = self._get_tax_rate(tenant)
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        currency = tenant.get("currency", "USD")
        if currency != "USD":
            lines, subtotal, tax, total = self._convert_currency(currency, tid, lines, subtotal, tax, total)
        
        invoice = {
            "tenant": tid,
            "period": period_start.strftime("%Y-%m"),
            "lines": lines,
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "currency": currency,
        }
        self.audit.append(f"invoiced {tid} {invoice['total']}")
        return invoice

    def _calculate_base_price(self, plan, tenant, period_start, period_end, lines):
        """Calculate base price, handling trial periods."""
        base = plan["base_price"]
        
        if tenant.get("status") == "trial":
            if tenant.get("trial_ends") and tenant["trial_ends"] >= period_end:
                base = 0
                lines.append({"desc": "trial", "amount": 0})
            else:
                days_paid = (period_end - tenant["trial_ends"]).days
                base = round(base * (days_paid / 30.0), 2)
                lines.append({"desc": "partial base (post-trial)", "amount": base})
        else:
            lines.append({"desc": f"{plan['name']} base", "amount": base})
        
        return base

    def _calculate_usage(self, tid, plan, period_start, period_end, lines):
        """Calculate usage-based charges."""
        usage_total = 0
        usage_handlers = {
            "api_call": self._handle_api_call,
            "storage_gb": self._handle_storage,
            "seats": self._handle_seats,
            "bandwidth_gb": self._handle_bandwidth,
        }
        
        for event in self.usage_log:
            if event["tenant"] != tid:
                continue
            if event["ts"] < period_start or event["ts"] > period_end:
                continue
            
            kind = event["kind"]
            handler = usage_handlers.get(kind)
            if handler:
                cost = handler(plan, event, lines)
                usage_total += cost
            else:
                self.audit.append(f"unknown usage kind {kind} for {tid}")
        
        return usage_total

    def _handle_api_call(self, plan, event, lines):
        """Handle API call overage charges."""
        included = plan.get("included_api", 0)
        over = max(0, event["count"] - included)
        rate = plan.get("api_overage", 0.001)
        cost = over * rate
        if cost > 0:
            lines.append({"desc": f"api overage {over}", "amount": cost})
        return cost

    def _handle_storage(self, plan, event, lines):
        """Handle storage overage charges."""
        included = plan.get("included_storage", 0)
        over = max(0, event["gb"] - included)
        rate = plan.get("storage_overage", 0.1)
        cost = over * rate
        if cost > 0:
            lines.append({"desc": f"storage {over}GB", "amount": cost})
        return cost

    def _handle_seats(self, plan, event, lines):
        """Handle extra seat charges."""
        included = plan.get("included_seats", 1)
        over = max(0, event["seats"] - included)
        rate = plan.get("seat_price", 10)
        cost = over * rate
        if cost > 0:
            lines.append({"desc": f"{over} extra seats", "amount": cost})
        return cost

    def _handle_bandwidth(self, plan, event, lines):
        """Handle bandwidth overage charges."""
        included = plan.get("included_bw", 100)
        over = max(0, event["gb"] - included)
        rate = plan.get("bw_overage", 0.02)
        cost = over * rate
        if cost > 0:
            lines.append({"desc": f"bandwidth {over}GB", "amount": cost})
        return cost

    def _apply_coupon(self, tenant, subtotal, lines):
        """Apply coupon discount if valid."""
        if not tenant.get("coupon"):
            return subtotal
        
        coupon = self.coupons.get(tenant["coupon"])
        if not coupon or coupon.get("valid_until", subtotal) < subtotal:
            return subtotal
        
        if coupon["type"] == "pct":
            discount = subtotal * coupon["value"]
        elif coupon["type"] == "flat":
            discount = min(coupon["value"], subtotal)
        else:
            return subtotal
        
        subtotal -= discount
        lines.append({"desc": f"coupon {tenant['coupon']}", "amount": -discount})
        return subtotal

    def _apply_commitment_discount(self, tenant, subtotal, lines):
        """Apply commitment discount if applicable."""
        if not tenant.get("commitment_discount"):
            return subtotal
        
        months = tenant.get("commitment_months", 0)
        if months >= 12:
            discount = subtotal * 0.1
            desc = "annual commitment"
        elif months >= 6:
            discount = subtotal * 0.05
            desc = "6mo commitment"
        else:
            return subtotal
        
        subtotal -= discount
        lines.append({"desc": desc, "amount": -discount})
        return subtotal

    def _get_tax_rate(self, tenant):
        """Determine applicable tax rate for tenant."""
        country = tenant.get("country", "US")
        
        for rule in self.tax_rules:
            if rule["country"] != country:
                continue
            if rule.get("region") and rule["region"] != tenant.get("region"):
                continue
            if rule.get("b2b") and not tenant.get("vat_id"):
                continue
            if rule.get("b2b") is False and tenant.get("vat_id"):
                continue
            return rule["rate"]
        
        return 0

    def _convert_currency(self, currency, tid, lines, subtotal, tax, total):
        """Convert amounts to target currency."""
        rate = self.fx_rates.get(currency)
        if rate is None:
            self.audit.append(f"no fx {currency} for {tid}")
            return lines, subtotal, tax, total
        
        lines = [{"desc": ln["desc"], "amount": round(ln["amount"] * rate, 2)} for ln in lines]
        subtotal = round(subtotal * rate, 2)
        tax = round(tax * rate, 2)
        total = round(total * rate, 2)
        
        return lines, subtotal, tax, total
```

Refactoring improvements:
- Extracted long method into smaller focused methods for maintainability
- Replaced manual period_end calculation with dedicated helper method
- Separated usage event handling into specialized methods per event type
- Extracted coupon, tax, currency, and commitment logic into reusable methods
- Used f-strings instead of string concatenation
- Improved control flow with early returns and reduced nesting
- Added docstrings to clarify method purposes
- Made main loop cleaner by delegating to `_process_tenant`
