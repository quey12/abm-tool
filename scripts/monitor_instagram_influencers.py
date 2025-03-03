# scripts/monitor_instagram_influencers.py
from bs4 import BeautifulSoup
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re

def scrape_instagram_influencers():
    url = "https://www.instagram.com/explore/tags/ecommerce/"
    signals = []

    chrome_options = Options()
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=chrome_options)
    
    print(f"Opening URL: {url}")
    driver.get(url)
    
    input("Log in to Instagram in the browser, then press Enter here to continue...")
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    posts = soup.find_all('div', class_='_aabd')  # Instagram post containers
    print(f"Found {len(posts)} posts on Instagram")
    
    if not posts:
        print("No posts found. Dumping first 1000 chars of HTML:")
        print(driver.page_source[:1000])
    
    keywords = ["ecom", "ecommerce", "marketing", "seo", "business"]
    for post in posts:
        caption_tag = post.find('span', class_='_aacl')  # Post caption
        if caption_tag:
            text = caption_tag.text.strip()
            link_tag = post.find('a', href=True)
            url = f"https://www.instagram.com{link_tag['href']}" if link_tag else "https://www.instagram.com"
            if any(kw in text.lower() for kw in keywords):
                company = extract_company(text) or "Unknown"
                signals.append({
                    'company': company,
                    'description': text,
                    'date': '2025-03-01',
                    'url': url,
                    'source': 'Instagram'
                })
                print(f"Signal found: {company} - {text}")
    
    driver.quit()
    return signals

def extract_company(title):
    exclude_words = {
        "the", "and", "for", "with", "how", "what", "it", "who", "marketing", "advertising", "seo", "social", "media",
        "campaign", "promotion", "need", "seeking", "hire", "wanted", "looking", "required", "new", "york", "area",
        "research", "ages", "test", "get", "paid", "today", "entry", "level", "b2b", "sales", "asap", "pay", "now",
        "hiring", "commission", "based", "remote", "team", "join", "our", "creative", "part", "time", "temporary",
        "college", "internship", "professional", "director", "manager", "group", "head", "growth", "huge", "street",
        "ecommerce", "e-commerce", "online", "store", "shop", "amazon", "shopify", "dropshipping", "retail", "makeup",
        "videogames", "ecom", "business"
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
    # Create instagram_signals table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS instagram_signals (
            signal_id INTEGER PRIMARY KEY,
            company_id INTEGER,
            signal_type TEXT,
            description TEXT,
            date TEXT,
            url TEXT,
            source TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        )
    """)
    for signal in signals:
        company = signal['company'] if signal['company'] else "Unknown"
        c.execute("INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)", (company, 'Influencer'))
        c.execute("SELECT company_id FROM companies WHERE name = ?", (company,))
        company_id = c.fetchone()[0]
        c.execute("""
            INSERT INTO instagram_signals (company_id, signal_type, description, date, url, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company_id, 'instagram', signal['description'], signal['date'], signal['url'], signal['source']))
    conn.commit()
    conn.close()
    print(f"Saved {len(signals)} signals to instagram_signals table")

if __name__ == "__main__":
    signals = scrape_instagram_influencers()
    save_to_db(signals)