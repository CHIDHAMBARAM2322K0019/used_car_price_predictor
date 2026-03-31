import sqlite3

conn = sqlite3.connect("users.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS predictions")

cur.execute("""
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    year INTEGER,
    km_driven INTEGER,
    fuel INTEGER,
    brand TEXT,
    predicted_price INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ predictions table recreated successfully")