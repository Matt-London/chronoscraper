"""
Main file for the Chronoscraper project

:author: Matt London
"""
import argparse
import json
import os
import tqdm

from chronoscraper.scraper import get_watch_urls, get_watch_data, get_reviews
from chronoscraper.database_handler import write_database_from_json


def scrape_data(watches_json: str, reviews_json: str, watch_urls: list[str], timeout: int,
                max_review_pages: int) -> None:
    """
    Scrape the data from the watch urls and write it to the json files

    :param watches_json: Path to the watches json file
    :param reviews_json: Path to the reviews json file
    :param watch_urls: List of watch urls to scrape
    :param timeout: Timeout for web requests
    :param max_review_pages: Maximum number of review pages to scrape for each watch
    """
    # ID counter
    watch_id = 1

    with open(watches_json, "w+") as watches_file, open(reviews_json, "w+") as reviews_file:
        # Write beginning of list
        watches_file.write("[")
        reviews_file.write("[")

        # Loop through the urls and get all the watch data
        for i, watch in enumerate(tqdm.tqdm(watch_urls, desc="Gathering watch data")):
            watch_data = get_watch_data(watch)
            watch_data["watch_id"] = str(watch_id)

            reviews_data = get_reviews(watch, watch_id, max_review_pages, timeout)

            json.dump(watch_data, watches_file)

            # Write each review separately to prevent it from being a list of lists
            for j, review in enumerate(reviews_data):
                json.dump(review, reviews_file)

                if i != len(watch_urls) - 1 or j != len(reviews_data) - 1:
                    reviews_file.write(",")

            # Write a comma if it's not the last watch
            if i != len(watch_urls) - 1:
                watches_file.write(",")

            watch_id += 1

        # Write end of list
        watches_file.write("]")
        reviews_file.write("]")


def main():
    # Setup arg parser
    parser = argparse.ArgumentParser(
        prog="Chronoscraper",
        description="Scrape chrono24.com for watch data and reviews",
        epilog="For any numerical limits besides timeout, enter 0 to scrape the maximum")

    parser.add_argument("database_path", help="Database file to write to")
    parser.add_argument("-t", "--timeout", default=10, help="Timeout for web requests")
    parser.add_argument("-r", "--reviews", default=50,
                        help="Maximum number of review pages to scrape for each watch")
    parser.add_argument("-p", "--pages", default=1, help="Maximum number of index pages to scrape")

    args = parser.parse_args()

    # Get the arguments
    timeout = int(args.timeout)
    max_review_pages = int(args.reviews)
    max_pages = int(args.pages)
    database = args.database_path

    # Get all the watch urls
    watch_urls = get_watch_urls(max_pages)

    # JSON file
    watches_json = "watches.json"
    reviews_json = "reviews.json"

    scrape_data(watches_json, reviews_json, watch_urls, timeout, max_review_pages)

    # Write the json files into the database
    write_database_from_json(watches_json, database, "watches")
    write_database_from_json(reviews_json, database, "reviews")

    os.remove(watches_json)
    os.remove(reviews_json)


if __name__ == "__main__":
    main()
