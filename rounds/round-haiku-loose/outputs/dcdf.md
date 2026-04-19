```python
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


class EventKind(Enum):
    API_CALL = "api_call"
    STORAGE_GB = "storage_gb"
    SEATS = "seats"
    BANDWIDTH_GB = "bandwidth_gb"


@dataclass
class UsageEventConfig:
    """Configuration for processing a specific usage event type."""
    plan_key: str
    overage_key: str
    default_included: int | float
    default_rate: float
    description_template: str

    def get_cost(self, event: Dict, plan: Dict) -> tuple[float, str]:
        """Calculate cost and description for this event type."""
        included = plan.get(self.plan_key, self.default_included)
        
        # Extract the quantity based on event kind
        if self.plan_key == "included_api":
            quantity = event["count"]
        elif self.plan_key == "included_bw":
            quantity = event["gb"]
        else:
            quantity = event.get(self.plan_key.replace("included_", ""), event.get("gb", event.get("seats", 0)))
        
        over = max(0, quantity - included)
        rate = plan.get(self.overage_key, self.default_rate)
        cost = over * rate
        
        desc = self.description_template.format(amount=over)
        return cost, desc


class BillingEngine:
    # Event configuration mapping
    EVENT_CONFIG = {
        EventKind.API_CALL: UsageEventConfig(
            plan_key="included_api",
            overage_key="api_overage",
            default_included=0,
            default_rate=0.001,
            description_template="api overage {amount}"
        ),
        EventKind.STORAGE_GB: UsageEventConfig(
            plan_key="included_storage",
            overage_key="storage_overage",
            default_included=0,
            default_rate=0.1,
            description_template="storage {amount}GB"
        ),
        EventKind.SEATS: UsageEventConfig(
            plan_key="included_seats",
            overage_key="seat_price",
            default_included=1,
            default_rate=10,
            description_template="{amount} extra seats"
        ),
        EventKind.BANDWIDTH_GB: UsageEventConfig(
            plan_key="included_bw",
            overage_key="bw_overage",
            default_included=100,
            default_rate=0.02,
            description_template="bandwidth {amount}GB"
        ),
    }

    def __init__(self, tenants: Dict, plans: Dict, usage_log: List,
                 coupons: Dict, fx_rates: Dict, tax_rules: List):
        self.tenants = tenants
        self.plans = plans
        self.usage_log = usage_log
        self.coupons = coupons
        self.fx_rates = fx_rates
        self.tax_rules = tax_rules
        self.invoices: List[Dict] = []
        self.audit: List[str] = []

    def run_for_period(self, year: int, month: int) -> List[Dict]:
        """Generate invoices for the specified period."""
        period_start, period_end = self._get_period_bounds(year, month)
        
        for tenant_id, tenant in self.tenants.items():
            if self._should_skip_tenant(tenant, tenant_id, period_start):
                continue
            
            plan = self.plans.get(tenant["plan"])
            if not plan:
                self.audit.append(f"no plan {tenant_id}")
                continue
            
            invoice = self._build_invoice(tenant_id, tenant, plan, period_start, period_end)
            self.invoices.append(invoice)
            self.audit.append(f"invoiced {tenant_id} {invoice['total']}")
        
        return self.invoices

    def _get_period_bounds(self, year: int, month: int) -> tuple[datetime, datetime]:
        """Calculate period start and end dates."""
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        return period_start, period_end

    def _should_skip_tenant(self, tenant: Dict, tenant_id: str, period_start: datetime) -> bool:
        """Check if tenant should be skipped from billing."""
        if tenant.get("status") == "cancelled":
            cancelled_at = tenant.get("cancelled_at")
            if cancelled_at and cancelled_at < period_start:
                self.audit.append(f"skip cancelled {tenant_id}")
                return True
        return False

    def _build_invoice(self, tenant_id: str, tenant: Dict, plan: Dict,
                       period_start: datetime, period_end: datetime) -> Dict:
        """Build a complete invoice for a tenant."""
        lines: List[Dict] = []
        
        # Base pricing
        base = self._calculate_base_price(tenant, plan, period_start, period_end, lines)
        
        # Usage charges
        usage_total = self._process_usage_events(tenant_id, plan, period_start, period_end, lines)
        
        # Subtotal and discounts
        subtotal = base + usage_total
        subtotal = self._apply_coupon(tenant, subtotal, lines)
        subtotal = self._apply_commitment_discount(tenant, subtotal, lines)
        
        # Tax and currency conversion
        tax = self._calculate_tax(tenant, subtotal)
        total = subtotal + tax
        
        currency = tenant.get("currency", "USD")
        if currency != "USD":
            total, subtotal, tax, lines = self._convert_currency(
                currency, total, subtotal, tax, lines, tenant_id
            )
        
        return {
            "tenant": tenant_id,
            "period": period_start.strftime("%Y-%m"),
            "lines": lines,
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "currency": currency,
        }

    def _calculate_base_price(self, tenant: Dict, plan: Dict, period_start: datetime,
                              period_end: datetime, lines: List[Dict]) -> float:
        """Calculate base price for the period."""
        base = plan["base_price"]
        
        if tenant.get("status") == "trial":
            trial_ends = tenant.get("trial_ends")
            if trial_ends and trial_ends >= period_end:
                lines.append({"desc": "trial", "amount": 0})
                return 0
            else:
                days_paid = (period_end - trial_ends).days
                pro = base * (days_paid / 30.0)
                base = round(pro, 2)
                lines.append({"desc": "partial base (post-trial)", "amount": base})
                return base
        
        lines.append({"desc": f"{plan['name']} base", "amount": base})
        return base

    def _process_usage_events(self, tenant_id: str, plan: Dict,
                             period_start: datetime, period_end: datetime,
                             lines: List[Dict]) -> float:
        """Process all usage events for the tenant in the period."""
        usage_total = 0
        
        for event in self.usage_log:
            if event["tenant"] != tenant_id:
                continue
            if not (period_start <= event["ts"] <= period_end):
                continue
            
            kind_str = event["kind"]
            try:
                kind = EventKind(kind_str)
                config = self.EVENT_CONFIG[kind]
                cost, desc = config.get_cost(event, plan)
                
                if cost > 0:
                    usage_total += cost
                    lines.append({"desc": desc, "amount": cost})
            except (ValueError, KeyError):
                self.audit.append(f"unknown usage kind {kind_str} for {tenant_id}")
        
        return usage_total

    def _apply_coupon(self, tenant: Dict, subtotal: float, lines: List[Dict]) -> float:
        """Apply coupon discount if applicable."""
        coupon_code = tenant.get("coupon")
        if not coupon_code:
            return subtotal
        
        coupon = self.coupons.get(coupon_code)
        if not coupon or coupon.get("valid_until", subtotal) < subtotal:
            return subtotal
        
        discount = 0
        if coupon["type"] == "pct":
            discount = subtotal * coupon["value"]
        elif coupon["type"] == "flat":
            discount = min(coupon["value"], subtotal)
        
        if discount > 0:
            subtotal -= discount
            lines.append({"desc": f"coupon {coupon_code}", "amount": -discount})
        
        return subtotal

    def _apply_commitment_discount(self, tenant: Dict, subtotal: float, lines: List[Dict]) -> float:
        """Apply commitment-based discount if applicable."""
        if not tenant.get("commitment_discount"):
            return subtotal
        
        commitment_months = tenant.get("commitment_months", 0)
        discount_rate = 0
        label = None
        
        if commitment_months >= 12:
            discount_rate = 0.1
            label = "annual commitment"
        elif commitment_months >= 6:
            discount_rate = 0.05
            label = "6mo commitment"
        
        if discount_rate > 0:
            discount = subtotal * discount_rate
            subtotal -= discount
            lines.append({"desc": label, "amount": -discount})
        
        return subtotal

    def _calculate_tax(self, tenant: Dict, subtotal: float) -> float:
        """Calculate applicable tax for the tenant."""
        tax_rate = self._find_tax_rate(tenant)
        return subtotal * tax_rate

    def _find_tax_rate(self, tenant: Dict) -> float:
        """Find the applicable tax rate for a tenant."""
        country = tenant.get("country", "US")
        vat_id = tenant.get("vat_id")
        region = tenant.get("region")
        
        for rule in self.tax_rules:
            if rule["country"] != country:
                continue
            if rule.get("region") and rule["region"] != region:
                continue
            if rule.get("b2b") and not vat_id:
                continue
            if rule.get("b2b") is False and vat_id:
                continue
            return rule["rate"]
        
        return 0

    def _convert_currency(self, currency: str, total: float, subtotal: float, tax: float,
                         lines: List[Dict], tenant_id: str) -> tuple[float, float, float, List[Dict]]:
        """Convert amounts to the specified currency."""
        rate = self.fx_rates.get(currency)
        if rate is None:
            self.audit.append(f"no fx {currency} for {tenant_id}")
            return total, subtotal, tax, lines
        
        lines = [{"desc": ln["desc"], "amount": round(ln["amount"] * rate, 2)} for ln in lines]
        subtotal = round(subtotal * rate, 2)
        tax = round(tax * rate, 2)
        total = round(total * rate, 2)
        
        return total, subtotal, tax, lines
```

This refactoring makes the following improvements:

1. **Extracted methods**: Break `run_for_period` into smaller, focused methods that each handle one responsibility
2. **Event configuration mapping**: Eliminated repetitive usage event processing with an `EventKind` enum and `UsageEventConfig` dataclass
3. **Removed magic numbers**: Used constants and configuration objects
4. **Improved readability**: Using f-strings instead of string concatenation
5. **Type hints**: Added type annotations for better code documentation
6. **Cleaner conditionals**: Extracted complex logic into dedicated methods
7. **Reduced nesting**: Each method handles one concern at an appropriate abstraction level
8. **Better encapsulation**: Private methods (prefixed with `_`) for internal logic
