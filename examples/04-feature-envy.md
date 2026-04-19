# Example 4: Feature envy / data clumps

```python
class Invoice:
    def __init__(self, customer_name, customer_street, customer_city,
                 customer_zip, customer_country, items):
        self.customer_name = customer_name
        self.customer_street = customer_street
        self.customer_city = customer_city
        self.customer_zip = customer_zip
        self.customer_country = customer_country
        self.items = items

    def format_address(self):
        return (self.customer_name + "\n" +
                self.customer_street + "\n" +
                self.customer_zip + " " + self.customer_city + "\n" +
                self.customer_country)

    def tax_rate(self):
        if self.customer_country == "DE":
            return 0.19
        if self.customer_country == "AT":
            return 0.20
        if self.customer_country == "US":
            return 0.07
        return 0.0

    def total(self):
        subtotal = sum(i["price"] * i["qty"] for i in self.items)
        return subtotal * (1 + self.tax_rate())
```
