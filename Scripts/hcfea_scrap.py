from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin, urlparse
import csv
import re
import time

import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore


BASE_LIST_URL = "https://hcfea.gouv.fr/conseil-de-lage-0"
BASE_DOMAIN = "https://hcfea.gouv.fr"

OUTPUT_DIR = Path("hcfea_scraping")
ARTICLES_DIR = OUTPUT_DIR / "articles_txt"
PDF_DIR = OUTPUT_DIR / "pdfs"
CSV_PATH = OUTPUT_DIR / "index_hcfea_conseil_age.csv"

ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; M2-NLP-Scraper/1.0)"
}


def clean_filename(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:180]


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def collect_listing_pages() -> list[str]:
    return [f"{BASE_LIST_URL}?page={i}&sort_by=field_ref_modification_date_value&sort_order=DESC" for i in range(6)]


def collect_article_links(listing_url: str) -> list[str]:
    soup = get_soup(listing_url)
    links = []

    for a in soup.select("h2 a, h3 a"):
        href = a.get("href")
        if not href:
            continue

        full_url = urljoin(BASE_DOMAIN, href)

        if full_url.startswith(BASE_DOMAIN) and full_url not in links:
            links.append(full_url)

    return links


def extract_article_data(article_url: str) -> dict:
    soup = get_soup(article_url)

    title_tag = soup.select_one("h1")
    title = normalize_text(title_tag.get_text(" ", strip=True)) if title_tag else ""

    subtitle_tag = soup.select_one("h2")
    subtitle = normalize_text(subtitle_tag.get_text(" ", strip=True)) if subtitle_tag else ""

    published_text = ""
    for tag in soup.find_all(["p", "div"]):
        txt = tag.get_text(" ", strip=True)
        if "Publié le" in txt:
            published_text = normalize_text(txt)
            break

    body_parts = []
    for p in soup.select("main p, article p"):
        txt = normalize_text(p.get_text(" ", strip=True))
        if not txt:
            continue
        if txt.lower().startswith(("imprimer", "courriel", "linkedin", "facebook", "twitter", "bluesky")):
            continue
        body_parts.append(txt)

    body_text = "\n\n".join(dict.fromkeys(body_parts))

    pdf_links = []
    for a in soup.select('a[href$=".pdf"], a'):
        href = a.get("href")
        if not href:
            continue
        full_url = urljoin(BASE_DOMAIN, href)
        if full_url.lower().endswith(".pdf") and full_url not in pdf_links:
            pdf_links.append(full_url)

    return {
        "article_url": article_url,
        "title": title,
        "subtitle": subtitle,
        "published": published_text,
        "text": body_text,
        "pdf_links": pdf_links,
    }


def download_pdf(pdf_url: str, output_dir: Path) -> str:
    parsed = urlparse(pdf_url)
    filename = Path(parsed.path).name
    filename = clean_filename(filename) or "document.pdf"
    output_path = output_dir / filename

    if not output_path.exists():
        resp = requests.get(pdf_url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)

    return output_path.name


def save_article_text(article: dict, output_dir: Path) -> str:
    safe_title = clean_filename(article["title"]) or "article"
    txt_name = f"{safe_title}.txt"
    txt_path = output_dir / txt_name

    content = [
        f"Titre : {article['title']}",
        f"Sous-titre : {article['subtitle']}",
        f"Publication : {article['published']}",
        f"URL : {article['article_url']}",
        "",
        article["text"],
    ]
    txt_path.write_text("\n".join(content), encoding="utf-8")
    return txt_name


def main() -> None:
    all_article_urls = []

    listing_pages = collect_listing_pages()
    print(f"{len(listing_pages)} pages de listing à parcourir.")

    for listing_url in listing_pages:
        try:
            print(f"[LISTING] {listing_url}")
            links = collect_article_links(listing_url)
            for link in links:
                if link not in all_article_urls:
                    all_article_urls.append(link)
            time.sleep(0.5)
        except Exception as e:
            print(f"[ERREUR LISTING] {listing_url} -> {e}")

    print(f"{len(all_article_urls)} article(s) trouvé(s).")

    rows = []

    for i, article_url in enumerate(all_article_urls, start=1):
        try:
            print(f"[ARTICLE {i}/{len(all_article_urls)}] {article_url}")
            article = extract_article_data(article_url)

            txt_file = save_article_text(article, ARTICLES_DIR)

            downloaded_pdfs = []
            for pdf_url in article["pdf_links"]:
                try:
                    pdf_file = download_pdf(pdf_url, PDF_DIR)
                    downloaded_pdfs.append(pdf_file)
                    time.sleep(0.3)
                except Exception as e:
                    print(f"  [ERREUR PDF] {pdf_url} -> {e}")

            rows.append({
                "title": article["title"],
                "subtitle": article["subtitle"],
                "published": article["published"],
                "article_url": article["article_url"],
                "txt_file": txt_file,
                "pdf_count": len(downloaded_pdfs),
                "pdf_files": " | ".join(downloaded_pdfs),
                "pdf_urls": " | ".join(article["pdf_links"]),
                "char_count": len(article["text"]),
                "word_count": len(article["text"].split()),
            })

            time.sleep(0.5)

        except Exception as e:
            print(f"[ERREUR ARTICLE] {article_url} -> {e}")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "subtitle",
                "published",
                "article_url",
                "txt_file",
                "pdf_count",
                "pdf_files",
                "pdf_urls",
                "char_count",
                "word_count",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV créé : {CSV_PATH.resolve()}")
    print(f"TXT dans : {ARTICLES_DIR.resolve()}")
    print(f"PDF dans : {PDF_DIR.resolve()}")


if __name__ == "__main__":
    main()