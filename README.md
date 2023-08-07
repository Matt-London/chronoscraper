# chrono-scraper
Scraper for the chrono24.com website

## Usage
A usage message for the scraper is available by passing the `-h` flag:

```
usage: Chronoscraper [-h] [-t TIMEOUT] [-r REVIEWS] [-p PAGES] database_path

Scrape chrono24.com for watch data and reviews

positional arguments:
  database_path         Database file to write to

options:
  -h, --help            show this help message and exit
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout for web requests
  -r REVIEWS, --reviews REVIEWS
                        Maximum number of review pages to scrape for each watch
  -p PAGES, --pages PAGES
                        Maximum number of index pages to scrape

For any numerical limits besides timeout, enter 0 to scrape the maximum
```

## Database
The scraper will write to a SQLite database file

### Tables
- `watches`: Contains the information about each watch
- `reviews`: Contains the reviews for each watch

These tables can be correlated using the watch_id variable which can be matched from the `watches` table to the `reviews` table
