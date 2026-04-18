# Blind Judging Package

**Do not open `manifest.json` or `judge_letter_map.json` until after you have filled in `rankings.md`.** Both files contain the condition→variant mapping and will bias your judgement.

You are the human judge. For each of the 10 examples below you will see:
  1. The original Python snippet.
  2. Six anonymous refactored variants labelled A–F, each tagged with a short hex id.

For each example, rank the six variants from best (1) to worst (6) based on refactoring quality — correctness preservation, readability, appropriate structural improvement, and good judgement about what to change vs leave alone. Record your ranks in `rankings.md`.

Variants were produced under two different prompting conditions (not disclosed until after you rank). Rank purely on the code; do not try to guess which condition produced which variant.

---

## Example 1: Long function with nested conditionals

### Original

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

### Variants

#### Variant A  (`4936`)

```python
MEMBER_DISCOUNTS = {"gold": 0.8, "silver": 0.9}
TAX_RATES = {"DE": 1.19, "US": 1.07}


def apply_member_discount(price, user):
    if not user.get("is_member"):
        return price
    factor = MEMBER_DISCOUNTS.get(user.get("tier"), 1.0)
    return price * factor


def apply_coupon(price, coupon):
    if coupon is None:
        return price
    if coupon["min"] > price:
        return price
    if coupon["type"] == "percent":
        return price * (1 - coupon["value"])
    return price - coupon["value"]


def apply_tax(total, country):
    return total * TAX_RATES.get(country, 1.0)


def calculate_item_price(item, inventory):
    sku = item.get("sku")
    if sku not in inventory:
        raise ValueError(f"unknown sku: {sku}")
    stock = inventory[sku]
    if stock["qty"] < item["qty"]:
        raise ValueError(f"out of stock: {sku}")
    return stock["price"] * item["qty"]


def process_order(order, user, inventory, coupons):
    if not order or not order.get("items"):
        return 0.0

    coupon_code = order.get("coupon")
    coupon = coupons.get(coupon_code) if coupon_code else None

    total = 0.0
    for item in order["items"]:
        price = calculate_item_price(item, inventory)
        price = apply_member_discount(price, user)
        price = apply_coupon(price, coupon)
        total += price

    if total > 1000:
        total *= 0.95

    total = apply_tax(total, user.get("country"))
    return round(total, 2)
```

#### Variant B  (`7703`)

```python
MEMBER_DISCOUNTS = {
    "gold": 0.80,
    "silver": 0.90,
}

TAX_RATES = {
    "DE": 1.19,
    "US": 1.07,
}

BULK_DISCOUNT_THRESHOLD = 1000
BULK_DISCOUNT_RATE = 0.95


def get_member_discount(user):
    if not user.get("is_member"):
        return 1.0
    return MEMBER_DISCOUNTS.get(user.get("tier"), 1.0)


def apply_coupon(price, coupon_code, coupons):
    if not coupon_code or coupon_code not in coupons:
        return price
    coupon = coupons[coupon_code]
    if price < coupon["min"]:
        return price
    if coupon["type"] == "percent":
        return price * (1 - coupon["value"])
    return price - coupon["value"]


def calculate_item_price(item, inventory, user, coupon_code, coupons):
    sku = item.get("sku")
    if sku not in inventory:
        raise ValueError(f"unknown sku: {sku}")

    stock = inventory[sku]
    qty = item["qty"]
    if stock["qty"] < qty:
        raise ValueError(f"out of stock: {sku}")

    price = stock["price"] * qty
    price *= get_member_discount(user)
    price = apply_coupon(price, coupon_code, coupons)
    return price


def apply_tax(total, country):
    rate = TAX_RATES.get(country, 1.0)
    return total * rate


def process_order(order, user, inventory, coupons):
    if not order or not order.get("items"):
        return 0.0

    coupon_code = order.get("coupon")
    total = sum(
        calculate_item_price(item, inventory, user, coupon_code, coupons)
        for item in order["items"]
    )

    if total > BULK_DISCOUNT_THRESHOLD:
        total *= BULK_DISCOUNT_RATE

    total = apply_tax(total, user.get("country"))
    return round(total, 2)
```

#### Variant C  (`f12b`)

```python
MEMBER_DISCOUNTS = {
    "gold": 0.80,
    "silver": 0.90,
}

TAX_RATES = {
    "DE": 1.19,
    "US": 1.07,
}

BULK_DISCOUNT_THRESHOLD = 1000
BULK_DISCOUNT_RATE = 0.95


def apply_member_discount(price, user):
    if not user.get("is_member"):
        return price
    rate = MEMBER_DISCOUNTS.get(user.get("tier"))
    return price * rate if rate is not None else price


def apply_coupon(price, coupon_code, coupons):
    if not coupon_code or coupon_code not in coupons:
        return price
    coupon = coupons[coupon_code]
    if price < coupon["min"]:
        return price
    if coupon["type"] == "percent":
        return price * (1 - coupon["value"])
    return price - coupon["value"]


def calculate_item_price(item, inventory, user, coupon_code, coupons):
    sku = item.get("sku")
    if sku not in inventory:
        raise ValueError("unknown sku: " + sku)
    stock = inventory[sku]
    if stock["qty"] < item["qty"]:
        raise ValueError("out of stock: " + sku)
    price = stock["price"] * item["qty"]
    price = apply_member_discount(price, user)
    price = apply_coupon(price, coupon_code, coupons)
    return price


def process_order(order, user, inventory, coupons):
    if not order or not order.get("items"):
        return 0.0

    coupon_code = order.get("coupon")
    total = sum(
        calculate_item_price(item, inventory, user, coupon_code, coupons)
        for item in order["items"]
    )

    if total > BULK_DISCOUNT_THRESHOLD:
        total *= BULK_DISCOUNT_RATE

    tax_rate = TAX_RATES.get(user.get("country"), 1.0)
    total *= tax_rate

    return round(total, 2)
```

#### Variant D  (`7367`)

```python
MEMBER_DISCOUNTS = {"gold": 0.80, "silver": 0.90}
TAX_RATES = {"DE": 1.19, "US": 1.07}


def apply_member_discount(price, user):
    if not user.get("is_member"):
        return price
    multiplier = MEMBER_DISCOUNTS.get(user.get("tier"), 1.0)
    return price * multiplier


def apply_coupon(price, coupon):
    if coupon is None or price < coupon["min"]:
        return price
    if coupon["type"] == "percent":
        return price * (1 - coupon["value"])
    return price - coupon["value"]


def calculate_item_price(item, inventory, user, coupon):
    sku = item.get("sku")
    if sku not in inventory:
        raise ValueError(f"unknown sku: {sku}")
    stock = inventory[sku]
    if stock["qty"] < item["qty"]:
        raise ValueError(f"out of stock: {sku}")
    price = stock["price"] * item["qty"]
    price = apply_member_discount(price, user)
    price = apply_coupon(price, coupon)
    return price


def apply_bulk_discount(total):
    return total * 0.95 if total > 1000 else total


def apply_tax(total, country):
    return total * TAX_RATES.get(country, 1.0)


def process_order(order, user, inventory, coupons):
    if not order or not order.get("items"):
        return 0.0

    coupon = coupons.get(order["coupon"]) if order.get("coupon") else None

    total = sum(
        calculate_item_price(item, inventory, user, coupon)
        for item in order["items"]
    )

    total = apply_bulk_discount(total)
    total = apply_tax(total, user.get("country"))
    return round(total, 2)
```

#### Variant E  (`c4b3`)

```python
MEMBER_DISCOUNTS = {
    "gold": 0.8,
    "silver": 0.9,
}

TAX_RATES = {
    "DE": 1.19,
    "US": 1.07,
}

BULK_DISCOUNT_THRESHOLD = 1000
BULK_DISCOUNT_RATE = 0.95


def apply_member_discount(price, user):
    if not user.get("is_member"):
        return price
    rate = MEMBER_DISCOUNTS.get(user.get("tier"), 1.0)
    return price * rate


def apply_coupon(price, coupon_code, coupons):
    if not coupon_code or coupon_code not in coupons:
        return price
    coupon = coupons[coupon_code]
    if price < coupon["min"]:
        return price
    if coupon["type"] == "percent":
        return price * (1 - coupon["value"])
    return price - coupon["value"]


def calculate_item_price(item, inventory, user, coupon_code, coupons):
    sku = item.get("sku")
    if sku not in inventory:
        raise ValueError("unknown sku: " + sku)
    stock = inventory[sku]
    if stock["qty"] < item["qty"]:
        raise ValueError("out of stock: " + sku)
    price = stock["price"] * item["qty"]
    price = apply_member_discount(price, user)
    price = apply_coupon(price, coupon_code, coupons)
    return price


def apply_tax(total, country):
    return total * TAX_RATES.get(country, 1.0)


def process_order(order, user, inventory, coupons):
    if not order or not order.get("items"):
        return 0.0

    coupon_code = order.get("coupon")
    total = sum(
        calculate_item_price(item, inventory, user, coupon_code, coupons)
        for item in order["items"]
    )

    if total > BULK_DISCOUNT_THRESHOLD:
        total *= BULK_DISCOUNT_RATE

    total = apply_tax(total, user.get("country"))

    return round(total, 2)
```

#### Variant F  (`ed76`)

```python
MEMBER_DISCOUNTS = {
    "gold": 0.80,
    "silver": 0.90,
}

TAX_RATES = {
    "DE": 1.19,
    "US": 1.07,
}

BULK_DISCOUNT_THRESHOLD = 1000
BULK_DISCOUNT_RATE = 0.95


def _get_member_discount(user):
    if not user.get("is_member"):
        return 1.0
    return MEMBER_DISCOUNTS.get(user.get("tier"), 1.0)


def _apply_coupon(price, coupon_code, coupons):
    if not coupon_code or coupon_code not in coupons:
        return price
    coupon = coupons[coupon_code]
    if price < coupon["min"]:
        return price
    if coupon["type"] == "percent":
        return price * (1 - coupon["value"])
    return price - coupon["value"]


def _calculate_item_price(item, inventory, user, coupon_code, coupons):
    sku = item.get("sku")
    if sku not in inventory:
        raise ValueError("unknown sku: " + sku)
    stock = inventory[sku]
    if stock["qty"] < item["qty"]:
        raise ValueError("out of stock: " + sku)
    price = stock["price"] * item["qty"]
    price *= _get_member_discount(user)
    price = _apply_coupon(price, coupon_code, coupons)
    return price


def _apply_bulk_discount(total):
    if total > BULK_DISCOUNT_THRESHOLD:
        return total * BULK_DISCOUNT_RATE
    return total


def _apply_tax(total, country):
    return total * TAX_RATES.get(country, 1.0)


def process_order(order, user, inventory, coupons):
    if not order or not order.get("items"):
        return 0.0

    coupon_code = order.get("coupon")
    total = sum(
        _calculate_item_price(item, inventory, user, coupon_code, coupons)
        for item in order["items"]
    )

    total = _apply_bulk_discount(total)
    total = _apply_tax(total, user.get("country"))

    return round(total, 2)
```

---

## Example 2: Class with too many responsibilities

### Original

```python
import smtplib
import sqlite3
from email.message import EmailMessage

class UserManager:
    def __init__(self, db_path, smtp_host):
        self.conn = sqlite3.connect(db_path)
        self.smtp_host = smtp_host

    def register(self, email, password):
        if "@" not in email:
            raise ValueError("bad email")
        if len(password) < 8:
            raise ValueError("password too short")
        hashed = "".join(reversed(password)) + "_salt"
        cur = self.conn.cursor()
        cur.execute("INSERT INTO users(email, pw) VALUES (?, ?)", (email, hashed))
        self.conn.commit()
        msg = EmailMessage()
        msg["Subject"] = "Welcome"
        msg["To"] = email
        msg.set_content("Thanks for registering, " + email)
        with smtplib.SMTP(self.smtp_host) as s:
            s.send_message(msg)
        with open("audit.log", "a") as f:
            f.write("registered " + email + "\n")

    def login(self, email, password):
        hashed = "".join(reversed(password)) + "_salt"
        cur = self.conn.cursor()
        cur.execute("SELECT pw FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        if not row or row[0] != hashed:
            with open("audit.log", "a") as f:
                f.write("failed login " + email + "\n")
            return False
        with open("audit.log", "a") as f:
            f.write("login " + email + "\n")
        return True
```

### Variants

#### Variant A  (`f8c7`)

```python
import logging
import smtplib
import sqlite3
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return "".join(reversed(password)) + "_salt"


class UserManager:
    def __init__(self, db_path: str, smtp_host: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.smtp_host = smtp_host

    def _send_welcome_email(self, email: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = "Welcome"
        msg["To"] = email
        msg.set_content(f"Thanks for registering, {email}")
        with smtplib.SMTP(self.smtp_host) as smtp:
            smtp.send_message(msg)

    def register(self, email: str, password: str) -> None:
        if "@" not in email:
            raise ValueError("Invalid email address")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        hashed = _hash_password(password)
        cur = self.conn.cursor()
        cur.execute("INSERT INTO users(email, pw) VALUES (?, ?)", (email, hashed))
        self.conn.commit()

        self._send_welcome_email(email)
        logger.info("registered %s", email)

    def login(self, email: str, password: str) -> bool:
        hashed = _hash_password(password)
        cur = self.conn.cursor()
        cur.execute("SELECT pw FROM users WHERE email = ?", (email,))
        row = cur.fetchone()

        if not row or row[0] != hashed:
            logger.warning("failed login %s", email)
            return False

        logger.info("login %s", email)
        return True
```

#### Variant B  (`0cdd`)

```python
import logging
import smtplib
import sqlite3
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return "".join(reversed(password)) + "_salt"


def _validate_email(email: str) -> None:
    if "@" not in email:
        raise ValueError("bad email")


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("password too short")


class AuditLogger:
    def __init__(self, log_path: str = "audit.log") -> None:
        self.log_path = log_path

    def log(self, message: str) -> None:
        with open(self.log_path, "a") as f:
            f.write(message + "\n")


class EmailSender:
    def __init__(self, smtp_host: str) -> None:
        self.smtp_host = smtp_host

    def send_welcome(self, email: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = "Welcome"
        msg["To"] = email
        msg.set_content("Thanks for registering, " + email)
        with smtplib.SMTP(self.smtp_host) as s:
            s.send_message(msg)


class UserRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert_user(self, email: str, hashed_password: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users(email, pw) VALUES (?, ?)",
            (email, hashed_password),
        )
        self.conn.commit()

    def get_password_hash(self, email: str) -> str | None:
        cur = self.conn.cursor()
        cur.execute("SELECT pw FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        return row[0] if row else None


class UserManager:
    def __init__(self, db_path: str, smtp_host: str) -> None:
        self._repo = UserRepository(sqlite3.connect(db_path))
        self._email_sender = EmailSender(smtp_host)
        self._audit = AuditLogger()

    def register(self, email: str, password: str) -> None:
        _validate_email(email)
        _validate_password(password)
        hashed = _hash_password(password)
        self._repo.insert_user(email, hashed)
        self._email_sender.send_welcome(email)
        self._audit.log(f"registered {email}")

    def login(self, email: str, password: str) -> bool:
        hashed = _hash_password(password)
        stored = self._repo.get_password_hash(email)
        if stored is None or stored != hashed:
            self._audit.log(f"failed login {email}")
            return False
        self._audit.log(f"login {email}")
        return True
```

#### Variant C  (`902a`)

```python
import hashlib
import logging
import smtplib
import sqlite3
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _validate_email(email: str) -> None:
    if "@" not in email:
        raise ValueError(f"Invalid email address: {email!r}")


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")


class UserManager:
    def __init__(self, db_path: str, smtp_host: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.smtp_host = smtp_host

    def register(self, email: str, password: str) -> None:
        _validate_email(email)
        _validate_password(password)

        hashed = _hash_password(password)
        cur = self.conn.cursor()
        cur.execute("INSERT INTO users (email, pw) VALUES (?, ?)", (email, hashed))
        self.conn.commit()

        self._send_welcome_email(email)
        logger.info("registered %s", email)

    def login(self, email: str, password: str) -> bool:
        hashed = _hash_password(password)
        cur = self.conn.cursor()
        cur.execute("SELECT pw FROM users WHERE email = ?", (email,))
        row = cur.fetchone()

        if not row or row[0] != hashed:
            logger.warning("failed login %s", email)
            return False

        logger.info("login %s", email)
        return True

    def _send_welcome_email(self, email: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = "Welcome"
        msg["To"] = email
        msg.set_content(f"Thanks for registering, {email}")
        with smtplib.SMTP(self.smtp_host) as s:
            s.send_message(msg)
```

#### Variant D  (`7faa`)

```python
import logging
import smtplib
import sqlite3
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return "".join(reversed(password)) + "_salt"


def _validate_email(email: str) -> None:
    if "@" not in email:
        raise ValueError("bad email")


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("password too short")


class AuditLogger:
    def __init__(self, log_path: str = "audit.log") -> None:
        self.log_path = log_path

    def log(self, message: str) -> None:
        with open(self.log_path, "a") as f:
            f.write(message + "\n")


class EmailSender:
    def __init__(self, smtp_host: str) -> None:
        self.smtp_host = smtp_host

    def send_welcome(self, email: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = "Welcome"
        msg["To"] = email
        msg.set_content("Thanks for registering, " + email)
        with smtplib.SMTP(self.smtp_host) as s:
            s.send_message(msg)


class UserRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert_user(self, email: str, hashed_password: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users(email, pw) VALUES (?, ?)",
            (email, hashed_password),
        )
        self.conn.commit()

    def get_password(self, email: str) -> str | None:
        cur = self.conn.cursor()
        cur.execute("SELECT pw FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        return row[0] if row else None


class UserManager:
    def __init__(self, db_path: str, smtp_host: str) -> None:
        conn = sqlite3.connect(db_path)
        self.repo = UserRepository(conn)
        self.email_sender = EmailSender(smtp_host)
        self.audit = AuditLogger()

    def register(self, email: str, password: str) -> None:
        _validate_email(email)
        _validate_password(password)
        hashed = _hash_password(password)
        self.repo.insert_user(email, hashed)
        self.email_sender.send_welcome(email)
        self.audit.log(f"registered {email}")

    def login(self, email: str, password: str) -> bool:
        hashed = _hash_password(password)
        stored = self.repo.get_password(email)
        if stored is None or stored != hashed:
            self.audit.log(f"failed login {email}")
            return False
        self.audit.log(f"login {email}")
        return True
```

#### Variant E  (`3a92`)

```python
import hashlib
import logging
import smtplib
import sqlite3
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _validate_email(email: str) -> None:
    if "@" not in email:
        raise ValueError(f"Invalid email address: {email!r}")


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")


class EmailService:
    def __init__(self, smtp_host: str, from_address: str = "noreply@example.com"):
        self.smtp_host = smtp_host
        self.from_address = from_address

    def send_welcome(self, to_address: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = "Welcome"
        msg["From"] = self.from_address
        msg["To"] = to_address
        msg.set_content(f"Thanks for registering, {to_address}")
        with smtplib.SMTP(self.smtp_host) as s:
            s.send_message(msg)


class UserRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert_user(self, email: str, hashed_password: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users(email, pw) VALUES (?, ?)",
            (email, hashed_password),
        )
        self.conn.commit()

    def get_password_hash(self, email: str) -> str | None:
        cur = self.conn.cursor()
        cur.execute("SELECT pw FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        return row[0] if row else None


class UserManager:
    def __init__(self, db_path: str, smtp_host: str):
        conn = sqlite3.connect(db_path)
        self._repo = UserRepository(conn)
        self._email_service = EmailService(smtp_host)

    def register(self, email: str, password: str) -> None:
        _validate_email(email)
        _validate_password(password)
        self._repo.insert_user(email, _hash_password(password))
        self._email_service.send_welcome(email)
        logger.info("registered %s", email)

    def login(self, email: str, password: str) -> bool:
        stored_hash = self._repo.get_password_hash(email)
        if stored_hash is None or stored_hash != _hash_password(password):
            logger.warning("failed login %s", email)
            return False
        logger.info("login %s", email)
        return True
```

#### Variant F  (`105c`)

```python
import logging
import smtplib
import sqlite3
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return "".join(reversed(password)) + "_salt"


def _validate_email(email: str) -> None:
    if "@" not in email:
        raise ValueError("bad email")


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("password too short")


class UserManager:
    def __init__(self, db_path: str, smtp_host: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.smtp_host = smtp_host

    def _get_cursor(self):
        return self.conn.cursor()

    def _send_welcome_email(self, email: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = "Welcome"
        msg["To"] = email
        msg.set_content(f"Thanks for registering, {email}")
        with smtplib.SMTP(self.smtp_host) as smtp:
            smtp.send_message(msg)

    def _insert_user(self, email: str, hashed_password: str) -> None:
        cur = self._get_cursor()
        cur.execute(
            "INSERT INTO users(email, pw) VALUES (?, ?)",
            (email, hashed_password),
        )
        self.conn.commit()

    def _fetch_stored_password(self, email: str) -> str | None:
        cur = self._get_cursor()
        cur.execute("SELECT pw FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        return row[0] if row else None

    def register(self, email: str, password: str) -> None:
        _validate_email(email)
        _validate_password(password)
        hashed = _hash_password(password)
        self._insert_user(email, hashed)
        self._send_welcome_email(email)
        logger.info("registered %s", email)

    def login(self, email: str, password: str) -> bool:
        hashed = _hash_password(password)
        stored = self._fetch_stored_password(email)
        if stored != hashed:
            logger.warning("failed login %s", email)
            return False
        logger.info("login %s", email)
        return True
```

---

## Example 3: Duplicated code across functions

### Original

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

### Variants

#### Variant A  (`7523`)

```python
import csv


def _sanitize(value):
    return str(value).replace(",", " ").replace("\n", " ")


def _export_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_users_csv(users, path):
    rows = [
        {
            "id": u["id"],
            "name": _sanitize(u["name"]),
            "email": _sanitize(u["email"]),
        }
        for u in users
    ]
    _export_csv(path, ["id", "name", "email"], rows)


def export_orders_csv(orders, path):
    rows = [
        {
            "id": o["id"],
            "user": _sanitize(o["user"]),
            "total": o["total"],
        }
        for o in orders
    ]
    _export_csv(path, ["id", "user", "total"], rows)


def export_products_csv(products, path):
    rows = [
        {
            "sku": p["sku"],
            "name": _sanitize(p["name"]),
            "price": p["price"],
        }
        for p in products
    ]
    _export_csv(path, ["sku", "name", "price"], rows)
```

#### Variant B  (`8c3e`)

```python
import csv


def _sanitize(value):
    return str(value).replace(",", " ").replace("\n", " ")


def _export_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        writer.writerows(rows)


def export_users_csv(users, path):
    _export_csv(
        path,
        ["id", "name", "email"],
        [(u["id"], _sanitize(u["name"]), _sanitize(u["email"])) for u in users],
    )


def export_orders_csv(orders, path):
    _export_csv(
        path,
        ["id", "user", "total"],
        [(o["id"], _sanitize(o["user"]), o["total"]) for o in orders],
    )


def export_products_csv(products, path):
    _export_csv(
        path,
        ["sku", "name", "price"],
        [(p["sku"], _sanitize(p["name"]), p["price"]) for p in products],
    )
```

#### Variant C  (`810d`)

```python
import csv


def _sanitize(value):
    return str(value).replace(",", " ").replace("\n", " ")


def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        writer.writerows(rows)


def export_users_csv(users, path):
    rows = [
        (u["id"], _sanitize(u["name"]), _sanitize(u["email"]))
        for u in users
    ]
    _write_csv(path, ["id", "name", "email"], rows)


def export_orders_csv(orders, path):
    rows = [
        (o["id"], _sanitize(o["user"]), o["total"])
        for o in orders
    ]
    _write_csv(path, ["id", "user", "total"], rows)


def export_products_csv(products, path):
    rows = [
        (p["sku"], _sanitize(p["name"]), p["price"])
        for p in products
    ]
    _write_csv(path, ["sku", "name", "price"], rows)
```

#### Variant D  (`892c`)

```python
import csv


def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export_users_csv(users, path):
    _write_csv(path, ["id", "name", "email"], users)


def export_orders_csv(orders, path):
    _write_csv(path, ["id", "user", "total"], orders)


def export_products_csv(products, path):
    _write_csv(path, ["sku", "name", "price"], products)
```

#### Variant E  (`1d03`)

```python
import csv


def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export_users_csv(users, path):
    _write_csv(path, ["id", "name", "email"], users)


def export_orders_csv(orders, path):
    _write_csv(path, ["id", "user", "total"], orders)


def export_products_csv(products, path):
    _write_csv(path, ["sku", "name", "price"], products)
```

#### Variant F  (`1ad6`)

```python
import csv


def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export_users_csv(users, path):
    _write_csv(path, ["id", "name", "email"], users)


def export_orders_csv(orders, path):
    _write_csv(path, ["id", "user", "total"], orders)


def export_products_csv(products, path):
    _write_csv(path, ["sku", "name", "price"], products)
```

---

## Example 4: Feature envy / data clumps

### Original

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

### Variants

#### Variant A  (`dcab`)

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

    def __str__(self) -> str:
        return f"{self.name}\n{self.street}\n{self.zip_code} {self.city}\n{self.country}"


@dataclass
class Invoice:
    address: Address
    items: List[Dict] = field(default_factory=list)

    @property
    def tax_rate(self) -> float:
        return TAX_RATES.get(self.address.country, 0.0)

    @property
    def subtotal(self) -> float:
        return sum(item["price"] * item["qty"] for item in self.items)

    @property
    def total(self) -> float:
        return self.subtotal * (1 + self.tax_rate)
```

#### Variant B  (`a810`)

```python
from dataclasses import dataclass, field
from typing import List


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

    def __str__(self) -> str:
        return f"{self.name}\n{self.street}\n{self.zip_code} {self.city}\n{self.country}"

    @property
    def tax_rate(self) -> float:
        return TAX_RATES.get(self.country, 0.0)


@dataclass
class LineItem:
    price: float
    qty: int

    @property
    def subtotal(self) -> float:
        return self.price * self.qty


@dataclass
class Invoice:
    customer: Address
    items: List[LineItem] = field(default_factory=list)

    @property
    def tax_rate(self) -> float:
        return self.customer.tax_rate

    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self.items)

    @property
    def total(self) -> float:
        return self.subtotal * (1 + self.tax_rate)
```

#### Variant C  (`af87`)

```python
from dataclasses import dataclass, field
from typing import List
from decimal import Decimal

TAX_RATES = {
    "DE": Decimal("0.19"),
    "AT": Decimal("0.20"),
    "US": Decimal("0.07"),
}


@dataclass
class Address:
    name: str
    street: str
    city: str
    zip_code: str
    country: str

    def __str__(self) -> str:
        return f"{self.name}\n{self.street}\n{self.zip_code} {self.city}\n{self.country}"


@dataclass
class LineItem:
    price: Decimal
    qty: int

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.qty


@dataclass
class Invoice:
    address: Address
    items: List[LineItem] = field(default_factory=list)

    @property
    def tax_rate(self) -> Decimal:
        return TAX_RATES.get(self.address.country, Decimal("0.0"))

    @property
    def subtotal(self) -> Decimal:
        return sum(item.subtotal for item in self.items)

    @property
    def total(self) -> Decimal:
        return self.subtotal * (1 + self.tax_rate)
```

#### Variant D  (`fc29`)

```python
from dataclasses import dataclass, field
from typing import List


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

    def __str__(self) -> str:
        return (
            f"{self.name}\n"
            f"{self.street}\n"
            f"{self.zip_code} {self.city}\n"
            f"{self.country}"
        )

    @property
    def tax_rate(self) -> float:
        return TAX_RATES.get(self.country, 0.0)


@dataclass
class LineItem:
    price: float
    qty: int

    @property
    def subtotal(self) -> float:
        return self.price * self.qty


@dataclass
class Invoice:
    address: Address
    items: List[LineItem] = field(default_factory=list)

    def format_address(self) -> str:
        return str(self.address)

    @property
    def tax_rate(self) -> float:
        return self.address.tax_rate

    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self.items)

    @property
    def total(self) -> float:
        return self.subtotal * (1 + self.tax_rate)
```

#### Variant E  (`8e70`)

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

    def __str__(self) -> str:
        return f"{self.name}\n{self.street}\n{self.zip_code} {self.city}\n{self.country}"


@dataclass
class Invoice:
    address: Address
    items: List[Dict] = field(default_factory=list)

    @property
    def tax_rate(self) -> float:
        return TAX_RATES.get(self.address.country, 0.0)

    @property
    def subtotal(self) -> float:
        return sum(item["price"] * item["qty"] for item in self.items)

    @property
    def total(self) -> float:
        return self.subtotal * (1 + self.tax_rate)

    def format_address(self) -> str:
        return str(self.address)
```

#### Variant F  (`fdcf`)

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

---

## Example 5: Long parameter list

### Original

```python
def create_report(title, author, start_date, end_date, include_charts,
                  include_tables, include_summary, include_appendix,
                  format_type, output_path, header_color, footer_color,
                  page_size, language, timezone):
    header = f"# {title}\nby {author} ({language})\n"
    header += f"Period: {start_date} - {end_date} ({timezone})\n"
    body = ""
    if include_summary:
        body += "## Summary\n...\n"
    if include_charts:
        body += "## Charts\n...\n"
    if include_tables:
        body += "## Tables\n...\n"
    if include_appendix:
        body += "## Appendix\n...\n"
    footer = f"<footer style='color:{footer_color}'>{page_size}</footer>"
    doc = header + body + footer
    if format_type == "html":
        doc = f"<html style='color:{header_color}'>{doc}</html>"
    with open(output_path, "w") as f:
        f.write(doc)
```

### Variants

#### Variant A  (`e8c6`)

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReportMetadata:
    title: str
    author: str
    start_date: str
    end_date: str
    language: str
    timezone: str


@dataclass
class ReportSections:
    include_summary: bool = False
    include_charts: bool = False
    include_tables: bool = False
    include_appendix: bool = False


@dataclass
class ReportStyle:
    header_color: str = "#000000"
    footer_color: str = "#000000"
    page_size: str = "A4"
    format_type: str = "text"


@dataclass
class ReportConfig:
    metadata: ReportMetadata
    sections: ReportSections = field(default_factory=ReportSections)
    style: ReportStyle = field(default_factory=ReportStyle)
    output_path: str = "report.txt"


def _build_header(meta: ReportMetadata) -> str:
    return (
        f"# {meta.title}\n"
        f"by {meta.author} ({meta.language})\n"
        f"Period: {meta.start_date} - {meta.end_date} ({meta.timezone})\n"
    )


def _build_body(sections: ReportSections) -> str:
    section_map = [
        (sections.include_summary, "## Summary\n...\n"),
        (sections.include_charts, "## Charts\n...\n"),
        (sections.include_tables, "## Tables\n...\n"),
        (sections.include_appendix, "## Appendix\n...\n"),
    ]
    return "".join(content for enabled, content in section_map if enabled)


def _build_footer(style: ReportStyle) -> str:
    return f"<footer style='color:{style.footer_color}'>{style.page_size}</footer>"


def _apply_format(doc: str, style: ReportStyle) -> str:
    if style.format_type == "html":
        return f"<html style='color:{style.header_color}'>{doc}</html>"
    return doc


def create_report(config: ReportConfig) -> None:
    header = _build_header(config.metadata)
    body = _build_body(config.sections)
    footer = _build_footer(config.style)
    doc = _apply_format(header + body + footer, config.style)
    with open(config.output_path, "w") as f:
        f.write(doc)
```

#### Variant B  (`9e71`)

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReportConfig:
    title: str
    author: str
    start_date: str
    end_date: str
    format_type: str
    output_path: str
    header_color: str
    footer_color: str
    page_size: str
    language: str
    timezone: str
    include_charts: bool = False
    include_tables: bool = False
    include_summary: bool = False
    include_appendix: bool = False


SECTION_ORDER = [
    ("include_summary", "Summary"),
    ("include_charts", "Charts"),
    ("include_tables", "Tables"),
    ("include_appendix", "Appendix"),
]


def _build_header(cfg: ReportConfig) -> str:
    return (
        f"# {cfg.title}\n"
        f"by {cfg.author} ({cfg.language})\n"
        f"Period: {cfg.start_date} - {cfg.end_date} ({cfg.timezone})\n"
    )


def _build_body(cfg: ReportConfig) -> str:
    sections = [
        f"## {label}\n...\n"
        for attr, label in SECTION_ORDER
        if getattr(cfg, attr)
    ]
    return "".join(sections)


def _build_footer(cfg: ReportConfig) -> str:
    return f"<footer style='color:{cfg.footer_color}'>{cfg.page_size}</footer>"


def _apply_format(doc: str, cfg: ReportConfig) -> str:
    if cfg.format_type == "html":
        return f"<html style='color:{cfg.header_color}'>{doc}</html>"
    return doc


def create_report(cfg: ReportConfig) -> None:
    doc = _build_header(cfg) + _build_body(cfg) + _build_footer(cfg)
    doc = _apply_format(doc, cfg)
    with open(cfg.output_path, "w") as f:
        f.write(doc)
```

#### Variant C  (`9661`)

```python
from dataclasses import dataclass, field
from typing import List


@dataclass
class ReportConfig:
    title: str
    author: str
    start_date: str
    end_date: str
    format_type: str
    output_path: str
    header_color: str
    footer_color: str
    page_size: str
    language: str
    timezone: str
    include_charts: bool = False
    include_tables: bool = False
    include_summary: bool = False
    include_appendix: bool = False


def _build_header(config: ReportConfig) -> str:
    return (
        f"# {config.title}\n"
        f"by {config.author} ({config.language})\n"
        f"Period: {config.start_date} - {config.end_date} ({config.timezone})\n"
    )


def _build_body(config: ReportConfig) -> str:
    sections = [
        (config.include_summary, "## Summary\n...\n"),
        (config.include_charts, "## Charts\n...\n"),
        (config.include_tables, "## Tables\n...\n"),
        (config.include_appendix, "## Appendix\n...\n"),
    ]
    return "".join(content for include, content in sections if include)


def _build_footer(config: ReportConfig) -> str:
    return f"<footer style='color:{config.footer_color}'>{config.page_size}</footer>"


def _apply_format(doc: str, config: ReportConfig) -> str:
    if config.format_type == "html":
        return f"<html style='color:{config.header_color}'>{doc}</html>"
    return doc


def create_report(config: ReportConfig) -> None:
    header = _build_header(config)
    body = _build_body(config)
    footer = _build_footer(config)
    doc = _apply_format(header + body + footer, config)
    with open(config.output_path, "w") as f:
        f.write(doc)
```

#### Variant D  (`444b`)

```python
from dataclasses import dataclass, field


@dataclass
class ReportConfig:
    title: str
    author: str
    start_date: str
    end_date: str
    format_type: str
    output_path: str
    header_color: str
    footer_color: str
    page_size: str
    language: str
    timezone: str
    include_charts: bool = False
    include_tables: bool = False
    include_summary: bool = False
    include_appendix: bool = False


SECTION_FLAGS = [
    ("include_summary", "Summary"),
    ("include_charts", "Charts"),
    ("include_tables", "Tables"),
    ("include_appendix", "Appendix"),
]


def _build_header(cfg: ReportConfig) -> str:
    return (
        f"# {cfg.title}\n"
        f"by {cfg.author} ({cfg.language})\n"
        f"Period: {cfg.start_date} - {cfg.end_date} ({cfg.timezone})\n"
    )


def _build_body(cfg: ReportConfig) -> str:
    return "".join(
        f"## {label}\n...\n"
        for flag, label in SECTION_FLAGS
        if getattr(cfg, flag)
    )


def _build_footer(cfg: ReportConfig) -> str:
    return f"<footer style='color:{cfg.footer_color}'>{cfg.page_size}</footer>"


def _apply_format(doc: str, cfg: ReportConfig) -> str:
    if cfg.format_type == "html":
        return f"<html style='color:{cfg.header_color}'>{doc}</html>"
    return doc


def create_report(cfg: ReportConfig) -> None:
    doc = _build_header(cfg) + _build_body(cfg) + _build_footer(cfg)
    doc = _apply_format(doc, cfg)
    with open(cfg.output_path, "w") as f:
        f.write(doc)
```

#### Variant E  (`73c1`)

```python
from dataclasses import dataclass, field


@dataclass
class ReportConfig:
    title: str
    author: str
    start_date: str
    end_date: str
    format_type: str
    output_path: str
    header_color: str
    footer_color: str
    page_size: str
    language: str
    timezone: str
    include_charts: bool = False
    include_tables: bool = False
    include_summary: bool = False
    include_appendix: bool = False


_SECTION_ORDER = [
    ("include_summary", "Summary"),
    ("include_charts", "Charts"),
    ("include_tables", "Tables"),
    ("include_appendix", "Appendix"),
]


def _build_header(config: ReportConfig) -> str:
    return (
        f"# {config.title}\n"
        f"by {config.author} ({config.language})\n"
        f"Period: {config.start_date} - {config.end_date} ({config.timezone})\n"
    )


def _build_body(config: ReportConfig) -> str:
    sections = [
        f"## {label}\n...\n"
        for attr, label in _SECTION_ORDER
        if getattr(config, attr)
    ]
    return "".join(sections)


def _build_footer(config: ReportConfig) -> str:
    return f"<footer style='color:{config.footer_color}'>{config.page_size}</footer>"


def _apply_format(doc: str, config: ReportConfig) -> str:
    if config.format_type == "html":
        return f"<html style='color:{config.header_color}'>{doc}</html>"
    return doc


def create_report(config: ReportConfig) -> None:
    doc = _build_header(config) + _build_body(config) + _build_footer(config)
    doc = _apply_format(doc, config)
    with open(config.output_path, "w") as f:
        f.write(doc)
```

#### Variant F  (`074f`)

```python
from dataclasses import dataclass


@dataclass
class ReportConfig:
    title: str
    author: str
    start_date: str
    end_date: str
    format_type: str
    output_path: str
    language: str
    timezone: str
    page_size: str
    header_color: str
    footer_color: str
    include_summary: bool = True
    include_charts: bool = True
    include_tables: bool = True
    include_appendix: bool = False


SECTIONS = [
    ("include_summary", "Summary"),
    ("include_charts", "Charts"),
    ("include_tables", "Tables"),
    ("include_appendix", "Appendix"),
]


def _build_header(cfg: ReportConfig) -> str:
    return (
        f"# {cfg.title}\n"
        f"by {cfg.author} ({cfg.language})\n"
        f"Period: {cfg.start_date} - {cfg.end_date} ({cfg.timezone})\n"
    )


def _build_body(cfg: ReportConfig) -> str:
    return "".join(
        f"## {heading}\n...\n"
        for attr, heading in SECTIONS
        if getattr(cfg, attr)
    )


def _build_footer(cfg: ReportConfig) -> str:
    return f"<footer style='color:{cfg.footer_color}'>{cfg.page_size}</footer>"


def _apply_format(doc: str, cfg: ReportConfig) -> str:
    if cfg.format_type == "html":
        return f"<html style='color:{cfg.header_color}'>{doc}</html>"
    return doc


def create_report(cfg: ReportConfig) -> None:
    doc = _build_header(cfg) + _build_body(cfg) + _build_footer(cfg)
    doc = _apply_format(doc, cfg)
    with open(cfg.output_path, "w") as f:
        f.write(doc)
```

---

## Example 6: If-elif chain begging for polymorphism

### Original

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

### Variants

#### Variant A  (`9abe`)

```python
CARRIER_CONFIG = {
    "ups": {
        "base": 5.0,
        "weight_threshold": 10,
        "weight_rate": 0.5,
        "express_multiplier": 1.8,
        "international_fee": 0,
    },
    "fedex": {
        "base": 6.0,
        "weight_threshold": 5,
        "weight_rate": 0.6,
        "express_multiplier": 2.0,
        "international_fee": 15,
    },
    "dhl": {
        "base": 7.0,
        "weight_threshold": 2,
        "weight_rate": 0.7,
        "express_multiplier": 1.9,
        "international_fee": 20,
    },
    "usps": {
        "base": 4.0,
        "weight_threshold": 1,
        "weight_rate": 0.4,
        "express_multiplier": 1.0,
        "international_fee": 0,
    },
}


def calculate_shipping(package, carrier):
    config = CARRIER_CONFIG.get(carrier)
    if config is None:
        raise ValueError("unknown carrier")

    cost = config["base"]

    excess_weight = package["weight"] - config["weight_threshold"]
    if excess_weight > 0:
        cost += excess_weight * config["weight_rate"]

    if package.get("international"):
        cost += config["international_fee"]

    if package.get("express"):
        cost *= config["express_multiplier"]

    return cost
```

#### Variant B  (`0f3b`)

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class CarrierConfig:
    base_rate: float
    weight_threshold: float
    weight_rate: float
    express_multiplier: Optional[float] = None
    international_surcharge: float = 0.0


CARRIER_CONFIGS = {
    "ups":   CarrierConfig(base_rate=5.0, weight_threshold=10, weight_rate=0.5, express_multiplier=1.8),
    "fedex": CarrierConfig(base_rate=6.0, weight_threshold=5,  weight_rate=0.6, express_multiplier=2.0, international_surcharge=15),
    "dhl":   CarrierConfig(base_rate=7.0, weight_threshold=2,  weight_rate=0.7, express_multiplier=1.9, international_surcharge=20),
    "usps":  CarrierConfig(base_rate=4.0, weight_threshold=1,  weight_rate=0.4),
}


def calculate_shipping(package: dict, carrier: str) -> float:
    config = CARRIER_CONFIGS.get(carrier)
    if config is None:
        raise ValueError(f"unknown carrier: {carrier!r}")

    cost = config.base_rate

    excess_weight = package["weight"] - config.weight_threshold
    if excess_weight > 0:
        cost += excess_weight * config.weight_rate

    if package.get("international"):
        cost += config.international_surcharge

    if package.get("express") and config.express_multiplier is not None:
        cost *= config.express_multiplier

    return cost
```

#### Variant C  (`b14d`)

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CarrierConfig:
    base_rate: float
    weight_threshold: float
    weight_rate: float
    express_multiplier: Optional[float]
    international_surcharge: float = 0.0
    apply_international_before_express: bool = False


CARRIER_CONFIGS: dict[str, CarrierConfig] = {
    "ups": CarrierConfig(
        base_rate=5.0,
        weight_threshold=10.0,
        weight_rate=0.5,
        express_multiplier=1.8,
    ),
    "fedex": CarrierConfig(
        base_rate=6.0,
        weight_threshold=5.0,
        weight_rate=0.6,
        express_multiplier=2.0,
        international_surcharge=15.0,
    ),
    "dhl": CarrierConfig(
        base_rate=7.0,
        weight_threshold=2.0,
        weight_rate=0.7,
        express_multiplier=1.9,
        international_surcharge=20.0,
        apply_international_before_express=True,
    ),
    "usps": CarrierConfig(
        base_rate=4.0,
        weight_threshold=1.0,
        weight_rate=0.4,
        express_multiplier=None,
    ),
}


def calculate_shipping(package: dict, carrier: str) -> float:
    config = CARRIER_CONFIGS.get(carrier)
    if config is None:
        raise ValueError(f"unknown carrier: {carrier!r}")

    cost = config.base_rate
    weight = package["weight"]

    if weight > config.weight_threshold:
        cost += (weight - config.weight_threshold) * config.weight_rate

    def apply_international(c: float) -> float:
        if package.get("international") and config.international_surcharge:
            c += config.international_surcharge
        return c

    def apply_express(c: float) -> float:
        if package.get("express") and config.express_multiplier is not None:
            c *= config.express_multiplier
        return c

    if config.apply_international_before_express:
        cost = apply_express(apply_international(cost))
    else:
        cost = apply_international(apply_express(cost))

    return cost
```

#### Variant D  (`576d`)

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CarrierConfig:
    base_rate: float
    weight_threshold: float
    weight_rate: float
    express_multiplier: Optional[float] = None
    international_surcharge: Optional[float] = None


CARRIER_CONFIGS: dict[str, CarrierConfig] = {
    "ups": CarrierConfig(
        base_rate=5.0,
        weight_threshold=10,
        weight_rate=0.5,
        express_multiplier=1.8,
    ),
    "fedex": CarrierConfig(
        base_rate=6.0,
        weight_threshold=5,
        weight_rate=0.6,
        express_multiplier=2.0,
        international_surcharge=15.0,
    ),
    "dhl": CarrierConfig(
        base_rate=7.0,
        weight_threshold=2,
        weight_rate=0.7,
        express_multiplier=1.9,
        international_surcharge=20.0,
    ),
    "usps": CarrierConfig(
        base_rate=4.0,
        weight_threshold=1,
        weight_rate=0.4,
    ),
}


def calculate_shipping(package: dict, carrier: str) -> float:
    config = CARRIER_CONFIGS.get(carrier)
    if config is None:
        raise ValueError(f"unknown carrier: {carrier!r}")

    cost = config.base_rate

    excess_weight = package["weight"] - config.weight_threshold
    if excess_weight > 0:
        cost += excess_weight * config.weight_rate

    if config.international_surcharge and package.get("international"):
        cost += config.international_surcharge

    if config.express_multiplier and package.get("express"):
        cost *= config.express_multiplier

    return cost
```

#### Variant E  (`a23d`)

```python
CARRIER_CONFIG = {
    "ups": {
        "base": 5.0,
        "weight_threshold": 10,
        "weight_rate": 0.5,
        "express_multiplier": 1.8,
        "international_surcharge": 0,
    },
    "fedex": {
        "base": 6.0,
        "weight_threshold": 5,
        "weight_rate": 0.6,
        "express_multiplier": 2.0,
        "international_surcharge": 15,
    },
    "dhl": {
        "base": 7.0,
        "weight_threshold": 2,
        "weight_rate": 0.7,
        "express_multiplier": 1.9,
        "international_surcharge": 20,
    },
    "usps": {
        "base": 4.0,
        "weight_threshold": 1,
        "weight_rate": 0.4,
        "express_multiplier": 1.0,
        "international_surcharge": 0,
    },
}


def calculate_shipping(package, carrier):
    config = CARRIER_CONFIG.get(carrier)
    if config is None:
        raise ValueError("unknown carrier")

    weight = package["weight"]
    cost = config["base"]

    if weight > config["weight_threshold"]:
        cost += (weight - config["weight_threshold"]) * config["weight_rate"]

    if package.get("international"):
        cost += config["international_surcharge"]

    if package.get("express"):
        cost *= config["express_multiplier"]

    return cost
```

#### Variant F  (`5e3e`)

```python
CARRIER_CONFIG = {
    "ups": {
        "base": 5.0,
        "weight_threshold": 10,
        "weight_rate": 0.5,
        "express_multiplier": 1.8,
        "international_surcharge": 0,
    },
    "fedex": {
        "base": 6.0,
        "weight_threshold": 5,
        "weight_rate": 0.6,
        "express_multiplier": 2.0,
        "international_surcharge": 15,
    },
    "dhl": {
        "base": 7.0,
        "weight_threshold": 2,
        "weight_rate": 0.7,
        "express_multiplier": 1.9,
        "international_surcharge": 20,
    },
    "usps": {
        "base": 4.0,
        "weight_threshold": 1,
        "weight_rate": 0.4,
        "express_multiplier": 1.0,
        "international_surcharge": 0,
    },
}


def calculate_shipping(package, carrier):
    if carrier not in CARRIER_CONFIG:
        raise ValueError("unknown carrier")

    config = CARRIER_CONFIG[carrier]
    cost = config["base"]

    excess_weight = package["weight"] - config["weight_threshold"]
    if excess_weight > 0:
        cost += excess_weight * config["weight_rate"]

    if package.get("international"):
        cost += config["international_surcharge"]

    if package.get("express"):
        cost *= config["express_multiplier"]

    return cost
```

---

## Example 7: Primitive obsession

### Original

```python
def schedule_meeting(start_hour, start_minute, duration_minutes, participants_csv):
    if start_hour < 0 or start_hour > 23:
        raise ValueError("bad hour")
    if start_minute < 0 or start_minute > 59:
        raise ValueError("bad minute")
    end_total = start_hour * 60 + start_minute + duration_minutes
    end_hour = (end_total // 60) % 24
    end_minute = end_total % 60
    parts = [p.strip() for p in participants_csv.split(",") if p.strip()]
    for p in parts:
        if "@" not in p:
            raise ValueError("bad email: " + p)
    return {
        "start": f"{start_hour:02d}:{start_minute:02d}",
        "end": f"{end_hour:02d}:{end_minute:02d}",
        "participants": parts,
    }

def overlaps(meeting_a_start_hour, meeting_a_start_min, meeting_a_duration,
             meeting_b_start_hour, meeting_b_start_min, meeting_b_duration):
    a_start = meeting_a_start_hour * 60 + meeting_a_start_min
    a_end = a_start + meeting_a_duration
    b_start = meeting_b_start_hour * 60 + meeting_b_start_min
    b_end = b_start + meeting_b_duration
    return a_start < b_end and b_start < a_end
```

### Variants

#### Variant A  (`19b5`)

```python
from dataclasses import dataclass


@dataclass
class TimeSlot:
    start_minutes: int
    duration_minutes: int

    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.duration_minutes

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes


def _validate_time(hour: int, minute: int) -> None:
    if not (0 <= hour <= 23):
        raise ValueError(f"Invalid hour: {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"Invalid minute: {minute}")


def _validate_participants(participants: list[str]) -> None:
    for participant in participants:
        if "@" not in participant:
            raise ValueError(f"Invalid email: {participant}")


def _format_time(total_minutes: int) -> str:
    hour = (total_minutes // 60) % 24
    minute = total_minutes % 60
    return f"{hour:02d}:{minute:02d}"


def schedule_meeting(
    start_hour: int,
    start_minute: int,
    duration_minutes: int,
    participants_csv: str,
) -> dict:
    _validate_time(start_hour, start_minute)

    participants = [p.strip() for p in participants_csv.split(",") if p.strip()]
    _validate_participants(participants)

    start_total = start_hour * 60 + start_minute
    slot = TimeSlot(start_minutes=start_total, duration_minutes=duration_minutes)

    return {
        "start": _format_time(slot.start_minutes),
        "end": _format_time(slot.end_minutes),
        "participants": participants,
    }


def overlaps(
    meeting_a_start_hour: int,
    meeting_a_start_min: int,
    meeting_a_duration: int,
    meeting_b_start_hour: int,
    meeting_b_start_min: int,
    meeting_b_duration: int,
) -> bool:
    slot_a = TimeSlot(
        start_minutes=meeting_a_start_hour * 60 + meeting_a_start_min,
        duration_minutes=meeting_a_duration,
    )
    slot_b = TimeSlot(
        start_minutes=meeting_b_start_hour * 60 + meeting_b_start_min,
        duration_minutes=meeting_b_duration,
    )
    return slot_a.overlaps(slot_b)
```

#### Variant B  (`73fe`)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TimeRange:
    start_minutes: int
    duration_minutes: int

    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.duration_minutes

    def overlaps(self, other: "TimeRange") -> bool:
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes


def _validate_time(hour: int, minute: int) -> None:
    if not (0 <= hour <= 23):
        raise ValueError(f"Invalid hour: {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"Invalid minute: {minute}")


def _parse_participants(participants_csv: str) -> list[str]:
    participants = [p.strip() for p in participants_csv.split(",") if p.strip()]
    invalid = [p for p in participants if "@" not in p]
    if invalid:
        raise ValueError(f"Invalid email(s): {', '.join(invalid)}")
    return participants


def _format_time(total_minutes: int) -> str:
    hour = (total_minutes // 60) % 24
    minute = total_minutes % 60
    return f"{hour:02d}:{minute:02d}"


def schedule_meeting(
    start_hour: int,
    start_minute: int,
    duration_minutes: int,
    participants_csv: str,
) -> dict:
    _validate_time(start_hour, start_minute)
    participants = _parse_participants(participants_csv)
    start_total = start_hour * 60 + start_minute
    time_range = TimeRange(start_total, duration_minutes)
    return {
        "start": _format_time(time_range.start_minutes),
        "end": _format_time(time_range.end_minutes),
        "participants": participants,
    }


def overlaps(
    meeting_a_start_hour: int,
    meeting_a_start_min: int,
    meeting_a_duration: int,
    meeting_b_start_hour: int,
    meeting_b_start_min: int,
    meeting_b_duration: int,
) -> bool:
    range_a = TimeRange(meeting_a_start_hour * 60 + meeting_a_start_min, meeting_a_duration)
    range_b = TimeRange(meeting_b_start_hour * 60 + meeting_b_start_min, meeting_b_duration)
    return range_a.overlaps(range_b)
```

#### Variant C  (`75ce`)

```python
from dataclasses import dataclass, field


@dataclass
class TimeSlot:
    start_minutes: int
    duration_minutes: int

    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.duration_minutes

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes

    def _format_time(self, total_minutes: int) -> str:
        hour = (total_minutes // 60) % 24
        minute = total_minutes % 60
        return f"{hour:02d}:{minute:02d}"

    @property
    def start_str(self) -> str:
        return self._format_time(self.start_minutes)

    @property
    def end_str(self) -> str:
        return self._format_time(self.end_minutes)


@dataclass
class Meeting:
    slot: TimeSlot
    participants: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, start_hour: int, start_minute: int, duration_minutes: int, participants_csv: str) -> "Meeting":
        if not (0 <= start_hour <= 23):
            raise ValueError(f"Invalid hour: {start_hour}")
        if not (0 <= start_minute <= 59):
            raise ValueError(f"Invalid minute: {start_minute}")

        participants = [p.strip() for p in participants_csv.split(",") if p.strip()]
        invalid = [p for p in participants if "@" not in p]
        if invalid:
            raise ValueError(f"Invalid email(s): {', '.join(invalid)}")

        slot = TimeSlot(
            start_minutes=start_hour * 60 + start_minute,
            duration_minutes=duration_minutes,
        )
        return cls(slot=slot, participants=participants)

    def to_dict(self) -> dict:
        return {
            "start": self.slot.start_str,
            "end": self.slot.end_str,
            "participants": self.participants,
        }

    def overlaps(self, other: "Meeting") -> bool:
        return self.slot.overlaps(other.slot)


def schedule_meeting(start_hour: int, start_minute: int, duration_minutes: int, participants_csv: str) -> dict:
    return Meeting.create(start_hour, start_minute, duration_minutes, participants_csv).to_dict()


def overlaps(
    meeting_a_start_hour: int, meeting_a_start_min: int, meeting_a_duration: int,
    meeting_b_start_hour: int, meeting_b_start_min: int, meeting_b_duration: int,
) -> bool:
    slot_a = TimeSlot(meeting_a_start_hour * 60 + meeting_a_start_min, meeting_a_duration)
    slot_b = TimeSlot(meeting_b_start_hour * 60 + meeting_b_start_min, meeting_b_duration)
    return slot_a.overlaps(slot_b)
```

#### Variant D  (`1fe0`)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TimeSlot:
    start_minutes: int
    duration_minutes: int

    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.duration_minutes

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes

    @classmethod
    def from_hm(cls, hour: int, minute: int, duration_minutes: int) -> "TimeSlot":
        if not (0 <= hour <= 23):
            raise ValueError(f"Hour must be 0-23, got {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"Minute must be 0-59, got {minute}")
        return cls(start_minutes=hour * 60 + minute, duration_minutes=duration_minutes)

    def start_label(self) -> str:
        return f"{self.start_minutes // 60 % 24:02d}:{self.start_minutes % 60:02d}"

    def end_label(self) -> str:
        end = self.end_minutes
        return f"{end // 60 % 24:02d}:{end % 60:02d}"


def _parse_participants(participants_csv: str) -> list[str]:
    parts = [p.strip() for p in participants_csv.split(",") if p.strip()]
    invalid = [p for p in parts if "@" not in p]
    if invalid:
        raise ValueError(f"Invalid email address(es): {', '.join(invalid)}")
    return parts


def schedule_meeting(
    start_hour: int,
    start_minute: int,
    duration_minutes: int,
    participants_csv: str,
) -> dict:
    slot = TimeSlot.from_hm(start_hour, start_minute, duration_minutes)
    participants = _parse_participants(participants_csv)
    return {
        "start": slot.start_label(),
        "end": slot.end_label(),
        "participants": participants,
    }


def overlaps(
    meeting_a_start_hour: int,
    meeting_a_start_min: int,
    meeting_a_duration: int,
    meeting_b_start_hour: int,
    meeting_b_start_min: int,
    meeting_b_duration: int,
) -> bool:
    slot_a = TimeSlot.from_hm(meeting_a_start_hour, meeting_a_start_min, meeting_a_duration)
    slot_b = TimeSlot.from_hm(meeting_b_start_hour, meeting_b_start_min, meeting_b_duration)
    return slot_a.overlaps(slot_b)
```

#### Variant E  (`72dc`)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TimeSlot:
    start_minutes: int
    duration_minutes: int

    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.duration_minutes

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes


def _validate_time(hour: int, minute: int) -> None:
    if not 0 <= hour <= 23:
        raise ValueError(f"Invalid hour: {hour}")
    if not 0 <= minute <= 59:
        raise ValueError(f"Invalid minute: {minute}")


def _validate_participants(participants: list[str]) -> None:
    for participant in participants:
        if "@" not in participant:
            raise ValueError(f"Invalid email: {participant}")


def _minutes_to_time_str(total_minutes: int) -> str:
    hour = (total_minutes // 60) % 24
    minute = total_minutes % 60
    return f"{hour:02d}:{minute:02d}"


def schedule_meeting(
    start_hour: int,
    start_minute: int,
    duration_minutes: int,
    participants_csv: str,
) -> dict:
    _validate_time(start_hour, start_minute)

    participants = [p.strip() for p in participants_csv.split(",") if p.strip()]
    _validate_participants(participants)

    start_total = start_hour * 60 + start_minute
    slot = TimeSlot(start_minutes=start_total, duration_minutes=duration_minutes)

    return {
        "start": _minutes_to_time_str(slot.start_minutes),
        "end": _minutes_to_time_str(slot.end_minutes),
        "participants": participants,
    }


def overlaps(
    meeting_a_start_hour: int,
    meeting_a_start_min: int,
    meeting_a_duration: int,
    meeting_b_start_hour: int,
    meeting_b_start_min: int,
    meeting_b_duration: int,
) -> bool:
    slot_a = TimeSlot(
        start_minutes=meeting_a_start_hour * 60 + meeting_a_start_min,
        duration_minutes=meeting_a_duration,
    )
    slot_b = TimeSlot(
        start_minutes=meeting_b_start_hour * 60 + meeting_b_start_min,
        duration_minutes=meeting_b_duration,
    )
    return slot_a.overlaps(slot_b)
```

#### Variant F  (`84c6`)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TimeSlot:
    start_minutes: int
    duration_minutes: int

    @property
    def end_minutes(self) -> int:
        return self.start_minutes + self.duration_minutes

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes

    @classmethod
    def from_hm(cls, hour: int, minute: int, duration_minutes: int) -> "TimeSlot":
        if not (0 <= hour <= 23):
            raise ValueError(f"Hour must be 0-23, got {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"Minute must be 0-59, got {minute}")
        return cls(start_minutes=hour * 60 + minute, duration_minutes=duration_minutes)

    def _as_hhmm(self, total_minutes: int) -> str:
        h = (total_minutes // 60) % 24
        m = total_minutes % 60
        return f"{h:02d}:{m:02d}"

    @property
    def start_hhmm(self) -> str:
        return self._as_hhmm(self.start_minutes)

    @property
    def end_hhmm(self) -> str:
        return self._as_hhmm(self.end_minutes)


def _parse_participants(participants_csv: str) -> list[str]:
    parts = [p.strip() for p in participants_csv.split(",") if p.strip()]
    invalid = [p for p in parts if "@" not in p]
    if invalid:
        raise ValueError(f"Invalid email address(es): {', '.join(invalid)}")
    return parts


def schedule_meeting(
    start_hour: int,
    start_minute: int,
    duration_minutes: int,
    participants_csv: str,
) -> dict:
    slot = TimeSlot.from_hm(start_hour, start_minute, duration_minutes)
    participants = _parse_participants(participants_csv)
    return {
        "start": slot.start_hhmm,
        "end": slot.end_hhmm,
        "participants": participants,
    }


def overlaps(
    meeting_a_start_hour: int,
    meeting_a_start_min: int,
    meeting_a_duration: int,
    meeting_b_start_hour: int,
    meeting_b_start_min: int,
    meeting_b_duration: int,
) -> bool:
    slot_a = TimeSlot.from_hm(meeting_a_start_hour, meeting_a_start_min, meeting_a_duration)
    slot_b = TimeSlot.from_hm(meeting_b_start_hour, meeting_b_start_min, meeting_b_duration)
    return slot_a.overlaps(slot_b)
```

---

## Example 8: Magic numbers and strings

### Original

```python
def classify_bmi(weight_kg, height_m):
    bmi = weight_kg / (height_m * height_m)
    if bmi < 18.5:
        return "U"
    elif bmi < 25:
        return "N"
    elif bmi < 30:
        return "O"
    else:
        return "OB"

def recommend(status, age):
    if status == "U":
        if age < 18:
            return "see pediatrician"
        return "gain weight"
    elif status == "N":
        return "maintain"
    elif status == "O":
        if age > 60:
            return "light exercise"
        return "exercise more"
    elif status == "OB":
        return "consult doctor"
```

### Variants

#### Variant A  (`2081`)

```python
from dataclasses import dataclass
from enum import Enum


class BMICategory(Enum):
    UNDERWEIGHT = "U"
    NORMAL = "N"
    OVERWEIGHT = "O"
    OBESE = "OB"


@dataclass(frozen=True)
class BMIThreshold:
    underweight: float = 18.5
    normal: float = 25.0
    overweight: float = 30.0


_THRESHOLDS = BMIThreshold()


def classify_bmi(weight_kg: float, height_m: float) -> BMICategory:
    bmi = weight_kg / (height_m ** 2)
    if bmi < _THRESHOLDS.underweight:
        return BMICategory.UNDERWEIGHT
    if bmi < _THRESHOLDS.normal:
        return BMICategory.NORMAL
    if bmi < _THRESHOLDS.overweight:
        return BMICategory.OVERWEIGHT
    return BMICategory.OBESE


def recommend(status: BMICategory, age: int) -> str:
    if status == BMICategory.UNDERWEIGHT:
        return "see pediatrician" if age < 18 else "gain weight"
    if status == BMICategory.NORMAL:
        return "maintain"
    if status == BMICategory.OVERWEIGHT:
        return "light exercise" if age > 60 else "exercise more"
    if status == BMICategory.OBESE:
        return "consult doctor"
    raise ValueError(f"Unknown BMI category: {status}")
```

#### Variant B  (`9f04`)

```python
from enum import Enum


class BMICategory(Enum):
    UNDERWEIGHT = "U"
    NORMAL = "N"
    OVERWEIGHT = "O"
    OBESE = "OB"


def classify_bmi(weight_kg: float, height_m: float) -> BMICategory:
    bmi = weight_kg / height_m ** 2
    if bmi < 18.5:
        return BMICategory.UNDERWEIGHT
    if bmi < 25.0:
        return BMICategory.NORMAL
    if bmi < 30.0:
        return BMICategory.OVERWEIGHT
    return BMICategory.OBESE


def recommend(status: BMICategory, age: int) -> str:
    if status is BMICategory.UNDERWEIGHT:
        return "see pediatrician" if age < 18 else "gain weight"
    if status is BMICategory.NORMAL:
        return "maintain"
    if status is BMICategory.OVERWEIGHT:
        return "light exercise" if age > 60 else "exercise more"
    if status is BMICategory.OBESE:
        return "consult doctor"
    raise ValueError(f"Unknown BMI category: {status}")
```

#### Variant C  (`80c2`)

```python
from enum import Enum


class BMICategory(Enum):
    UNDERWEIGHT = "underweight"
    NORMAL = "normal"
    OVERWEIGHT = "overweight"
    OBESE = "obese"


_BMI_THRESHOLDS = [
    (18.5, BMICategory.UNDERWEIGHT),
    (25.0, BMICategory.NORMAL),
    (30.0, BMICategory.OVERWEIGHT),
]


def classify_bmi(weight_kg: float, height_m: float) -> BMICategory:
    bmi = weight_kg / height_m ** 2
    for threshold, category in _BMI_THRESHOLDS:
        if bmi < threshold:
            return category
    return BMICategory.OBESE


def recommend(category: BMICategory, age: int) -> str:
    if category is BMICategory.UNDERWEIGHT:
        return "see pediatrician" if age < 18 else "gain weight"
    if category is BMICategory.NORMAL:
        return "maintain"
    if category is BMICategory.OVERWEIGHT:
        return "light exercise" if age > 60 else "exercise more"
    if category is BMICategory.OBESE:
        return "consult doctor"
    raise ValueError(f"Unknown category: {category}")
```

#### Variant D  (`5af4`)

```python
from enum import Enum


class BMICategory(Enum):
    UNDERWEIGHT = "underweight"
    NORMAL = "normal"
    OVERWEIGHT = "overweight"
    OBESE = "obese"


_BMI_THRESHOLDS = [
    (18.5, BMICategory.UNDERWEIGHT),
    (25.0, BMICategory.NORMAL),
    (30.0, BMICategory.OVERWEIGHT),
]


def classify_bmi(weight_kg: float, height_m: float) -> BMICategory:
    bmi = weight_kg / (height_m ** 2)
    for upper, category in _BMI_THRESHOLDS:
        if bmi < upper:
            return category
    return BMICategory.OBESE


def recommend(category: BMICategory, age: int) -> str:
    if category == BMICategory.UNDERWEIGHT:
        return "see pediatrician" if age < 18 else "gain weight"
    if category == BMICategory.NORMAL:
        return "maintain"
    if category == BMICategory.OVERWEIGHT:
        return "light exercise" if age > 60 else "exercise more"
    if category == BMICategory.OBESE:
        return "consult doctor"
    raise ValueError(f"Unknown BMI category: {category}")
```

#### Variant E  (`fb9b`)

```python
from dataclasses import dataclass
from enum import Enum


class BmiCategory(Enum):
    UNDERWEIGHT = "U"
    NORMAL = "N"
    OVERWEIGHT = "O"
    OBESE = "OB"


@dataclass(frozen=True)
class BmiThreshold:
    upper: float
    category: BmiCategory


BMI_THRESHOLDS = [
    BmiThreshold(18.5, BmiCategory.UNDERWEIGHT),
    BmiThreshold(25.0, BmiCategory.NORMAL),
    BmiThreshold(30.0, BmiCategory.OVERWEIGHT),
]

RECOMMENDATIONS = {
    BmiCategory.NORMAL: "maintain",
    BmiCategory.OBESE: "consult doctor",
}


def classify_bmi(weight_kg: float, height_m: float) -> BmiCategory:
    bmi = weight_kg / height_m ** 2
    for threshold in BMI_THRESHOLDS:
        if bmi < threshold.upper:
            return threshold.category
    return BmiCategory.OBESE


def recommend(status: BmiCategory, age: int) -> str:
    if status in RECOMMENDATIONS:
        return RECOMMENDATIONS[status]

    if status == BmiCategory.UNDERWEIGHT:
        return "see pediatrician" if age < 18 else "gain weight"

    if status == BmiCategory.OVERWEIGHT:
        return "light exercise" if age > 60 else "exercise more"

    raise ValueError(f"Unhandled BMI category: {status}")
```

#### Variant F  (`cc1d`)

```python
from enum import Enum


class BMICategory(Enum):
    UNDERWEIGHT = "underweight"
    NORMAL = "normal"
    OVERWEIGHT = "overweight"
    OBESE = "obese"


_BMI_THRESHOLDS = [
    (18.5, BMICategory.UNDERWEIGHT),
    (25.0, BMICategory.NORMAL),
    (30.0, BMICategory.OVERWEIGHT),
]


def classify_bmi(weight_kg: float, height_m: float) -> BMICategory:
    bmi = weight_kg / height_m ** 2
    for threshold, category in _BMI_THRESHOLDS:
        if bmi < threshold:
            return category
    return BMICategory.OBESE


def recommend(category: BMICategory, age: int) -> str:
    if category is BMICategory.UNDERWEIGHT:
        return "see pediatrician" if age < 18 else "gain weight"
    if category is BMICategory.NORMAL:
        return "maintain"
    if category is BMICategory.OVERWEIGHT:
        return "light exercise" if age > 60 else "exercise more"
    if category is BMICategory.OBESE:
        return "consult doctor"
    raise ValueError(f"Unknown BMI category: {category}")
```

---

## Example 9: State flags instead of state machine

### Original

```python
class Document:
    def __init__(self, text):
        self.text = text
        self.is_draft = True
        self.is_reviewed = False
        self.is_approved = False
        self.is_published = False
        self.is_archived = False

    def submit_for_review(self):
        if not self.is_draft:
            raise RuntimeError("cannot submit")
        self.is_draft = False
        self.is_reviewed = False

    def review(self, approved):
        if self.is_draft or self.is_approved or self.is_published or self.is_archived:
            raise RuntimeError("cannot review")
        self.is_reviewed = True
        if approved:
            self.is_approved = True

    def publish(self):
        if not self.is_approved or self.is_published or self.is_archived:
            raise RuntimeError("cannot publish")
        self.is_published = True

    def archive(self):
        if self.is_archived:
            raise RuntimeError("already archived")
        self.is_archived = True

    def status(self):
        if self.is_archived:
            return "archived"
        if self.is_published:
            return "published"
        if self.is_approved:
            return "approved"
        if self.is_reviewed:
            return "reviewed"
        if self.is_draft:
            return "draft"
        return "submitted"
```

### Variants

#### Variant A  (`bdac`)

```python
from enum import Enum, auto


class Status(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


class Document:
    def __init__(self, text):
        self.text = text
        self._status = Status.DRAFT

    def submit_for_review(self):
        if self._status != Status.DRAFT:
            raise RuntimeError("cannot submit")
        self._status = Status.SUBMITTED

    def review(self, approved):
        if self._status != Status.SUBMITTED:
            raise RuntimeError("cannot review")
        self._status = Status.APPROVED if approved else Status.REVIEWED

    def publish(self):
        if self._status != Status.APPROVED:
            raise RuntimeError("cannot publish")
        self._status = Status.PUBLISHED

    def archive(self):
        if self._status == Status.ARCHIVED:
            raise RuntimeError("already archived")
        self._status = Status.ARCHIVED

    def status(self):
        return self._status.name.lower()
```

#### Variant B  (`7f13`)

```python
from enum import Enum, auto


class State(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


_TRANSITIONS = {
    "submit_for_review": {State.DRAFT},
    "review": {State.SUBMITTED},
    "approve": {State.REVIEWED},
    "publish": {State.APPROVED},
    "archive": set(State) - {State.ARCHIVED},
}


class Document:
    def __init__(self, text):
        self.text = text
        self._state = State.DRAFT

    def _require_state(self, *allowed):
        if self._state not in allowed:
            raise RuntimeError(
                f"cannot perform action in state {self._state.name.lower()}"
            )

    def submit_for_review(self):
        self._require_state(State.DRAFT)
        self._state = State.SUBMITTED

    def review(self, approved):
        self._require_state(State.SUBMITTED)
        self._state = State.APPROVED if approved else State.REVIEWED

    def publish(self):
        self._require_state(State.APPROVED)
        self._state = State.PUBLISHED

    def archive(self):
        self._require_state(*(_TRANSITIONS["archive"]))
        self._state = State.ARCHIVED

    def status(self):
        return self._state.name.lower()
```

#### Variant C  (`8c74`)

```python
from enum import Enum, auto


class DocumentState(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


_VALID_TRANSITIONS = {
    DocumentState.DRAFT: {DocumentState.SUBMITTED},
    DocumentState.SUBMITTED: {DocumentState.REVIEWED},
    DocumentState.REVIEWED: {DocumentState.APPROVED, DocumentState.SUBMITTED},
    DocumentState.APPROVED: {DocumentState.PUBLISHED},
    DocumentState.PUBLISHED: {DocumentState.ARCHIVED},
    DocumentState.ARCHIVED: set(),
}


class Document:
    def __init__(self, text: str) -> None:
        self.text = text
        self._state = DocumentState.DRAFT

    @property
    def state(self) -> DocumentState:
        return self._state

    def _transition(self, target: DocumentState, error_msg: str) -> None:
        if target not in _VALID_TRANSITIONS.get(self._state, set()):
            raise RuntimeError(error_msg)
        self._state = target

    def submit_for_review(self) -> None:
        self._transition(DocumentState.SUBMITTED, "cannot submit")

    def review(self, approved: bool) -> None:
        if self._state != DocumentState.SUBMITTED:
            raise RuntimeError("cannot review")
        self._state = DocumentState.APPROVED if approved else DocumentState.REVIEWED

    def publish(self) -> None:
        self._transition(DocumentState.PUBLISHED, "cannot publish")

    def archive(self) -> None:
        if self._state == DocumentState.ARCHIVED:
            raise RuntimeError("already archived")
        self._state = DocumentState.ARCHIVED

    def status(self) -> str:
        return self._state.name.lower()
```

#### Variant D  (`dd98`)

```python
from enum import Enum, auto


class State(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


class Document:
    def __init__(self, text):
        self.text = text
        self._state = State.DRAFT

    def _require(self, condition, message="invalid transition"):
        if not condition:
            raise RuntimeError(message)

    def submit_for_review(self):
        self._require(self._state == State.DRAFT, "cannot submit")
        self._state = State.SUBMITTED

    def review(self, approved):
        self._require(self._state == State.SUBMITTED, "cannot review")
        self._state = State.APPROVED if approved else State.REVIEWED

    def publish(self):
        self._require(self._state == State.APPROVED, "cannot publish")
        self._state = State.PUBLISHED

    def archive(self):
        self._require(self._state != State.ARCHIVED, "already archived")
        self._state = State.ARCHIVED

    def status(self):
        return self._state.name.lower()
```

#### Variant E  (`f2ae`)

```python
from enum import Enum, auto


class DocumentState(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


class Document:
    def __init__(self, text):
        self.text = text
        self._state = DocumentState.DRAFT

    @property
    def state(self):
        return self._state

    def status(self):
        return self._state.name.lower()

    def submit_for_review(self):
        if self._state is not DocumentState.DRAFT:
            raise RuntimeError("cannot submit")
        self._state = DocumentState.SUBMITTED

    def review(self, approved):
        if self._state is not DocumentState.SUBMITTED:
            raise RuntimeError("cannot review")
        self._state = DocumentState.APPROVED if approved else DocumentState.REVIEWED

    def publish(self):
        if self._state is not DocumentState.APPROVED:
            raise RuntimeError("cannot publish")
        self._state = DocumentState.PUBLISHED

    def archive(self):
        if self._state is DocumentState.ARCHIVED:
            raise RuntimeError("already archived")
        self._state = DocumentState.ARCHIVED
```

#### Variant F  (`6298`)

```python
from enum import Enum, auto


class DocumentState(Enum):
    DRAFT = auto()
    SUBMITTED = auto()
    REVIEWED = auto()
    APPROVED = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()


class Document:
    _VALID_TRANSITIONS = {
        DocumentState.DRAFT: {DocumentState.SUBMITTED},
        DocumentState.SUBMITTED: {DocumentState.REVIEWED},
        DocumentState.REVIEWED: {DocumentState.APPROVED, DocumentState.ARCHIVED},
        DocumentState.APPROVED: {DocumentState.PUBLISHED, DocumentState.ARCHIVED},
        DocumentState.PUBLISHED: {DocumentState.ARCHIVED},
        DocumentState.ARCHIVED: set(),
    }

    def __init__(self, text: str) -> None:
        self.text = text
        self._state = DocumentState.DRAFT

    def _transition(self, target: DocumentState) -> None:
        if target not in self._VALID_TRANSITIONS[self._state]:
            raise RuntimeError(
                f"cannot transition from {self._state.name} to {target.name}"
            )
        self._state = target

    def submit_for_review(self) -> None:
        self._transition(DocumentState.SUBMITTED)

    def review(self, approved: bool) -> None:
        if self._state != DocumentState.SUBMITTED:
            raise RuntimeError(
                f"cannot review a document in state {self._state.name}"
            )
        self._state = DocumentState.APPROVED if approved else DocumentState.REVIEWED

    def publish(self) -> None:
        self._transition(DocumentState.PUBLISHED)

    def archive(self) -> None:
        self._transition(DocumentState.ARCHIVED)

    def status(self) -> str:
        return self._state.name.lower()
```

---

## Example 10: Global state and side effects

### Original

```python
CACHE = {}
LOG = []
CONFIG = {"retries": 3, "timeout": 5}

def fetch(url):
    if url in CACHE:
        LOG.append("hit " + url)
        return CACHE[url]
    LOG.append("miss " + url)
    attempts = 0
    while attempts < CONFIG["retries"]:
        try:
            # pretend this is a real HTTP call
            data = "DATA:" + url
            CACHE[url] = data
            LOG.append("ok " + url)
            return data
        except Exception:
            attempts += 1
            LOG.append("retry " + url)
    LOG.append("fail " + url)
    return None

def clear_cache():
    global CACHE
    CACHE = {}
    LOG.append("cache cleared")

def set_retries(n):
    CONFIG["retries"] = n
    LOG.append("retries=" + str(n))
```

### Variants

#### Variant A  (`b260`)

```python
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FetcherConfig:
    retries: int = 3
    timeout: int = 5


class Fetcher:
    def __init__(self, config: FetcherConfig | None = None):
        self.config = config or FetcherConfig()
        self._cache: dict[str, str] = {}

    def fetch(self, url: str) -> str | None:
        if url in self._cache:
            logger.debug("cache hit: %s", url)
            return self._cache[url]

        logger.debug("cache miss: %s", url)
        for attempt in range(self.config.retries):
            try:
                data = "DATA:" + url
                self._cache[url] = data
                logger.debug("ok: %s", url)
                return data
            except Exception:
                logger.warning("retry %d: %s", attempt + 1, url)

        logger.error("failed: %s", url)
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.debug("cache cleared")

    @property
    def retries(self) -> int:
        return self.config.retries

    @retries.setter
    def retries(self, n: int) -> None:
        self.config.retries = n
        logger.debug("retries set to %d", n)
```

#### Variant B  (`192d`)

```python
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FetcherConfig:
    retries: int = 3
    timeout: int = 5


class Fetcher:
    def __init__(self, config: FetcherConfig | None = None):
        self.config = config or FetcherConfig()
        self._cache: dict[str, str] = {}

    def fetch(self, url: str) -> str | None:
        if url in self._cache:
            logger.debug("cache hit: %s", url)
            return self._cache[url]

        logger.debug("cache miss: %s", url)
        for attempt in range(self.config.retries):
            try:
                data = "DATA:" + url
                self._cache[url] = data
                logger.info("ok: %s", url)
                return data
            except Exception:
                logger.warning("retry %d: %s", attempt + 1, url)

        logger.error("failed: %s", url)
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.debug("cache cleared")

    def set_retries(self, n: int) -> None:
        self.config.retries = n
        logger.debug("retries set to %d", n)
```

#### Variant C  (`a7f2`)

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class FetcherConfig:
    retries: int = 3
    timeout: int = 5


class Fetcher:
    def __init__(self, config: Optional[FetcherConfig] = None):
        self.config = config or FetcherConfig()
        self._cache: dict[str, str] = {}
        self._log: list[str] = []

    @property
    def log(self) -> list[str]:
        return self._log

    def fetch(self, url: str) -> Optional[str]:
        if url in self._cache:
            self._log.append(f"hit {url}")
            return self._cache[url]

        self._log.append(f"miss {url}")

        for _ in range(self.config.retries):
            try:
                data = f"DATA:{url}"
                self._cache[url] = data
                self._log.append(f"ok {url}")
                return data
            except Exception:
                self._log.append(f"retry {url}")

        self._log.append(f"fail {url}")
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
        self._log.append("cache cleared")

    def set_retries(self, n: int) -> None:
        self.config.retries = n
        self._log.append(f"retries={n}")
```

#### Variant D  (`6dff`)

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FetcherConfig:
    retries: int = 3
    timeout: int = 5


class Fetcher:
    def __init__(self, config: Optional[FetcherConfig] = None) -> None:
        self._config = config or FetcherConfig()
        self._cache: dict[str, str] = {}
        self._log: list[str] = []

    @property
    def log(self) -> list[str]:
        return self._log

    @property
    def config(self) -> FetcherConfig:
        return self._config

    def fetch(self, url: str) -> Optional[str]:
        if url in self._cache:
            self._log.append("hit " + url)
            return self._cache[url]

        self._log.append("miss " + url)

        for attempt in range(self._config.retries):
            try:
                data = "DATA:" + url
                self._cache[url] = data
                self._log.append("ok " + url)
                return data
            except Exception:
                self._log.append("retry " + url)

        self._log.append("fail " + url)
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
        self._log.append("cache cleared")

    def set_retries(self, n: int) -> None:
        self._config.retries = n
        self._log.append("retries=" + str(n))
```

#### Variant E  (`1f8f`)

```python
import logging

logger = logging.getLogger(__name__)


class FetchClient:
    DEFAULT_RETRIES = 3
    DEFAULT_TIMEOUT = 5

    def __init__(self, retries=DEFAULT_RETRIES, timeout=DEFAULT_TIMEOUT):
        self._cache: dict[str, str] = {}
        self._retries = retries
        self._timeout = timeout

    @property
    def retries(self) -> int:
        return self._retries

    @retries.setter
    def retries(self, value: int) -> None:
        self._retries = value
        logger.debug("retries=%d", value)

    def fetch(self, url: str) -> str | None:
        if url in self._cache:
            logger.debug("hit %s", url)
            return self._cache[url]

        logger.debug("miss %s", url)
        for attempt in range(self._retries):
            try:
                data = "DATA:" + url
                self._cache[url] = data
                logger.debug("ok %s", url)
                return data
            except Exception:
                logger.debug("retry %s (attempt %d)", url, attempt + 1)

        logger.debug("fail %s", url)
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.debug("cache cleared")
```

#### Variant F  (`0e58`)

```python
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FetcherConfig:
    retries: int = 3
    timeout: int = 5


class Fetcher:
    def __init__(self, config: Optional[FetcherConfig] = None):
        self._config = config or FetcherConfig()
        self._cache: dict[str, str] = {}

    @property
    def config(self) -> FetcherConfig:
        return self._config

    def fetch(self, url: str) -> Optional[str]:
        if url in self._cache:
            logger.debug("hit %s", url)
            return self._cache[url]

        logger.debug("miss %s", url)
        for attempt in range(self._config.retries):
            try:
                data = "DATA:" + url
                self._cache[url] = data
                logger.debug("ok %s", url)
                return data
            except Exception:
                logger.debug("retry %s (attempt %d)", url, attempt + 1)

        logger.debug("fail %s", url)
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.debug("cache cleared")

    def set_retries(self, n: int) -> None:
        self._config.retries = n
        logger.debug("retries=%d", n)
```

---
