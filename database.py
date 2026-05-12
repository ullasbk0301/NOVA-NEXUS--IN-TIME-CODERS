import sqlite3
import json

conn = sqlite3.connect("orders.db", check_same_thread=False)
c = conn.cursor()

# =============================
# USERS
# =============================
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
""")

# =============================
# ORDERS
# =============================
c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    items TEXT,
    deadline TEXT,
    status TEXT,
    quality_logs TEXT
)
""")

conn.commit()

# =============================
# USERS
# =============================
def add_user(username, password, role):
    c.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, (username, password, role))
    conn.commit()

def get_user(username):
    c.execute("""
        SELECT username, password, role
        FROM users
        WHERE username=?
    """, (username,))
    return c.fetchone()

# =============================
# ORDERS
# =============================
def add_order(username, items, deadline, status):
    c.execute("""
        INSERT INTO orders (username, items, deadline, status, quality_logs)
        VALUES (?, ?, ?, ?, ?)
    """, (
        username,
        json.dumps(items),
        deadline,
        status,
        json.dumps([])
    ))
    conn.commit()

def get_orders(username):
    c.execute("SELECT * FROM orders WHERE username=?", (username,))
    return c.fetchall()

def get_all_orders():
    c.execute("SELECT * FROM orders ORDER BY id DESC")
    return c.fetchall()

def update_order_status(order_id, status):
    c.execute("""
        UPDATE orders SET status=? WHERE id=?
    """, (status, order_id))
    conn.commit()

def delete_order(order_id):
    c.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()