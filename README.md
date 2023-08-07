# chronoscraper
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

These tables can be correlated using the `watch_id` variable which can be matched from the `watches` table to the `reviews` table

## Program Flow
1. Scrape the index pages for watches
2. Scrape the watch pages for watch information
3. Scrape the reviews from the watch page
4. Write the data into two json files
    - This is required as not all watch parameters are known until all keys are indexed and so a table cannot be created
5. Write the data from the json files into a SQLite database

## Example
In the `doc/` folder there is an example database file `watches.db`. This contains a scrape of the first two pages of the index and 10 pages of reviews from each watch.
This database was generated with the following command:
```bash
python3 src/main.py -p 2 -r 10 doc/watches.db
```

### Parameters
- `-p 2`: Scrape 2 pages of the index
- `-r 10`: Scrape 10 pages of reviews for each watch
- `doc/watches.db`: Write to the file `doc/watches.db`
