from itertools import count
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup
from bs4.element import Tag

import tqdm
import requests
import re

BASE_URL = "https://www.chrono24.com"
CATEGORY = "/rolex"
PAGES = "/index-{}.htm"
MAX_PAGES = 10
TIMEOUT = 25

REVIEW_ID_REGEX = r"^id-\d+$"

# Header to prevent access denied from the scraper
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Chrome options to prevent browser popup from selenium
selenium_options = Options()
selenium_options.add_argument("--headless")
selenium_options.add_argument("--disable-gpu")
selenium_options.add_experimental_option("excludeSwitches", ["enable-logging"])


def click_show_more_buttons(driver: WebDriver, timeout: int) -> None:
    """
    Loop through all show more link buttons in reviews, so they are all readable

    :param driver: Webdriver that is currently on the page with reviews
    :param timeout: Timeout for waiting for the show more buttons to be clickable
    :return:
    """
    SHOW_MORE_BUTTON_XPATH = "//button[@type='button' and @class='text-link' and span[text()=' Show more']]"
    show_more_buttons_locator = (
        By.XPATH, SHOW_MORE_BUTTON_XPATH
    )

    # Wait for at least one "Show more" button to be present before proceeding
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located(show_more_buttons_locator))

    while True:
        show_more_buttons = driver.find_elements(*show_more_buttons_locator)

        if not show_more_buttons:
            break

        try:
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, SHOW_MORE_BUTTON_XPATH)))

            show_more_buttons[0].click()

        except StaleElementReferenceException:
            # The button may no longer exist
            continue


def get_review(review: Tag, watch_id: int) -> dict[str, str] | None:
    """
    Take in a bs4 review and return a dictionary built from its data

    :param review: BeautifulSoup review element
    :param watch_id: ID of the watch the review is for
    :return Dictionary of review data if successful, None otherwise
    """
    header = (review.find("div", class_="d-flex align-items-center m-b-4")
              .find("div", class_="d-flex flex-column"))

    body = (review.find("div", class_="card-padding")
            .find_all("div", class_="m-b-4")[1])

    button = header.find("button", class_="text-lg relative rating-card-tooltip")

    rating = button.find("span", class_="m-r-1").find("strong").text.strip()

    # Get the name attribute by finding a span under button with no class specified
    name = button.find(lambda tag: tag.name == "span" and not tag.has_attr("class")).text.strip()

    date = header.find("time", class_="text-muted").text.strip()

    text_container = body.find("div", class_="m-b-4")

    if text_container is None:
        # This is not a review for the watch and it may be in the carousel
        return None
    else:
        try:
            title = text_container.find("strong").text.strip()
        except:
            return None

        try:
            content = text_container.find("p", class_="m-b-0").text.strip()
        except:
            return None

        try:
            dealer_response = body.find("div", class_="left-card-border p-l-3").find("p", class_="m-b-0").text.strip()
        except:
            dealer_response = ""

    return {
        "watch_id": str(watch_id),
        "rating": rating,
        "name": name,
        "date": date,
        "title": title,
        "content": content,
        "dealer_response": dealer_response
    }


def get_watch_data(url: str) -> dict[str, str]:
    """
    Get the watch attributes from the watch page

    :param url: Url of the watch page
    :return: Dictionary of watch attributes
    """
    # Get the table from the page
    page = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(page.content, "html.parser")

    table = soup.find("table")

    # Get the watch attributes
    attributes = {"Url": url}
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


def get_reviews(url: str, watch_id: int, max_review_pages: int = MAX_PAGES,
                timeout: int = TIMEOUT) -> list[dict[str, str]]:
    """
    Get all reviews for a watch

    :param url: Url of the watch page
    :param watch_id: ID of the watch
    :param max_review_pages: Maximum number of pages to get reviews from (show more clicks)
    :param timeout: Timeout for waiting for elements to be clickable
    :return: List of dictionaries of review data for a watch
    """
    driver = webdriver.Chrome(options=selenium_options)

    def is_element_clickable(wait, locator):
        try:
            element = wait.until(EC.presence_of_element_located(locator))
            if element.is_enabled():
                wait.until(EC.element_to_be_clickable(locator))
                return element
            else:
                return element
        except:
            return None

    try:
        driver.get(url)

        # Simulate click on the ok button for cookies
        ok_button_locator = (
            By.XPATH, "//button[@type='button' and @class='btn btn-primary btn-full-width js-cookie-accept-all wt-consent-layer-accept-all m-b-2']")
        ok_button = is_element_clickable(WebDriverWait(driver, timeout), ok_button_locator)
        ok_button.click()

        # Simulate click to the show more button until it is disabled
        pages_count = 0
        while True:
            show_more_locator = (
                By.XPATH, "//button[@type='button' and @class='btn btn-secondary' and contains(text(), 'Show more')]")
            show_more_button = is_element_clickable(WebDriverWait(driver, 1), show_more_locator)

            if show_more_button is None:
                # This means that all pages have been expanded
                break

            show_more_button.click()

            pages_count += 1
            if max_review_pages != 0 and pages_count >= max_review_pages:
                break

        # Now we want to click all the show more buttons for review content
        click_show_more_buttons(driver, timeout)

        page_content = driver.page_source

    except:
        # Usually this is an edge case with the button so it is acceptable to just return an empty list
        return []
    finally:
        driver.quit()

    soup = BeautifulSoup(page_content, "html.parser")

    dealer_ratings_container = soup.find("div", id="dealer-ratings")

    reviews = dealer_ratings_container.find(lambda tag: tag.name == 'div' and not tag.has_attr('class') and not tag.has_attr('id'))

    review_list = []

    for review in reviews.find_all(
            lambda tag: tag.name == 'div' and tag.has_attr('id') and re.match(REVIEW_ID_REGEX, tag['id'])):
        review_data = get_review(review, watch_id)

        if review_data is not None:
            review_list.append(review_data)

    return review_list


def get_watch_urls(max_pages: int = 0) -> list[str]:
    """
    Get all watch urls from the index page

    :param max_pages: Number of pages to get watch urls from (0 for all)
    :return: List of all URLs on the page(s)
    """
    watch_urls = []

    if max_pages == 0:
        generator = count(1)
    else:
        generator = range(1, max_pages + 1)

    for i in tqdm.tqdm(generator, desc="Gathering watch URLs"):
        request_url = BASE_URL + CATEGORY + PAGES.format(i)
        page = requests.get(request_url, headers=HEADERS)

        # Make sure the url is equal to the one we requested
        if page.url != request_url:
            # This means we hit the maximum number of pages and we should break
            break

        soup = BeautifulSoup(page.content, "html.parser")

        # Get all the watch urls
        watch_images = soup.find_all("a", class_="js-article-item article-item block-item rcard")
        page_urls = [BASE_URL + watch_image["href"] for watch_image in watch_images]

        watch_urls.extend(page_urls)

    return watch_urls
