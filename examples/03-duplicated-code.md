# Example 3: Duplicated code across functions

```python
def export_users_csv(users, path):
    with open(path, "w") as f:
        f.write("id,name,email\n")
        for u in users:
            name = u["name"].replace(",", " ").replace("\n", " ")
            email = u["email"].replace(",", " ").replace("\n", " ")
            f.write(f"{u['id']},{name},{email}\n")

def export_orders_csv(orders, path):
    with open(path, "w") as f:
        f.write("id,user,total\n")
        for o in orders:
            user = o["user"].replace(",", " ").replace("\n", " ")
            f.write(f"{o['id']},{user},{o['total']}\n")

def export_products_csv(products, path):
    with open(path, "w") as f:
        f.write("sku,name,price\n")
        for p in products:
            name = p["name"].replace(",", " ").replace("\n", " ")
            f.write(f"{p['sku']},{name},{p['price']}\n")
```
