from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
import time
from selenium.webdriver.chrome.options import Options  # Ensure Options is imported

# Set up the driver (headless for efficiency)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
driver = webdriver.Chrome(options=chrome_options)

# Start on the first page
base_url = "https://www.yellowpages.com/search?search_terms=liquor+stores&geo_location_terms=New+Jersey"
driver.get(base_url)

current_page = 1
max_pages = 5  # Adjust as needed

while current_page <= max_pages:
    try:
        # Wait for listings to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'result')))
        print(f"Scraping page {current_page}")
        # Add your scraping logic here (e.g., using BeautifulSoup on driver.page_source)

        if current_page < max_pages:
            # Check if "Next" button exists
            next_buttons = driver.find_elements(By.CSS_SELECTOR, 'a.next.ajax-page')
            print(f"Found {len(next_buttons)} 'Next' buttons on page {current_page}")
            
            if not next_buttons:
                print(f"No more pages after page {current_page}")
                break

            # Use the first "Next" button and wait for it to be clickable
            next_button = next_buttons[0]
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(next_button))
            next_button.click()
            current_page += 1
            time.sleep(2)  # Brief pause for AJAX content to load

        else:
            print(f"Reached maximum pages ({max_pages})")
            break

    except TimeoutException:
        print(f"Timeout waiting for elements on page {current_page}. Check network or page load.")
        break
    except NoSuchElementException:
        print(f"No listings found on page {current_page}. Possibly incorrect selector or no results.")
        break
    except ElementClickInterceptedException:
        print(f"Could not click 'Next' button on page {current_page}. It may be obscured.")
        break
    except Exception as e:
        print(f"Unexpected error on page {current_page}: {e}")
        break

driver.quit()
print("Scraping completed.")