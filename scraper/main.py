import yaml
from datetime import date
from scraper import scrape_listing_type

today = date.today().isoformat()
with open("config.yaml") as f:
    config = yaml.safe_load(f)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

for listing_type in config["listing_types"]:
    scrape_listing_type(
        search_path=listing_type["search_path"],
        output_file = f"{listing_type['output_file'].replace('.jsonl', '')}_{today}.jsonl",
        base_url=config["base_url"],
        headers=headers,
        pages_to_scrape_limit=config["pages_to_scrape"],
        request_delay_seconds=config["request_delay_seconds"],
    )