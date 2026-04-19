# Example 2: Class with too many responsibilities

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
