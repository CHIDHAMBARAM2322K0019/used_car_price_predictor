import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("users.db")
cur = conn.cursor()

username = "admin"
password = generate_password_hash("1234")  # password nee change pannalaam
role = "admin"

try:
    cur.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, password, role)
    )
    conn.commit()
    print("✅ Admin user successfully added")
except sqlite3.IntegrityError:
    print("⚠️ Admin already exists")

conn.close()