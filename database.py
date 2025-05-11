# -------database.py -------- #
import sqlite3
from typing import Dict, Optional

def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (order_id TEXT PRIMARY KEY, 
                  status TEXT, 
                  customer_email TEXT,
                  items TEXT)''')
    # Insert more realistic sample data
    c.execute('''INSERT OR IGNORE INTO orders VALUES
                 ('123456', 'Shipped', 'user@example.com', 'Item1,Item2'),
                 ('123457', 'Processing', 'user2@example.com', 'Item3'),
                 ('123458', 'Returned', 'return@example.com', 'Item4')''')
    conn.commit()
    conn.close()

def get_order(order_id: str):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE order_id=?", (order_id,))
    result = c.fetchone()
    conn.close()
    return dict(zip(['order_id', 'status', 'email', 'items'], result)) if result else None