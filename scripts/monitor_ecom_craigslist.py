import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re

def scrape_craigslist_influencers():
    cities = [
        "https://newyork.craigslist.org",
        "https://sfbay.craigslist.org",
        "https://losangeles.craigslist.org",
        # Add more cities as needed
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    signals = []
    keywords = ["makeup", "videogames", "ecom", "ecommerce"]

    for city in cities:
        for keyword in keywords:
            url = f"{city}/search/sss?query={keyword}"
            print(f"Fetching URL: {url}")
            response = requests.get(url, headers=headers)
            print(f"Response status: {response.status_code}")

            if response.status_code != 200:
                print(f"Failed to fetch {url}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('li', class_='cl-static-search-result')
            print(f"Found {len(listings)} listings for {keyword} in {city}")

            for listing in listings:
                title_tag = listing.find('div', class_='title')
                link_tag = listing.find('a', href=True)
                if title_tag and link_tag:
                    title = title_tag.text.strip()
                    url = link_tag['href']
                    if any(kw in title.lower() for kw in keywords):
                        email = scrape_listing_email(url, headers)
                        company = extract_company(title) or "Unknown"
                        signals.append({
                            'company': company,
                            'description': title,
                            'date': '2025-03-01',
                            'url': url,
                            'source': f'Craigslist ({city.split("//")[1].split(".")[0]})',
                            'email': email
                        })
                        print(f"Signal found: {company} - {title} - Email: {email or 'Not found'}")
                else:
                    print("No title or URL found in listing")
            time.sleep(2)

    return signals

def scrape_listing_email(url, headers):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            body = soup.find('section', id='postingbody')
            if body:
                text = body.text.strip()
                email = re.search(r'[\w\.-]+@[\w\.-]+', text)
                return email.group(0) if email else None
        time.sleep(1)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return None

def extract_company(title):
    exclude_words = {
        "the", "and", "for", "with", "how", "what", "it", "who", "marketing", "advertising", "seo", "social", "media",
        "campaign", "promotion", "need", "seeking", "hire", "wanted", "looking", "required", "new", "york", "area",
        "research", "ages", "test", "get", "paid", "today", "entry", "level", "b2b", "sales", "asap", "pay", "now",
        "hiring", "commission", "based", "remote", "team", "join", "our", "creative", "part", "time", "temporary",
        "college", "internship", "professional", "director", "manager", "group", "head", "growth", "huge", "street",
        "ecommerce", "e-commerce", "online", "store", "shop", "amazon", "shopify", "dropshipping", "retail", "makeup",
        "videogames", "ecom"
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

def save_to_db(signals):
    if not signals:
        print("No signals to save")
        return
    conn = sqlite3.connect('data/abm_tool.db')
    c = conn.cursor()
    for signal in signals:
        company = signal['company'] if signal['company'] else "Unknown"
        c.execute("INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)", (company, 'Ecommerce'))
        c.execute("SELECT company_id FROM companies WHERE name = ?", (company,))
        company_id = c.fetchone()[0]
        c.execute("""
            INSERT INTO ecom_signals (company_id, signal_type, description, date, url, source, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company_id, 'ecom', signal['description'], signal['date'], signal['url'], signal['source'], signal['email']))
    conn.commit()
    conn.close()
    print(f"Saved {len(signals)} signals to database")

if __name__ == "__main__":
    signals = scrape_craigslist_influencers()
    save_to_db(signals)