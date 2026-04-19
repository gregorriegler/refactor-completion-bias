```python
from dataclasses import dataclass
from typing import List, Dict

# Tax rates by country
TAX_RATES = {
    "DE": 0.19,
    "AT": 0.20,
    "US": 0.07,
}

@dataclass
class Address:
    name: str
    street: str
    city: str
    zip_code: str
    country: str

    def format(self) -> str:
        return (
            f"{self.name}\n"
            f"{self.street}\n"
            f"{self.zip_code} {self.city}\n"
            f"{self.country}"
        )


@dataclass
class Invoice:
    customer: Address
    items: List[Dict[str, float]]

    def tax_rate(self) -> float:
        return TAX_RATES.get(self.customer.country, 0.0)

    def total(self) -> float:
        subtotal = sum(item["price"] * item["qty"] for item in self.items)
        return subtotal * (1 + self.tax_rate())
```

Notes: Refactored to use dataclasses for cleaner initialization and representation. Extracted address data into its own `Address` class to better separate concerns. Moved tax rates to a module-level dict for easier maintenance. Used f-strings and the `dict.get()` method for cleaner code. Removed the redundant `format_address` method and integrated address formatting into the `Address` class.
