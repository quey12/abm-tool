import sqlite3

conn = sqlite3.connect('data/abm_tool.db')
c = conn.cursor()

# List all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("Tables in database:", tables)

conn.close()