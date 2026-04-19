# Example 1: Long function with nested conditionals

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
