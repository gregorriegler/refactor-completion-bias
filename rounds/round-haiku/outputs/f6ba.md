```python
from dataclasses import dataclass
from typing import Any

TAX_RATES = {
    "DE": 0.19,
    "AT": 0.20,
    "US": 0.07,
}


@dataclass
class Customer:
    name: str
    street: str
    city: str
    zip: str
    country: str

    def format_address(self) -> str:
        return "\n".join([
            self.name,
            self.street,
            f"{self.zip} {self.city}",
            self.country
        ])


@dataclass
class Invoice:
    customer: Customer
    items: list[dict[str, Any]]

    def tax_rate(self) -> float:
        return TAX_RATES.get(self.customer.country, 0.0)

    def total(self) -> float:
        subtotal = sum(item["price"] * item["qty"] for item in self.items)
        return subtotal * (1 + self.tax_rate())
```

Refactoring improvements:
- Extracted customer data into a separate `Customer` dataclass for better separation of concerns
- Used dataclasses with type hints for clarity
- Extracted magic tax rate values into a `TAX_RATES` dictionary for easier maintenance
- Simplified `tax_rate()` method using dict.get() instead of multiple if statements
- Improved `format_address()` using `"\n".join()` for better readability
- Reduced constructor parameters and dependencies in `Invoice`
