```python
def process_order(order, user, inventory, coupons):
    """Calculate the total order price with discounts, stock validation, and taxes."""
    if not order or not order.get("items"):
        return 0.0
    
    total = 0.0
    
    for item in order["items"]:
        total += _calculate_item_price(item, inventory, user, order, coupons)
    
    # Apply bulk discount
    if total > 1000:
        total *= 0.95
    
    # Apply tax based on country
    total = _apply_tax(total, user.get("country"))
    
    return round(total, 2)


def _calculate_item_price(item, inventory, user, order, coupons):
    """Calculate the price for a single item with member discount and coupon."""
    sku = item.get("sku")
    if sku not in inventory:
        raise ValueError(f"unknown sku: {sku}")
    
    stock = inventory[sku]
    qty = item.get("qty", 0)
    
    if stock["qty"] < qty:
        raise ValueError(f"out of stock: {sku}")
    
    price = stock["price"] * qty
    
    # Apply member discount
    price = _apply_member_discount(price, user)
    
    # Apply coupon discount
    if order.get("coupon") and order["coupon"] in coupons:
        price = _apply_coupon(price, coupons[order["coupon"]])
    
    return price


def _apply_member_discount(price, user):
    """Apply member tier discount to price."""
    if not user.get("is_member"):
        return price
    
    tier = user.get("tier")
    if tier == "gold":
        return price * 0.8
    elif tier == "silver":
        return price * 0.9
    
    return price


def _apply_coupon(price, coupon):
    """Apply coupon discount to price if applicable."""
    if price < coupon["min"]:
        return price
    
    if coupon["type"] == "percent":
        return price * (1 - coupon["value"])
    else:
        return price - coupon["value"]


def _apply_tax(total, country):
    """Apply country-specific tax to total."""
    if country == "DE":
        return total * 1.19
    elif country == "US":
        return total * 1.07
    return total
```

Refactoring improvements:
- Extracted nested logic into focused helper functions for better readability
- Replaced early return with early exit to reduce nesting
- Used f-strings for clearer error messages
- Added docstrings to clarify intent
- Made tax application a separate function (easier to extend)
- Separated concerns: member discount, coupon, tax calculations are now isolated
- Reduced cyclomatic complexity and improved testability
