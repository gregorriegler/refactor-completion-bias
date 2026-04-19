```python
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class UserTier(Enum):
    GOLD = 0.8
    SILVER = 0.9
    STANDARD = 1.0


class CouponType(Enum):
    PERCENT = "percent"
    FIXED = "fixed"


@dataclass
class Item:
    sku: str
    qty: int


@dataclass
class InventoryEntry:
    qty: int
    price: float


TAX_RATES = {
    "DE": 1.19,
    "US": 1.07,
}
BULK_DISCOUNT_THRESHOLD = 1000
BULK_DISCOUNT_RATE = 0.95


def get_member_discount(user: Dict[str, Any]) -> float:
    """Get the membership discount multiplier for a user."""
    if not user.get("is_member"):
        return 1.0
    
    tier = user.get("tier", "").upper()
    try:
        return UserTier[tier].value
    except KeyError:
        return 1.0


def apply_coupon(price: float, coupon_code: Optional[str], coupons: Dict[str, Any]) -> float:
    """Apply coupon discount to price if applicable."""
    if not coupon_code or coupon_code not in coupons:
        return price
    
    coupon = coupons[coupon_code]
    if price < coupon.get("min", 0):
        return price
    
    if coupon.get("type") == CouponType.PERCENT.value:
        return price * (1 - coupon.get("value", 0))
    else:
        return price - coupon.get("value", 0)


def apply_tax(price: float, country: Optional[str]) -> float:
    """Apply country-specific tax to price."""
    rate = TAX_RATES.get(country, 1.0)
    return price * rate


def calculate_item_price(
    item: Dict[str, Any],
    inventory: Dict[str, Dict[str, Any]],
    member_discount: float,
    coupon_code: Optional[str],
    coupons: Dict[str, Any],
) -> float:
    """Calculate price for a single item with all applicable discounts."""
    sku = item.get("sku")
    if sku not in inventory:
        raise ValueError(f"unknown sku: {sku}")
    
    stock = inventory[sku]
    qty = item.get("qty", 0)
    
    if stock.get("qty", 0) < qty:
        raise ValueError(f"out of stock: {sku}")
    
    price = stock.get("price", 0) * qty
    price *= member_discount
    price = apply_coupon(price, coupon_code, coupons)
    
    return price


def process_order(order: Dict[str, Any], user: Dict[str, Any], inventory: Dict[str, Any], coupons: Dict[str, Any]) -> float:
    """Process an order and return the total price with taxes."""
    if not order or not order.get("items"):
        return 0.0
    
    member_discount = get_member_discount(user)
    coupon_code = order.get("coupon")
    
    total = sum(
        calculate_item_price(item, inventory, member_discount, coupon_code, coupons)
        for item in order["items"]
    )
    
    # Apply bulk discount
    if total > BULK_DISCOUNT_THRESHOLD:
        total *= BULK_DISCOUNT_RATE
    
    # Apply tax
    total = apply_tax(total, user.get("country"))
    
    return round(total, 2)
```

Refactoring highlights:
- Extracted helper functions to reduce nesting and improve testability
- Added type hints for clarity
- Defined constants and enums for magic numbers and string literals
- Simplified the main function logic using list comprehension
- Better separation of concerns (discounts, coupons, taxes)
- More descriptive variable names and clearer error messages
- Made the code more modular and easier to extend (e.g., adding new tax rates or coupon types)
