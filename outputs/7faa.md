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
