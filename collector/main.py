import argparse
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from db import save_listings


BASE_URL = "https://www.mubawab.ma/fr/ct/casablanca/immobilier-a-vendre"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}


class Scraper:
    def __init__(self, base_url, delay=1.0):
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def page_url(self, page):
        # Mubawab paginates with a ":p:N" suffix
        return self.base_url if page == 1 else f"{self.base_url}:p:{page}"

    def fetch(self, page, retries=3):
        for attempt in range(1, retries + 1):
            try:
                response = self.session.get(self.page_url(page), timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException:
                if attempt == retries:
                    raise
                time.sleep(5 * attempt)

    def scrape(self, max_pages=None, on_page=None):
        """Scrape pages until the site runs out of results (or max_pages).

        on_page(records) is called with each page's new listings so they can
        be saved incrementally.
        """
        listings_data = []
        seen = set()
        page = 1
        while max_pages is None or page <= max_pages:
            try:
                html = self.fetch(page)
            except requests.RequestException as e:
                print(f"Page {page}: request failed ({e}), stopping.")
                break

            # Past the last page the site says "0 résultats" and shows filler listings
            if total_results(html) == 0:
                print(f"Page {page}: no more results, done.")
                break

            # Sponsored listings repeat on every page, keep only the first occurrence
            new_records = [r for r in parse_page(html) if (r["type"], r["id"]) not in seen]
            if not new_records:
                print(f"Page {page}: no new listings, done.")
                break

            seen.update((r["type"], r["id"]) for r in new_records)
            listings_data.extend(new_records)
            if on_page:
                on_page(new_records)
            print(f"Page {page}: {len(new_records)} listings (total {len(listings_data)})")
            page += 1
            time.sleep(self.delay)
        return listings_data


def total_results(html):
    match = re.search(r"(\d[\d\s ]*)\s*résultats", html)
    return to_int(match.group(1)) if match else None


def to_int(text):
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def parse_listing(box):
    # 1. Title & URL (Skip if not a valid listing container)
    title_tag = box.select_one(".titleRow .listingTit a")
    if not title_tag:
        return None

    title = title_tag.get_text(strip=True)
    url = title_tag.get("href")

    # 2. Ad ID & type ("ad" for regular listings, "promotion" for developer projects)
    id_tag = box.select_one(".favDivPickId[id]")
    ad_id = id_tag.get("id") if id_tag else None
    listing_type = id_tag.get("type") if id_tag else None
    if not ad_id and url:
        match = re.search(r"/(?:pa|a|p)/(\d+)", url)
        if match:
            ad_id = match.group(1)

    # 3. Price & Currency ("Prix à consulter" has no digits -> None)
    price, currency = None, None
    price_tag = box.find("span", class_="priceTag")
    if price_tag:
        currency_tag = price_tag.find("span", class_="priceCurrency")
        currency = currency_tag.get_text(strip=True) if currency_tag else None
        amount_tag = price_tag.find("bdi") or price_tag
        price = to_int(amount_tag.get_text(strip=True))

    # 4. Location
    location_tag = box.select_one(".contactBar .listingH3")
    location = location_tag.get_text(strip=True) if location_tag else None
    neighborhood, city = None, None
    if location:
        parts = [p.strip() for p in location.split(",")]
        neighborhood = parts[0]
        city = parts[-1] if len(parts) > 1 else None

    # 5. Features (Mapped via icons; promotions list per-unit specs, keep the first)
    surface, rooms, bedrooms, bathrooms = None, None, None, None
    for feat in box.select(".adDetailFeature"):
        icon = feat.find("i")
        if not icon:
            continue
        classes = " ".join(icon.get("class", []))
        value = to_int(feat.get_text(strip=True))
        if "icon-triangle" in classes and surface is None:
            surface = value
        elif "icon-house-boxes" in classes and rooms is None:
            rooms = value
        elif "icon-bed" in classes and bedrooms is None:
            bedrooms = value
        elif "icon-bath" in classes and bathrooms is None:
            bathrooms = value

    amenities = [a.get_text(strip=True) for a in box.select(".adFeatures .adFeature span")]

    # 6. Description
    desc_tag = box.find("p", class_="descLi")
    description = " ".join(desc_tag.get_text().split()) if desc_tag else None

    return {
        "id": ad_id,
        "type": listing_type,
        "title": title,
        "url": url,
        "price": price,
        "currency": currency,
        "location": location,
        "neighborhood": neighborhood,
        "city": city,
        "surface_m2": surface,
        "rooms": rooms,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "amenities": ", ".join(amenities) or None,
        "description": description,
    }


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    records = []
    for box in soup.select(".contentBox"):
        try:
            record = parse_listing(box)
            if record:
                records.append(record)
        except Exception as e:
            print(f"Error parsing an element: {e}")
    return records


# run program
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Mubawab listings")
    parser.add_argument("--url", default=BASE_URL)
    parser.add_argument("--pages", type=int, help="max pages to scrape (default: all)")
    parser.add_argument("--output", help="also write results to this CSV file")
    parser.add_argument("--no-db", action="store_true", help="skip saving to PostgreSQL")
    args = parser.parse_args()

    on_page = None if args.no_db else save_listings
    listings_data = Scraper(args.url).scrape(args.pages, on_page=on_page)

    # Convert to DataFrame with safety checks
    df = pd.DataFrame(listings_data)

    if not df.empty:
        print(f"Successfully extracted {len(df)} clean listings.")
        print(df[["id", "type", "price", "surface_m2", "rooms", "bedrooms", "bathrooms", "neighborhood"]].head(10))
        if args.output:
            df.to_csv(args.output, index=False)
            print(f"Wrote CSV -> {args.output}")
        if not args.no_db:
            print(f"Saved {len(df)} listings to PostgreSQL table 'listings'")
    else:
        print("Warning: DataFrame is empty. No listings were parsed successfully.")
