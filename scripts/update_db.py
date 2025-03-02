import sqlite3

conn = sqlite3.connect('data/abm_tool.db')
c = conn.cursor()
c.execute("ALTER TABLE intent_signals ADD COLUMN url TEXT")
conn.commit()
conn.close()
print("Added URL column to intent_signals table.")