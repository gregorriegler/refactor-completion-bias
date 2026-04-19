```python
# Constants for discount rates and thresholds
MEMBER_DISCOUNT = {"gold": 0.20, "silver": 0.10}  # percentage discounts
BULK_DISCOUNT_THRESHOLD = 1000
BULK_DISCOUNT_RATE = 0.05  # 5% off for orders over 1000
TAX_RATES = {"DE": 0.19, "US": 0.07}  # VAT/sales tax by country


def process_order(order, user, inventory, coupons):
    """
    Calculate the final price of an order with member discounts, coupons, and tax.
    
    Args:
        order: dict with 'items' (list) and optional 'coupon' (str)
        user: dict with 'is_member' (bool), 'tier' (str), 'country' (str)
        inventory: dict mapping SKU to {'qty': int, 'price': float}
        coupons: dict mapping coupon code to {'type': str, 'value': float, 'min': float}
    
    Returns:
        float: Final price rounded to 2 decimals
    
    Raises:
        ValueError: If item not in inventory or insufficient stock
    """
    if not order or not order.get("items"):
        return 0.0
    
    total = 0.0
    
    for item in order["items"]:
        sku = item.get("sku")
        qty = item.get("qty", 0)
        
        if sku not in inventory:
            raise ValueError(f"unknown sku: {sku}")
        
        stock = inventory[sku]
        if stock["qty"] < qty:
            raise ValueError(f"out of stock: {sku}")
        
        # Calculate base item price
        price = stock["price"] * qty
        
        # Apply member discount
        if user.get("is_member"):
            tier = user.get("tier")
            discount = MEMBER_DISCOUNT.get(tier, 0)
            price *= (1 - discount)
        
        # Apply coupon if valid
        if order.get("coupon") in coupons:
            coupon = coupons[order["coupon"]]
            if price >= coupon["min"]:
                if coupon["type"] == "percent":
                    price *= (1 - coupon["value"])
                else:
                    price -= coupon["value"]
        
        total += price
    
    # Apply bulk discount
    if total > BULK_DISCOUNT_THRESHOLD:
        total *= (1 - BULK_DISCOUNT_RATE)
    
    # Apply tax based on country
    country = user.get("country")
    if country in TAX_RATES:
        total *= (1 + TAX_RATES[country])
    
    return round(total, 2)
```

## Refactoring Notes

**Key improvements:**

1. **Constants extracted** — magic numbers for discounts and thresholds are now named constants, making the function easier to maintain and modify.

2. **Reduced nesting** — replaced deeply nested if-statements with guard clauses (early return, early validation) and dictionary lookups with `.get()` defaults.

3. **Clearer logic flow** — the function now processes items in order: validate → base price → member discount → coupon → total bulk discount → tax.

4. **Better error messages** — switched to f-strings for clarity and maintainability.

5. **Data-driven discount logic** — member discounts stored in a dict rather than hardcoded elif chains; tax rates similarly data-driven.

6. **Added docstring** — documents function purpose, arguments, return value, and exceptions.

7. **Dictionary access safety** — uses `.get()` with sensible defaults to avoid KeyError and reduce defensive checks.

The refactored version is more maintainable (easier to add new tiers or tax rates), more readable (logic is linear rather than pyramidal), and follows Python conventions (constants in UPPER_CASE, docstrings, early returns).
