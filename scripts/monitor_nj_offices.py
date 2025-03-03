# scripts/monitor_nj_offices.py
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

print("Starting NJ, Philly, PA office scraper...")

def save_to_db(signals, conn):
    if not signals:
        print("No signals to save this batch")
        return
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS office_buildings (
            signal_id INTEGER PRIMARY KEY,
            company_id INTEGER,
            signal_type TEXT,
            description TEXT,
            date TEXT,
            url TEXT,
            source TEXT,
            contacted INTEGER DEFAULT 0,
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        )
    """)
    for signal in signals:
        company = signal['company'] if signal['company'] else "Unknown"
        c.execute("INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)", (company, 'Office Building'))
        c.execute("SELECT company_id FROM companies WHERE name = ?", (company,))
        company_id = c.fetchone()[0]
        c.execute("""
            INSERT INTO office_buildings (company_id, signal_type, description, date, url, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company_id, 'office', signal['description'], signal['date'], signal['url'], signal['source']))
    conn.commit()
    print(f"Saved {len(signals)} signals to office_buildings table")

def extract_company(title):
    exclude_words = {
        "the", "and", "for", "with", "how", "what", "it", "who", "marketing", "advertising", "seo", "social", "media",
        "campaign", "promotion", "need", "seeking", "hire", "wanted", "looking", "required", "new", "york", "area",
        "research", "ages", "test", "get", "paid", "today", "entry", "level", "b2b", "sales", "asap", "pay", "now",
        "hiring", "commission", "based", "remote", "team", "join", "our", "creative", "part", "time", "temporary",
        "college", "internship", "professional", "director", "manager", "group", "head", "growth", "huge", "street",
        "ecommerce", "e-commerce", "online", "store", "shop", "amazon", "shopify", "dropshipping", "retail", "makeup",
        "videogames", "ecom", "business", "office", "commercial", "space"
    }
    parts = title.split(',')
    candidates = []
    for part in parts:
        words = part.strip().split()
        i = 0
        while i < len(words):
            if words[i][0].isupper() and len(words[i]) > 2:
                if i + 1 < len(words) and words[i + 1][0].isupper():
                    candidate = f"{words[i]} {words[i + 1]}"
                    if not any(exclude in candidate.lower() for exclude in exclude_words):
                        candidates.append(candidate)
                    i += 2
                elif not any(exclude in words[i].lower() for exclude in exclude_words):
                    candidates.append(words[i])
                    i += 1
                else:
                    i += 1
            else:
                i += 1
    return candidates[0] if candidates else None

def scrape_nj_offices():
    cities = [
        "https://newyork.craigslist.org",
        "https://cnj.craigslist.org",
        "https://southjersey.craigslist.org",
        "https://northjersey.craigslist.org",
        "https://philadelphia.craigslist.org",
        "https://allentown.craigslist.org",
        "https://scranton.craigslist.org",
        "https://pennstate.craigslist.org",
        "https://harrisburg.craigslist.org",
        "https://poconos.craigslist.org"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    conn = sqlite3.connect('data/abm_tool.db')

    all_signals = []
    for city in cities:
        url = f"{city}/search/off"
        print(f"Fetching URL: {url}")
        try:
            response = session.get(url, headers=headers, timeout=10)
            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Failed to fetch {url}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('li', class_='cl-static-search-result')
            print(f"Found {len(listings)} listings in {city}")

            signals = []
            for listing in listings:
                title_tag = listing.find('div', class_='title')
                link_tag = listing.find('a', href=True)
                if title_tag and link_tag:
                    title = title_tag.text.strip()
                    url = link_tag['href']
                    if any(kw in title.lower() for kw in ["office", "commercial", "building", "space"]):
                        company = extract_company(title) or "Unknown"
                        signals.append({
                            'company': company,
                            'description': title,
                            'date': '2025-03-03',
                            'url': url,
                            'source': f'Craigslist ({city.split("//")[1].split(".")[0]})'
                        })
                        print(f"Signal found: {company} - {title}")
            all_signals.extend(signals)
            save_to_db(signals, conn)  # Save per city
            time.sleep(2)
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue

    conn.close()
    print(f"Total signals collected: {len(all_signals)}")
    return all_signals

if __name__ == "__main__":
    print("Running main function...")
    signals = scrape_nj_offices()
    print("Script completed.")