```python
import csv

def export_to_csv(data, path, headers, field_mapping):
    """
    Generic CSV exporter that handles any data structure.
    
    Args:
        data: List of dictionaries to export
        path: Output file path
        headers: List of column headers
        field_mapping: Dict mapping headers to dict keys or callables
    """
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for item in data:
            row = []
            for header in headers:
                value = field_mapping[header]
                if callable(value):
                    row.append(value(item))
                else:
                    row.append(item.get(value, ""))
            writer.writerow(row)


def export_users_csv(users, path):
    export_to_csv(
        users,
        path,
        headers=["id", "name", "email"],
        field_mapping={
            "id": "id",
            "name": "name",
            "email": "email",
        }
    )


def export_orders_csv(orders, path):
    export_to_csv(
        orders,
        path,
        headers=["id", "user", "total"],
        field_mapping={
            "id": "id",
            "user": "user",
            "total": "total",
        }
    )


def export_products_csv(products, path):
    export_to_csv(
        products,
        path,
        headers=["sku", "name", "price"],
        field_mapping={
            "sku": "sku",
            "name": "name",
            "price": "price",
        }
    )
```

This refactoring:
- Eliminates code duplication by extracting a generic `export_to_csv()` function
- Uses Python's built-in `csv` module instead of manual string manipulation, which properly handles escaping and edge cases
- Makes the field mappings explicit and easy to modify
- Supports both simple field references and custom transformations via callables
