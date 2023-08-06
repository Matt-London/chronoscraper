from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import requests
import time
import re

BASE_URL = "https://www.chrono24.com"
CATEGORY = "/rolex"
PAGES = "/index-{}.htm"
MAX_PAGES = 50

REVIEW_ID_REGEX = r"^id-\d+$"

# Header to prevent access denied
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Chrome options to prevent browser popup from selenium
selenium_options = Options()
selenium_options.add_argument("--headless")
selenium_options.add_argument("--disable-gpu")


def get_watch_data(url: str) -> dict[str, str]:
    # Get the table from the page
    page = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(page.content, "html.parser")

    table = soup.find("table")

    # Get the watch attributes
    attributes = {"url": url}
    for category in table.find_all("tbody"):
        for attribute in category:
            # Drop empty lines
            if attribute.text.rstrip() == "":
                continue

            # Get all table data
            tds = attribute.find_all("td")

            # It should have exactly two td tags in order to be a valid attribute, otherwise it is probbably a header
            if len(tds) != 2:
                continue

            # Get the attribute name and value
            attr_name = tds[0].text.strip()
            # Occasionally there will be an added link after a new line so we will chop that off
            attr_value = tds[1].text.strip().split("\n")[0]

            # Save it to the dictionary
            attributes[attr_name] = attr_value

    return attributes


def get_reviews(url: str, max_pages: int = MAX_PAGES) -> list[dict[str, str]]:
    driver = webdriver.Chrome(options=selenium_options)

    def is_element_clickable(wait, locator):
        return wait.until(lambda driver: EC.element_to_be_clickable(locator)(driver))

    wait = WebDriverWait(driver, 10)

    try:
        driver.get(url)

        # Simulate click on the ok button for cookies
        ok_button_locator = (
            By.XPATH, "//button[@type='button' and @class='btn btn-primary btn-full-width js-cookie-accept-all wt-consent-layer-accept-all m-b-2']")
        ok_button = is_element_clickable(wait, ok_button_locator)
        ok_button.click()

        # Simulate click to the show more button until it is disabled
        pages_count = 0
        while True:
            show_more_locator = (
                By.XPATH, "//button[@type='button' and @class='btn btn-secondary' and contains(text(), 'Show more')]")
            show_more_button = is_element_clickable(wait, show_more_locator)
            show_more_button.click()

            pages_count += 1
            print(pages_count)
            if max_pages != 0 and pages_count >= max_pages:
                break

        page_content = driver.page_source
    except Exception as e:
        print(e)
        print(type(e))
        print("Error getting reviews")
        return []
    finally:
        driver.quit()

    soup = BeautifulSoup(page_content, "html.parser")

    dealer_ratings_container = soup.find("div", id="dealer-ratings")

    reviews = dealer_ratings_container.find(lambda tag: tag.name == 'div' and not tag.has_attr('class') and not tag.has_attr('id'))

    for review in reviews.find_all(
            lambda tag: tag.name == 'div' and tag.has_attr('id') and re.match(REVIEW_ID_REGEX, tag['id'])):
        print(review)


def get_watch_urls() -> list[str]:
    page = requests.get(BASE_URL + CATEGORY + PAGES.format(1), headers=HEADERS)
    soup = BeautifulSoup(page.content, "html.parser")

    # Get all the watch urls
    watch_images = soup.find_all("a", class_="js-article-item article-item block-item rcard")
    watch_urls = [BASE_URL + watch_image["href"] for watch_image in watch_images]

    return watch_urls


def main():
    # Get all the watch urls
    watch_urls = get_watch_urls()

    # Loop through the urls and get all the watch data
    for watch in watch_urls:
        print("Watch:")
        print(get_watch_data(watch))
        print(get_reviews(watch))
        print()


if __name__ == "__main__":
    main()
