# scripts/monitor_liquor_stores_nj_pa.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sqlite3
import time
import traceback

print("Starting NJ & PA liquor store scraper...")

def save_to_db(signals, conn):
    if not signals:
        print("No signals to save this batch")
        return
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS liquor_stores (
            signal_id INTEGER PRIMARY KEY,
            company_id INTEGER,
            signal_type TEXT,
            name TEXT,
            phone TEXT,
            address TEXT,
            url TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id INTEGER PRIMARY KEY,
            name TEXT,
            industry TEXT
        )
    """)
    for signal in signals:
        company = signal['name'] if signal['name'] else "Unknown"
        c.execute("INSERT OR IGNORE INTO companies (name, industry) VALUES (?, ?)", (company, 'Liquor Store'))
        c.execute("SELECT company_id FROM companies WHERE name = ?", (company,))
        company_id = c.fetchone()[0]
        c.execute("""
            INSERT INTO liquor_stores (company_id, signal_type, name, phone, address, url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company_id, 'liquor_store', signal['name'], signal['phone'], signal['address'], signal['url']))
    conn.commit()
    print(f"Saved {len(signals)} liquor store signals to database")

def scrape_liquor_stores(state, pages=5):
    base_url = f"https://www.yellowpages.com/search?search_terms=liquor+stores&geo_location_terms={state}"
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    conn = sqlite3.connect('data/abm_tool.db')
    
    all_signals = []
    seen_numbers = set()

    # Scrape page 1
    print(f"Fetching page 1 for {state}")
    driver.get(base_url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'result')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listings = soup.find_all('div', class_='result')
        print(f"Found {len(listings)} listings on page 1 for {state}")

        signals = []
        for listing in listings:
            name_tag = listing.find('a', class_='business-name')
            phone_tag = listing.find('div', class_='phones')
            addr_tag = listing.find('div', class_='street-address')
            url_tag = listing.find('a', class_='business-name', href=True)

            name = name_tag.text.strip() if name_tag else "Unknown"
            phone = phone_tag.text.strip() if phone_tag else "N/A"
            address = addr_tag.text.strip() if addr_tag else "N/A"
            url = f"https://www.yellowpages.com{url_tag['href']}" if url_tag else base_url

            if phone != "N/A" and phone not in seen_numbers:
                seen_numbers.add(phone)
                signals.append({
                    'name': name,
                    'phone': phone,
                    'address': address,
                    'url': url
                })
                print(f"Signal found: {name} - {phone} - {address}")
        
        all_signals.extend(signals)
        save_to_db(signals, conn)
    except Exception as e:
        print(f"Error on page 1 for {state}: {e}\n{traceback.format_exc()}")

    # Scrape pages 2 to 5 by clicking "Next"
    for page in range(2, pages + 1):
        try:
            next_button = driver.find_element(By.CLASS_NAME, 'next')  # Locate the "Next" button
            next_button.click()  # Click to go to the next page
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'result')))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            listings = soup.find_all('div', class_='result')
            print(f"Found {len(listings)} listings on page {page} for {state}")

            signals = []
            for listing in listings:
                name_tag = listing.find('a', class_='business-name')
                phone_tag = listing.find('div', class_='phones')
                addr_tag = listing.find('div', class_='street-address')
                url_tag = listing.find('a', class_='business-name', href=True)

                name = name_tag.text.strip() if name_tag else "Unknown"
                phone = phone_tag.text.strip() if phone_tag else "N/A"
                address = addr_tag.text.strip() if addr_tag else "N/A"
                url = f"https://www.yellowpages.com{url_tag['href']}" if url_tag else base_url

                if phone != "N/A" and phone not in seen_numbers:
                    seen_numbers.add(phone)
                    signals.append({
                        'name': name,
                        'phone': phone,
                        'address': address,
                        'url': url
                    })
                    print(f"Signal found: {name} - {phone} - {address}")
            
            all_signals.extend(signals)
            save_to_db(signals, conn)
            time.sleep(2)  # Add delay to avoid overwhelming the server
        except Exception as e:
            print(f"No more pages or error on page {page} for {state}: {e}")
            break

    driver.quit()
    conn.close()
    return all_signals

if __name__ == "__main__":
    print("Running main function...")
    nj_signals = scrape_liquor_stores("New+Jersey", pages=5)
    pa_signals = scrape_liquor_stores("Pennsylvania", pages=5)
    total_signals = nj_signals + pa_signals
    print(f"Total liquor store signals collected: {len(total_signals)}")
    print("Script completed.")