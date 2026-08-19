import re
from urllib.parse import urljoin


def get_total_pages(soup, listings_per_page=20):
    p_tag = soup.find("p", class_="text-body-2 md:text-body-1 flex-1 flex gap-0.5x whitespace-nowrap truncate text-gray__dark_2")
    if p_tag is None:
        return None

    full_text = p_tag.get_text()
    digits = re.sub(r"[^\d]", "", full_text)

    if not digits:
        return None

    total_count = int(digits)
    total_pages = (total_count + listings_per_page - 1) // listings_per_page

    return total_pages


def safe_extract(card, tag, class_name=None, attr=None):
    if class_name:
        element = card.find(tag, class_=class_name)
    else:
        element = card.find(tag)
    if element is None:
        return None
    if attr:
        return element.get(attr)
    return element.get_text(strip=True)


def safe_extract_sibling(card, icon_class):
    icon = card.find("i", class_=icon_class)
    if icon is None:
        return None
    parent_li = icon.find_parent("li")
    if parent_li is None:
        return None
    span = parent_li.find("span")
    if span is None:
        return None
    return span.get_text(strip=True)


def extract_listing(card, base_url):
    price = safe_extract(card, 'data', None, attr='value')
    title = safe_extract(card, 'h2', None, attr='title')
    size = safe_extract_sibling(card, "size-icon")
    bedrooms = safe_extract_sibling(card, "bedroom-icon")
    bathrooms = safe_extract_sibling(card, "bathroom-icon")

    link_tag = card.find("a", href=True)
    if link_tag:
        relative_link = link_tag['href']
        listing_url = urljoin(base_url, relative_link)
    else:
        listing_url = None

    return {
        "price": price,
        "title": title,
        "size": size,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "url": listing_url
    }