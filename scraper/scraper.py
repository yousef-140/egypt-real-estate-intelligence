import time
import json
import requests
from bs4 import BeautifulSoup

from extractors import get_total_pages, extract_listing


def scrape_page(page_num, search_path, base_url, headers):
    page_url = f"{base_url}{search_path}?page={page_num}"
    response = requests.get(page_url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page {page_num}: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    cards = soup.find_all("article", class_="listing-card")
    page_listings = []
    for card in cards:
        listing = extract_listing(card, base_url)
        page_listings.append(listing)
    return page_listings


def save_to_jsonl(listings, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for listing in listings:
            f.write(json.dumps(listing, ensure_ascii=False) + "\n")


def scrape_listing_type(search_path, output_file, base_url, headers, pages_to_scrape_limit, request_delay_seconds):
    url = base_url + search_path
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    page_count = get_total_pages(soup)
    pages_to_scrape = min(pages_to_scrape_limit, page_count)

    all_listings = []
    for page_num in range(1, pages_to_scrape + 1):
        print(f"Scraping {search_path} - page {page_num}...")
        listings = scrape_page(page_num, search_path, base_url, headers)
        all_listings.extend(listings)
        time.sleep(request_delay_seconds)

    save_to_jsonl(all_listings, output_file)
    print(f"Saved {len(all_listings)} listings to {output_file}")