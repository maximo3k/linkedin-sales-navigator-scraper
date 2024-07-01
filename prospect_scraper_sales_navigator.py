import csv
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time

# How to use:
# virtual environment: python -m venv virt
# Create CSV that you want to write in.
# Put the time between actions high. Run the script and when the chrome window opens, log in. There are issues with Chrome profiles. Need to log in manually.
# Then you can cancel the application and finetune the timers, according to your Internet Connection

chrome_options = Options()
chrome_options.add_argument("--start-maximized")
user_data_dir = r'C:\Users\Max\AppData\Local\Google\Chrome\User Data\scraper_profile'
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# name of the CSV file we want to use
csv_file_name = 'scraped_prospects.csv'

def write_results_to_csv(results, filename):
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(['person_name', 'person_title', 'person_company', 'person_location', 'person_link'])

        for result in results:
            writer.writerow([result['person_name'], result['person_title'], result['person_company'], result['person_location'], result['person_link']])

def login_to_site(driver, config):
    print('start login')
    # go to login page
    driver.get("https://www.linkedin.com/login")

    # wait till element (name='session_key' is loaded) Should we base it on ID better?
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "session_key")))

    email_field = driver.find_element(By.NAME, "session_key")
    password_field = driver.find_element(By.NAME, "session_password")

    # enter id and pw
    email_field.send_keys(config['email'])
    password_field.send_keys(config['password'])

    # hit enter
    password_field.send_keys(Keys.RETURN)

    # if there is a security check
    time.sleep(15)

    # then wait till page loaded and hit the start url
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    driver.get(config['start_url'])


def scroll_extract(driver, items):
    results = []
    for index, item in enumerate(items):
        # initialize variables
        person_name = "NA"
        person_title = "NA"
        person_company = "NA"
        person_location = "NA"
        person_link = "NA"
        
        try:
            # Scroll the item into view using JavaScript
            driver.execute_script("arguments[0].scrollIntoView(true);", item)
            print(f"Scrolled to item {index + 1}")
            # wait till visible
            WebDriverWait(driver, 10).until(EC.visibility_of(item))

            item = driver.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item.pl3.pv3")[index]

            # Extract person's name safely
            name_element = item.find_element(By.CSS_SELECTOR, "span[data-anonymize='person-name']")
            person_name = name_element.text if name_element else "NA"

            link_element = name_element.find_element(By.XPATH, "..")
            person_link = link_element.get_attribute('href') if link_element else "NA"
            print(f'the person link is {person_link}')
            
            # Extract person's title safely
            title_element = item.find_element(By.CSS_SELECTOR, "span[data-anonymize='title']")
            person_title = title_element.text if title_element else "NA"

            # Extract company name safely
            company_element = item.find_element(By.CSS_SELECTOR, "a[data-anonymize='company-name']")
            person_company = company_element.text if company_element else "NA"

            # Extract location safely
            location_element = item.find_element(By.CSS_SELECTOR, "span[data-anonymize='location']")
            person_location = location_element.text if location_element else "NA"

            # Extract link

            print(person_name)
            results.append({
                    'person_name' : person_name,
                    'person_title' : person_title,
                    'person_company' : person_company,
                    'person_location' : person_location,
                    'person_link' : person_link,
                })

            # Wait for 1 second to allow any dynamic content to load
            time.sleep(1)
        except Exception as e:
            print(f"Failed to process item at index {index}: {str(e)}")
            # You may choose to append a record with NA values or just log the error
            results.append({
                'person_name': person_name,
                'person_title': person_title,
                'person_company': person_company,  # Default NA for company as the error occurred here
                'person_location': person_location,
                'person_link': person_link,
            })

    write_results_to_csv(results, 'prospects_1.csv')

    return

def scrape_results_page(driver):


    while True:  # Loop through all pages

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".artdeco-list")))
        time.sleep(4)

        # Find elements on the page
        li_elements_no_soup = driver.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item.pl3.pv3")
        # Scroll and extract information from the current page
        scroll_extract(driver, li_elements_no_soup)

        # Try to find the 'Next' button; if it's there and clickable, click it
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button.artdeco-pagination__button--next")
            if next_button.is_enabled():
                next_button.click()
                print("Navigated to next page")
            else:
                print("Next button not enabled, last page reached.")
                break
        except NoSuchElementException:
            print("No more pages to navigate.")
            break
        except Exception as e:
            print(f"Error navigating to next page: {str(e)}")
            break

    return

with open('config.json', 'r') as config_file:
    config = json.load(config_file)


login_to_site(driver, config)
scrape_results_page(driver)

time.sleep(10)

driver.quit()