from pathlib import Path
from urllib.parse import urljoin
import re
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.fondationdefrance.org"
START_URL = "https://www.fondationdefrance.org/fr/tag-pa"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "Database" / "FdF_database"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def clean_filename(name, max_length=120):
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = name.replace("’", "'").replace("«", "").replace("»", "")
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > max_length:
        name = name[:max_length].rstrip()
    return name

def make_unique_filepath(directory, filename):
    path = directory / filename
    stem = path.stem
    suffix = path.suffix
    counter = 1

    while path.exists():
        path = directory / f"{stem}_{counter}{suffix}"
        counter += 1

    return path

def normalize_text(text):
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_soup(url, session):
    response = session.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def extract_listing_links(soup):
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(BASE_URL, href)

        if full_url.startswith(BASE_URL) and "/fr/" in full_url and full_url != START_URL:
            links.add(full_url)

    return sorted(links)

def find_next_page(current_url, soup):
    current_start = 0
    match = re.search(r"start=(\d+)", current_url)
    if match:
        current_start = int(match.group(1))

    candidates = []

    for a in soup.find_all("a", href=True):
        href = urljoin(BASE_URL, a["href"].strip())
        if not href.startswith(START_URL):
            continue

        match = re.search(r"start=(\d+)", href)
        if match:
            start_value = int(match.group(1))
            if start_value > current_start:
                candidates.append((start_value, href))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]

def extract_article_content(article_url, session):
    soup = get_soup(article_url, session)

    title_tag = soup.find("h1")
    title = title_tag.get_text(" ", strip=True) if title_tag else "Sans titre"

    paragraphs = []
    for tag in soup.find_all(["p", "h2", "h3", "li"]):
        text = normalize_text(tag.get_text(" ", strip=True))
        if text:
            paragraphs.append(text)

    body = "\n".join(paragraphs)

    return title, body

def save_article(title, body, article_url):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename = clean_filename(title) + ".txt"
    filepath = make_unique_filepath(OUTPUT_DIR, filename)

    content = f"{title}\n\n{article_url}\n\n{body}\n"
    filepath.write_text(content, encoding="utf-8")

    print(f"[SAVE] {filepath.name}")

def main():
    session = requests.Session()

    visited_listing_pages = set()
    visited_article_urls = set()

    current_url = START_URL
    total_saved = 0

    while current_url and current_url not in visited_listing_pages:
        print(f"[LIST PAGE] {current_url}")
        visited_listing_pages.add(current_url)

        soup = get_soup(current_url, session)
        links = extract_listing_links(soup)

        for article_url in links:
            if article_url in visited_article_urls:
                continue

            visited_article_urls.add(article_url)

            try:
                title, body = extract_article_content(article_url, session)

                if not body:
                    continue

                save_article(title, body, article_url)
                total_saved += 1
                time.sleep(0.3)

            except Exception as e:
                print(f"[ERROR] {article_url} -> {e}")

        current_url = find_next_page(current_url, soup)

    print(f"[END] {total_saved} article(s) sauvegardé(s).")

if __name__ == "__main__":
    main()