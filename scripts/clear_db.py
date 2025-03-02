# scripts/clear_db.py
import sqlite3

conn = sqlite3.connect('data/abm_tool.db')
c = conn.cursor()

# Delete all rows from relevant tables
c.execute("DELETE FROM intent_signals")
c.execute("DELETE FROM ecom_signals")
c.execute("DELETE FROM companies")  # Optional: clears companies too

conn.commit()
conn.close()

print("Database cleared successfully.")