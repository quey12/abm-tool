import sqlite3
import json

# Load sample scraped data
with open('data/temp_data/linkedin_data.json', 'r') as f:
    data = json.load(f)

conn = sqlite3.connect('data/abm_tool.db')
c = conn.cursor()

# Insert companies and decision makers
for entry in data:
    c.execute("INSERT OR IGNORE INTO companies (name, industry, size, location) VALUES (?, ?, ?, ?)",
              (entry['company'], entry['industry'], entry['size'], entry['location']))
    c.execute("SELECT company_id FROM companies WHERE name = ?", (entry['company'],))
    company_id = c.fetchone()[0]
    c.execute("INSERT INTO decision_makers (name, job_title, company_id, linkedin_url) VALUES (?, ?, ?, ?)",
              (entry['name'], entry['title'], company_id, entry['linkedin_url']))

conn.commit()
conn.close()