import sqlite3

conn = sqlite3.connect('data/abm_tool.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    industry TEXT,
    size TEXT,
    location TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS decision_makers (
    dm_id INTEGER PRIMARY KEY,
    name TEXT,
    job_title TEXT,
    company_id INTEGER,
    linkedin_url TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS intent_signals (
    signal_id INTEGER PRIMARY KEY,
    company_id INTEGER,
    signal_type TEXT,
    description TEXT,
    date TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
)''')

conn.commit()
conn.close()

print("Database initialized with tables: companies, decision_makers, intent_signals")