# scripts/monitor_health_offices_ny_nj_pa.py
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

print("Starting NY, NJ, PA health office scraper...")

def save_to_db(signals, conn):
    if not signals:
        print("No signals to save this batch")
        return
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS health_offices (
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
        c.execute("INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)", (company, signal['signal_type']))
        c.execute("SELECT company_id FROM companies WHERE name = ?", (company,))
        company_id = c.fetchone()[0]
        c.execute("""
            INSERT INTO health_offices (company_id, signal_type, description, date, url, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company_id, signal['signal_type'], signal['description'], signal['date'], signal['url'], signal['source']))
    conn.commit()
    print(f"Saved {len(signals)} signals to health_offices table")

def extract_company(title):
    exclude_words = {
        "the", "and", "for", "with", "how", "what", "it", "who", "marketing", "advertising", "seo", "social", "media",
        "campaign", "promotion", "need", "seeking", "hire", "wanted", "looking", "required", "new", "york", "area",
        "research", "ages", "test", "get", "paid", "today", "entry", "level", "b2b", "sales", "asap", "pay", "now",
        "hiring", "commission", "based", "remote", "team", "join", "our", "creative", "part", "time", "temporary",
        "college", "internship", "professional", "director", "manager", "group", "head", "growth", "huge", "street",
        "office", "job", "employment", "nj", "new", "jersey", "pa", "pennsylvania", "dental", "dentist", "space",
        "chiropractic", "physical", "therapy", "optometry", "veterinary", "vet", "medspa", "medical", "spa", "podiatry"
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

def scrape_craigslist():
    cities = [
        "https://newyork.craigslist.org", "https://albany.craigslist.org", "https://buffalo.craigslist.org",
        "https://rochester.craigslist.org", "https://syracuse.craigslist.org", "https://cnj.craigslist.org",
        "https://southjersey.craigslist.org", "https://northjersey.craigslist.org", "https://allentown.craigslist.org",
        "https://scranton.craigslist.org", "https://pennstate.craigslist.org", "https://harrisburg.craigslist.org",
        "https://poconos.craigslist.org", "https://erie.craigslist.org", "https://pittsburgh.craigslist.org"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    conn = sqlite3.connect('data/abm_tool.db')

    keywords = {
        "dental": ["dental", "dentist", "practice"],
        "chiropractic": ["chiropractic", "chiropractor"],
        "physical therapy": ["physical therapy", "physical therapist", "pt"],
        "optometry": ["optometry", "optometrist", "eye"],
        "veterinary": ["veterinary", "vet", "animal"],
        "medspa": ["medspa", "medical spa", "aesthetic"],
        "podiatry": ["podiatry", "podiatrist", "foot"]
    }
    all_signals = []
    for city in cities:
        for section in ["/search/off", "/search/jjj"]:
            url = f"{city}{section}" + ("?query=dental+office" if section == "/search/jjj" else "")
            print(f"Fetching Craigslist URL: {url}")
            try:
                response = session.get(url, headers=headers, timeout=10)
                print(f"Response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Failed to fetch {url}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                listings = soup.find_all('li', class_='cl-static-search-result')
                print(f"Found {len(listings)} listings in {city} ({section})")

                signals = []
                for listing in listings:
                    title_tag = listing.find('div', class_='title')
                    link_tag = listing.find('a', href=True)
                    if title_tag and link_tag:
                        title = title_tag.text.strip()
                        url = link_tag['href']
                        title_lower = title.lower()
                        for signal_type, kws in keywords.items():
                            if any(kw in title_lower for kw in kws) and any(term in title_lower for term in ["office", "practice", "center", "clinic"]):
                                company = extract_company(title) or "Unknown"
                                signals.append({
                                    'company': company,
                                    'signal_type': signal_type,
                                    'description': title,
                                    'date': '2025-03-04',
                                    'url': url,
                                    'source': f'Craigslist ({city.split("//")[1].split(".")[0]})'
                                })
                                print(f"Signal found: {company} - {title} ({signal_type})")
                all_signals.extend(signals)
                save_to_db(signals, conn)
                time.sleep(2)
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                continue

    conn.close()
    return all_signals

def scrape_google():
    url = "https://www.google.com/search?q=dental+offices+chiropractic+physical+therapy+optometry+veterinary+medspa+podiatry+new+york+new+jersey+pennsylvania+site:*.edu+|site:*.org+|site:*.gov+|site:*.com+-inurl:(signup+login)"
    signals = []

    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"Fetching Google URL: {url}")
        driver.get(url)
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listings = soup.find_all('div', class_='tF2Cxc')
        print(f"Found {len(listings)} listings on Google")
        
        conn = sqlite3.connect('data/abm_tool.db')
        keywords = {
            "dental": ["dental", "dentist"],
            "chiropractic": ["chiropractic", "chiropractor"],
            "physical therapy": ["physical therapy", "physical therapist", "pt"],
            "optometry": ["optometry", "optometrist", "eye"],
            "veterinary": ["veterinary", "vet", "animal"],
            "medspa": ["medspa", "medical spa", "aesthetic"],
            "podiatry": ["podiatry", "podiatrist", "foot"]
        }
        for listing in listings:
            title_tag = listing.find('h3')
            link_tag = listing.find('a', href=True)
            if title_tag and link_tag:
                title = title_tag.text.strip()
                url = link_tag['href']
                title_lower = title.lower()
                for signal_type, kws in keywords.items():
                    if any(kw in title_lower for kw in kws) and any(term in title_lower for term in ["office", "practice", "center", "clinic"]):
                        company = extract_company(title) or "Unknown"
                        signals.append({
                            'company': company,
                            'signal_type': signal_type,
                            'description': title,
                            'date': '2025-03-04',
                            'url': url,
                            'source': 'Google'
                        })
                        print(f"Signal found: {company} - {title} ({signal_type})")
        save_to_db(signals, conn)
        driver.quit()
        conn.close()
    except Exception as e:
        print(f"Google scrape error: {e}")
    return signals

if __name__ == "__main__":
    print("Running main function...")
    try:
        cl_signals = scrape_craigslist()
        google_signals = scrape_google()
        total_signals = cl_signals + google_signals
        print(f"Total signals collected: {len(total_signals)}")
    except Exception as e:
        print(f"Main execution error: {e}")
    print("Script completed.")