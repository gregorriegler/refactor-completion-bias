```python
import csv
from typing import Any, List

def export_to_csv(items: List[dict], path: str, fieldnames: List[str], 
                   sanitize_fields: List[str] = None) -> None:
    """Export a list of dictionaries to a CSV file.
    
    Args:
        items: List of dictionaries to export
        path: File path to write CSV to
        fieldnames: Column names in order
        sanitize_fields: Field names that should have commas/newlines removed
    """
    if sanitize_fields is None:
        sanitize_fields = []
    
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in items:
            row = item.copy()
            for field in sanitize_fields:
                if field in row and isinstance(row[field], str):
                    row[field] = row[field].replace(",", " ").replace("\n", " ")
            writer.writerow(row)


def export_users_csv(users: List[dict], path: str) -> None:
    """Export users to CSV."""
    export_to_csv(users, path, ["id", "name", "email"], 
                   sanitize_fields=["name", "email"])


def export_orders_csv(orders: List[dict], path: str) -> None:
    """Export orders to CSV."""
    export_to_csv(orders, path, ["id", "user", "total"],
                   sanitize_fields=["user"])


def export_products_csv(products: List[dict], path: str) -> None:
    """Export products to CSV."""
    export_to_csv(products, path, ["sku", "name", "price"],
                   sanitize_fields=["name"])
```

## Refactoring notes:

- **DRY principle**: Extracted common CSV export logic into a generic `export_to_csv()` function
- **CSV handling**: Now uses Python's `csv` module which properly handles special characters, quoting, and escaping per RFC 4180
- **Type hints**: Added type annotations for clarity and better IDE support
- **Sanitization**: Sanitization logic is centralized and applied only to fields that need it
- **Backward compatibility**: The original three functions are preserved with the same signatures, maintaining the public API
- **Configurability**: The generic function is flexible enough to handle different export formats without duplication
- **Docstrings**: Added documentation for the functions
