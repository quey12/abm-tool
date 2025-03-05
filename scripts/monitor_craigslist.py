# scripts/monitor_craigslist.py
import requests
from bs4 import BeautifulSoup
import sqlite3
import time

def scrape_craigslist():
    cities = [
        "https://newyork.craigslist.org", "https://sfbay.craigslist.org", "https://losangeles.craigslist.org",
        "https://chicago.craigslist.org", "https://atlanta.craigslist.org", "https://seattle.craigslist.org",
        "https://miami.craigslist.org", "https://houston.craigslist.org", "https://dallas.craigslist.org",
        "https://boston.craigslist.org", "https://philadelphia.craigslist.org", "https://denver.craigslist.org",
        "https://phoenix.craigslist.org", "https://portland.craigslist.org", "https://sandiego.craigslist.org"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    signals = []
    seen_descriptions = set()

    for city in cities:
        for section in ["ggg", "jjj"]:
            url = f"{city}/search/{section}?query=marketing"
            print(f"Fetching URL: {url}")
            response = requests.get(url, headers=headers)
            print(f"Response status: {response.status_code}")

            if response.status_code != 200:
                print(f"Failed to fetch {url}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('li', class_='cl-static-search-result')
            print(f"Found {len(listings)} listings with 'cl-static-search-result' in {section}")

            for listing in listings:
                title_div = listing.find('div', class_='title')
                link_tag = listing.find('a')
                if title_div and title_div.text.strip() and link_tag and link_tag.get('href'):
                    title = title_div.text.strip()
                    if title in seen_descriptions:
                        continue
                    seen_descriptions.add(title)
                    url = link_tag['href']
                    print(f"Listing title: {title}")
                    if any(keyword in title.lower() for keyword in ["marketing", "advertising", "seo", "social media", "campaign", "promotion"]):
                        company = extract_company(title)
                        for comp in company:
                            signals.append({
                                'company': comp,
                                'description': title,
                                'date': '2025-03-05',
                                'url': url,
                                'city': city.split('//')[1].split('.')[0],  # Keep city
                                'source': 'Craigslist'  # Add source for consistency
                            })
                            print(f"Signal found: {comp} - {title} ({city})")
                else:
                    print("No title or URL found in listing")
            time.sleep(5)

    return signals

def extract_company(title):
    exclude_words = {
        "the", "and", "for", "with", "how", "what", "it", "who", "new", "york", "area",
        "research", "ages", "test", "get", "paid", "today", "entry", "level", "b2b", "sales", "asap", "pay", "now",
        "hiring", "commission", "based", "remote", "team", "join", "our", "creative", "part", "time", "temporary",
        "college", "internship", "professional", "director", "manager", "group", "head", "growth", "huge", "street",
        "call", "casting", "models", "w", "visible", "hair", "loss", "toppers", "wigs", "in", "house", "san", "francisco",
        "los", "angeles", "chicago", "atlanta", "seattle", "miami", "houston", "dallas", "boston", "philadelphia",
        "denver", "phoenix", "portland", "diego", "black", "car", "uber", "lyft", "drivers", "short", "term", "project",
        "from", "home", "day", "potential", "super", "simple", "dancers", "demos", "video", "open", "base", "com"
    }
    parts = [p.strip() for p in title.split(',')]
    candidates = []
    
    for part in parts:
        words = part.split()
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
    return candidates[:1] if candidates else ["Unknown"]

def save_to_db(signals):
    if not signals:
        print("No signals to save")
        return
    conn = sqlite3.connect('data/abm_tool.db')
    c = conn.cursor()
    # Add both city and source columns
    for column in ['city', 'source']:
        try:
            c.execute(f"ALTER TABLE intent_signals ADD COLUMN {column} TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()

    for signal in signals:
        c.execute("INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)", (signal['company'], 'Marketing'))
        c.execute("SELECT company_id FROM companies WHERE name = ?", (signal['company'],))
        company_id = c.fetchone()[0]
        c.execute("""
            INSERT INTO intent_signals (company_id, signal_type, description, date, url, city, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company_id, 'craigslist', signal['description'], signal['date'], signal['url'], signal['city'], signal['source']))
    conn.commit()
    conn.close()
    print(f"Saved {len(signals)} signals to database")

if __name__ == "__main__":
    signals = scrape_craigslist()
    save_to_db(signals)