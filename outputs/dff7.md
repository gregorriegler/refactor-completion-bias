```python
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Any


def _period_end(year: int, month: int) -> datetime:
    if month == 12:
        return datetime(year + 1, 1, 1) - timedelta(seconds=1)
    return datetime(year, month + 1, 1) - timedelta(seconds=1)


def _find_tax_rate(tax_rules: list, country: str, tenant: dict) -> float:
    for rule in tax_rules:
        if rule["country"] != country:
            continue
        if rule.get("region") and rule["region"] != tenant.get("region"):
            continue
        if rule.get("b2b") and not tenant.get("vat_id"):
            continue
        if rule.get("b2b") is False and tenant.get("vat_id"):
            continue
        return rule["rate"]
    return 0.0


def _apply_coupon(subtotal: float, coupon: dict, coupon_id: str) -> tuple[float, dict | None]:
    if coupon["type"] == "pct":
        discount = subtotal * coupon["value"]
    elif coupon["type"] == "flat":
        discount = min(coupon["value"], subtotal)
    else:
        return subtotal, None
    return subtotal - discount, {"desc": f"coupon {coupon_id}", "amount": -discount}


def _apply_commitment_discount(subtotal: float, months: int) -> tuple[float, dict | None]:
    if months >= 12:
        discount = subtotal * 0.10
        return subtotal - discount, {"desc": "annual commitment", "amount": -discount}
    if months >= 6:
        discount = subtotal * 0.05
        return subtotal - discount, {"desc": "6mo commitment", "amount": -discount}
    return subtotal, None


_USAGE_CONFIG = {
    "api_call": {
        "included_key": "included_api",
        "quantity_key": "count",
        "rate_key": "api_overage",
        "default_rate": 0.001,
        "desc_template": "api overage {over}",
    },
    "storage_gb": {
        "included_key": "included_storage",
        "quantity_key": "gb",
        "rate_key": "storage_overage",
        "default_rate": 0.10,
        "desc_template": "storage {over}GB",
    },
    "seats": {
        "included_key": "included_seats",
        "default_included": 1,
        "quantity_key": "seats",
        "rate_key": "seat_price",
        "default_rate": 10,
        "desc_template": "{over} extra seats",
    },
    "bandwidth_gb": {
        "included_key": "included_bw",
        "default_included": 100,
        "quantity_key": "gb",
        "rate_key": "bw_overage",
        "default_rate": 0.02,
        "desc_template": "bandwidth {over}GB",
    },
}


def _calc_usage_line(event: dict, plan: dict, cfg: dict) -> tuple[float, dict | None]:
    included = plan.get(cfg["included_key"], cfg.get("default_included", 0))
    quantity = event[cfg["quantity_key"]]
    over = max(0, quantity - included)
    rate = plan.get(cfg["rate_key"], cfg["default_rate"])
    cost = over * rate
    if cost == 0:
        return 0.0, None
    desc = cfg["desc_template"].format(over=over)
    return cost, {"desc": desc, "amount": cost}


def _convert_currency(inv: dict, lines: list, rate: float) -> dict:
    for ln in lines:
        ln["amount"] = round(ln["amount"] * rate, 2)
    return {
        **inv,
        "subtotal": round(inv["subtotal"] * rate, 2),
        "tax": round(inv["tax"] * rate, 2),
        "total": round(inv["total"] * rate, 2),
    }


@dataclass
class BillingEngine:
    tenants: dict
    plans: dict
    usage_log: list
    coupons: dict
    fx_rates: dict
    tax_rules: list
    invoices: list = field(default_factory=list)
    audit: list = field(default_factory=list)

    def run_for_period(self, year: int, month: int) -> list:
        period_start = datetime(year, month, 1)
        period_end = _period_end(year, month)

        for tid, tenant in self.tenants.items():
            inv = self._build_invoice(tid, tenant, period_start, period_end)
            if inv is not None:
                self.invoices.append(inv)
                self.audit.append(f"invoiced {tid} {inv['total']}")

        return self.invoices

    def _build_invoice(
        self, tid: str, tenant: dict, period_start: datetime, period_end: datetime
    ) -> dict | None:
        if self._should_skip(tid, tenant, period_start):
            return None

        plan = self.plans.get(tenant["plan"])
        if not plan:
            self.audit.append(f"no plan {tid}")
            return None

        lines: list[dict] = []
        base = self._calc_base(tenant, plan, period_end, lines)
        usage_total = self._calc_usage(tid, tenant, plan, period_start, period_end, lines)

        subtotal = base + usage_total
        subtotal = self._apply_discounts(subtotal, tenant, period_end, lines)

        country = tenant.get("country", "US")
        tax_rate = _find_tax_rate(self.tax_rules, country, tenant)
        tax = subtotal * tax_rate
        total = subtotal + tax

        inv = {
            "tenant": tid,
            "period": period_start.strftime("%Y-%m"),
            "lines": lines,
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "currency": tenant.get("currency", "USD"),
        }

        currency = tenant.get("currency", "USD")
        if currency != "USD":
            fx = self.fx_rates.get(currency)
            if fx is None:
                self.audit.append(f"no fx {currency} for {tid}")
            else:
                inv = _convert_currency(inv, lines, fx)

        return inv

    def _should_skip(self, tid: str, tenant: dict, period_start: datetime) -> bool:
        if tenant.get("status") == "cancelled":
            cancelled_at = tenant.get("cancelled_at")
            if cancelled_at and cancelled_at < period_start:
                self.audit.append(f"skip cancelled {tid}")
                return True
        return False

    def _calc_base(
        self, tenant: dict, plan: dict, period_end: datetime, lines: list
    ) -> float:
        base = plan["base_price"]
        if tenant.get("status") == "trial":
            trial_ends = tenant.get("trial_ends")
            if trial_ends and trial_ends >= period_end:
                lines.append({"desc": "trial", "amount": 0})
                return 0.0
            days_paid = (period_end - trial_ends).days
            base = round(base * (days_paid / 30.0), 2)
            lines.append({"desc": "partial base (post-trial)", "amount": base})
        else:
            lines.append({"desc": f"{plan['name']} base", "amount": base})
        return base

    def _calc_usage(
        self,
        tid: str,
        tenant: dict,
        plan: dict,
        period_start: datetime,
        period_end: datetime,
        lines: list,
    ) -> float:
        total = 0.0
        for event in self.usage_log:
            if event["tenant"] != tid:
                continue
            if not (period_start <= event["ts"] <= period_end):
                continue
            kind = event["kind"]
            cfg = _USAGE_CONFIG.get(kind)
            if cfg is None:
                self.audit.append(f"unknown usage kind {kind} for {tid}")
                continue
            cost, line = _calc_usage_line(event, plan, cfg)
            total += cost
            if line:
                lines.append(line)
        return total

    def _apply_discounts(
        self, subtotal: float, tenant: dict, period_end: datetime, lines: list
    ) -> float:
        if tenant.get("coupon"):
            coupon = self.coupons.get(tenant["coupon"])
            if coupon and coupon.get("valid_until", period_end) >= period_end:
                subtotal, line = _apply_coupon(subtotal, coupon, tenant["coupon"])
                if line:
                    lines.append(line)

        if tenant.get("commitment_discount"):
            subtotal, line = _apply_commitment_discount(
                subtotal, tenant["commitment_months"]
            )
            if line:
                lines.append(line)

        return subtotal
```

- Converted `BillingEngine` to a `@dataclass`, eliminating the boilerplate `__init__`.
- Extracted `run_for_period` logic into focused private methods: `_should_skip`, `_calc_base`, `_calc_usage`, `_apply_discounts`, and `_build_invoice`, so each method has a single responsibility.
- Replaced the four nearly-identical usage-kind `if/elif` blocks with a `_USAGE_CONFIG` dispatch table and a single `_calc_usage_line` helper, removing the repetition entirely.
- Extracted pure, stateless functions (`_period_end`, `_find_tax_rate`, `_apply_coupon`, `_apply_commitment_discount`, `_convert_currency`) that are easy to unit-test in isolation.
- Replaced string concatenation throughout with f-strings for readability.
- Added type annotations to all function signatures.
