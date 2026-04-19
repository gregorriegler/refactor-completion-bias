# Example 6: If-elif chain begging for polymorphism

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
