```python
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional


class UsageKind(Enum):
    API_CALL = "api_call"
    STORAGE_GB = "storage_gb"
    SEATS = "seats"
    BANDWIDTH_GB = "bandwidth_gb"


class BillingEngine:
    def __init__(self, tenants: Dict, plans: Dict, usage_log: List, coupons: Dict, 
                 fx_rates: Dict, tax_rules: List):
        self.tenants = tenants
        self.plans = plans
        self.usage_log = usage_log
        self.coupons = coupons
        self.fx_rates = fx_rates
        self.tax_rules = tax_rules
        self.invoices: List[Dict[str, Any]] = []
        self.audit: List[str] = []

    def run_for_period(self, year: int, month: int) -> List[Dict[str, Any]]:
        period_start = datetime(year, month, 1)
        period_end = self._get_period_end(year, month)
        
        for tid, tenant in self.tenants.items():
            if not self._should_process_tenant(tid, tenant, period_start):
                continue
                
            plan = self.plans.get(tenant["plan"])
            if not plan:
                self.audit.append(f"no plan {tid}")
                continue
            
            invoice = self._build_invoice(tid, tenant, plan, period_start, period_end)
            self.invoices.append(invoice)
            
        return self.invoices

    def _get_period_end(self, year: int, month: int) -> datetime:
        """Get the last moment of the given month."""
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        return next_month - timedelta(seconds=1)

    def _should_process_tenant(self, tid: str, tenant: Dict, period_start: datetime) -> bool:
        """Check if tenant should be processed for this period."""
        if tenant.get("status") == "cancelled":
            if tenant.get("cancelled_at") and tenant["cancelled_at"] < period_start:
                self.audit.append(f"skip cancelled {tid}")
                return False
        return True

    def _build_invoice(self, tid: str, tenant: Dict, plan: Dict, 
                       period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Build a complete invoice for a tenant."""
        lines: List[Dict[str, Any]] = []
        
        # Base price calculation
        base = self._calculate_base_price(tenant, plan, period_start, period_end, lines)
        
        # Usage charges
        usage_total = self._calculate_usage_charges(tid, plan, period_start, period_end, lines)
        
        subtotal = base + usage_total
        
        # Apply discounts
        self._apply_coupons(tenant, subtotal, lines)
        subtotal = sum(line["amount"] for line in lines)
        
        self._apply_commitment_discount(tenant, subtotal, lines)
        subtotal = sum(line["amount"] for line in lines)
        
        # Tax calculation
        tax_rate = self._get_tax_rate(tenant)
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        # Currency conversion
        currency = tenant.get("currency", "USD")
        if currency != "USD":
            self._apply_currency_conversion(currency, tid, lines, subtotal, tax, total)
            
        currency_total = round(total * self.fx_rates.get(currency, 1), 2) if currency != "USD" else round(total, 2)
        
        return {
            "tenant": tid,
            "period": period_start.strftime("%Y-%m"),
            "lines": lines,
            "subtotal": round(subtotal * self.fx_rates.get(currency, 1), 2) if currency != "USD" else round(subtotal, 2),
            "tax": round(tax * self.fx_rates.get(currency, 1), 2) if currency != "USD" else round(tax, 2),
            "total": currency_total,
            "currency": currency,
        }

    def _calculate_base_price(self, tenant: Dict, plan: Dict, period_start: datetime, 
                              period_end: datetime, lines: List) -> float:
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

    def _calculate_usage_charges(self, tid: str, plan: Dict, period_start: datetime, 
                                 period_end: datetime, lines: List) -> float:
        """Calculate usage-based charges."""
        usage_handlers = {
            UsageKind.API_CALL.value: self._handle_api_call,
            UsageKind.STORAGE_GB.value: self._handle_storage,
            UsageKind.SEATS.value: self._handle_seats,
            UsageKind.BANDWIDTH_GB.value: self._handle_bandwidth,
        }
        
        usage_total = 0
        for event in self.usage_log:
            if event["tenant"] != tid or event["ts"] < period_start or event["ts"] > period_end:
                continue
                
            kind = event["kind"]
            handler = usage_handlers.get(kind)
            
            if handler:
                cost = handler(plan, event, lines)
                usage_total += cost
            else:
                self.audit.append(f"unknown usage kind {kind} for {tid}")
                
        return usage_total

    def _handle_api_call(self, plan: Dict, event: Dict, lines: List) -> float:
        """Handle API call overage."""
        included = plan.get("included_api", 0)
        over = max(0, event["count"] - included)
        rate = plan.get("api_overage", 0.001)
        cost = over * rate
        if cost > 0:
            lines.append({"desc": f"api overage {over}", "amount": cost})
        return cost

    def _handle_storage(self, plan: Dict, event: Dict, lines: List) -> float:
        """Handle storage overage."""
        included = plan.get("included_storage", 0)
        over = max(0, event["gb"] - included)
        rate = plan.get("storage_overage", 0.1)
        cost = over * rate
        if cost > 0:
            lines.append({"desc": f"storage {over}GB", "amount": cost})
        return cost

    def _handle_seats(self, plan: Dict, event: Dict, lines: List) -> float:
        """Handle extra seats."""
        included = plan.get("included_seats", 1)
        over = max(0, event["seats"] - included)
        rate = plan.get("seat_price", 10)
        cost = over * rate
        if cost > 0:
            lines.append({"desc": f"{over} extra seats", "amount": cost})
        return cost

    def _handle_bandwidth(self, plan: Dict, event: Dict, lines: List) -> float:
        """Handle bandwidth overage."""
        included = plan.get("included_bw", 100)
        over = max(0, event["gb"] - included)
        rate = plan.get("bw_overage", 0.02)
        cost = over * rate
        if cost > 0:
            lines.append({"desc": f"bandwidth {over}GB", "amount": cost})
        return cost

    def _apply_coupons(self, tenant: Dict, subtotal: float, lines: List) -> None:
        """Apply coupon discount if applicable."""
        if not tenant.get("coupon"):
            return
            
        coupon = self.coupons.get(tenant["coupon"])
        if not coupon:
            return
            
        if coupon_value := self._calculate_coupon_discount(coupon, subtotal):
            lines.append({"desc": f"coupon {tenant['coupon']}", "amount": -coupon_value})

    def _calculate_coupon_discount(self, coupon: Dict, subtotal: float) -> Optional[float]:
        """Calculate coupon discount amount."""
        if coupon.get("type") == "pct":
            return subtotal * coupon["value"]
        elif coupon.get("type") == "flat":
            return min(coupon["value"], subtotal)
        return None

    def _apply_commitment_discount(self, tenant: Dict, subtotal: float, lines: List) -> None:
        """Apply commitment-based discount."""
        if not tenant.get("commitment_discount"):
            return
            
        months = tenant.get("commitment_months", 0)
        if months >= 12:
            discount = subtotal * 0.1
            lines.append({"desc": "annual commitment", "amount": -discount})
        elif months >= 6:
            discount = subtotal * 0.05
            lines.append({"desc": "6mo commitment", "amount": -discount})

    def _get_tax_rate(self, tenant: Dict) -> float:
        """Get applicable tax rate for tenant."""
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

    def _apply_currency_conversion(self, currency: str, tid: str, lines: List, 
                                   subtotal: float, tax: float, total: float) -> None:
        """Apply FX rate conversion to amounts."""
        rate = self.fx_rates.get(currency)
        if rate is None:
            self.audit.append(f"no fx {currency} for {tid}")
        else:
            for line in lines:
                line["amount"] = round(line["amount"] * rate, 2)
```

Notes: Refactored to extract methods, reduce nesting, improve readability, and add type hints. The core logic remains the same but is now more modular and maintainable.
