```python
from dataclasses import dataclass, field
from typing import List, Dict


TAX_RATES: Dict[str, float] = {
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
        return f"{self.name}\n{self.street}\n{self.zip_code} {self.city}\n{self.country}"


@dataclass
class Invoice:
    address: Address
    items: List[Dict] = field(default_factory=list)

    def tax_rate(self) -> float:
        return TAX_RATES.get(self.address.country, 0.0)

    def subtotal(self) -> float:
        return sum(item["price"] * item["qty"] for item in self.items)

    def total(self) -> float:
        return self.subtotal() * (1 + self.tax_rate())

    def format_address(self) -> str:
        return self.address.format()
```
