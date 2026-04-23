from pathlib import Path
from urllib.parse import urljoin, urlparse
import csv
import re
import unicodedata
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader


BASE_URL = "https://www.villesamiesdesaines-rf.fr/nos-fiches/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; M2-NLP-Scraper/1.0)"
}

BASE_DIR = Path(__file__).resolve().parents[1]
WORK_DIR = BASE_DIR / "Vada_database"
PDF_DIR = WORK_DIR / "pdf"
TXT_DIR = WORK_DIR / "txt"
CSV_PATH = WORK_DIR / "index_vada_61_80.csv"

WORK_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
TXT_DIR.mkdir(exist_ok=True)


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\t", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_filename(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\- ]+", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:180] or "fiche"


def get_soup(url: str) -> BeautifulSoup:
    print(f"[GET] {url}")
    response = requests.get(url, headers=HEADERS, timeout=60)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def collect_all_listing_pages(start_url: str, start: int = 60, max_pages: int = 20) -> list[str]:
    pages = []
    seen = set()
    current_url = start_url
    count = 0
    kept = 0

    while current_url and current_url not in seen:
        seen.add(current_url)

        if count >= start and kept < max_pages:
            print(f"[LISTING PAGE {count+1} → kept {kept+1}/{max_pages}] {current_url}")
            pages.append(current_url)
            kept += 1
        else:
            print(f"[SKIP PAGE {count+1}] {current_url}")

        soup = get_soup(current_url)
        next_url = None

        for a in soup.find_all("a", href=True):
            label = normalize_text(a.get_text(" ", strip=True)).lower()
            if "plus anciens" in label:
                next_url = urljoin(current_url, a["href"])
                break

        current_url = next_url
        count += 1

        if kept >= max_pages:
            break

    print(f"[TOTAL PAGES GARDÉES] {len(pages)}")
    return pages


def extract_cards_from_listing(listing_url: str) -> list[dict]:
    soup = get_soup(listing_url)
    cards = []

    for a in soup.find_all("a", href=True):
        label = normalize_text(a.get_text(" ", strip=True)).lower()
        href = urljoin(listing_url, a["href"])

        if "lire la fiche" not in label:
            continue

        if not href.lower().endswith(".pdf"):
            continue

        title = ""
        categories = ""
        commune = ""

        title_tag = a.find_previous(["h2", "h3"])
        if title_tag:
            title = normalize_text(title_tag.get_text(" ", strip=True))

        meta_lines = []
        for prev in title_tag.find_previous_siblings() if title_tag else []:
            txt = normalize_text(prev.get_text(" ", strip=True))
            if txt:
                meta_lines.append(txt)
            if prev.name in {"h2", "h3"}:
                break

        meta_lines = list(reversed(meta_lines))
        if meta_lines:
            categories = meta_lines[0]
        if len(meta_lines) > 1:
            commune = meta_lines[-1]

        cards.append({
            "title": title,
            "categories": categories,
            "commune": commune,
            "pdf_url": href,
            "listing_url": listing_url,
        })

    dedup = []
    seen_urls = set()
    for card in cards:
        if card["pdf_url"] not in seen_urls:
            dedup.append(card)
            seen_urls.add(card["pdf_url"])

    print(f"[FICHES TROUVÉES SUR PAGE] {len(dedup)}")
    return dedup


def download_pdf(pdf_url: str, output_dir: Path, title: str) -> str:
    parsed = urlparse(pdf_url)
    original_name = Path(parsed.path).name

    if title:
        filename = clean_filename(title) + ".pdf"
    else:
        filename = clean_filename(original_name) or "fiche.pdf"

    output_path = output_dir / filename

    if not output_path.exists():
        print("  ↓ Téléchargement PDF...")
        response = requests.get(pdf_url, headers=HEADERS, timeout=120)
        response.raise_for_status()
        output_path.write_bytes(response.content)
    else:
        print("  ✓ PDF déjà existant")

    return filename


def extract_text_from_pdf(pdf_path: Path) -> tuple[str, int]:
    reader = PdfReader(str(pdf_path))
    page_texts = []

    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = normalize_text(text)
        if text:
            page_texts.append(f"--- PAGE {i} ---\n{text}")

    return "\n\n".join(page_texts).strip(), len(reader.pages)


def save_txt(title: str, categories: str, commune: str, pdf_url: str, text: str, output_dir: Path) -> str:
    filename = clean_filename(title) + ".txt" if title else "fiche.txt"
    output_path = output_dir / filename

    content = [
        f"Titre : {title}",
        f"Catégories : {categories}",
        f"Commune : {commune}",
        f"Source PDF : {pdf_url}",
        "",
        text,
    ]

    output_path.write_text("\n".join(content), encoding="utf-8")
    return filename


def main() -> None:
    listing_pages = collect_all_listing_pages(BASE_URL, start=60, max_pages=20)

    all_cards = []
    seen_pdf_urls = set()

    for page_url in listing_pages:
        cards = extract_cards_from_listing(page_url)

        for card in cards:
            if card["pdf_url"] not in seen_pdf_urls:
                all_cards.append(card)
                seen_pdf_urls.add(card["pdf_url"])

    print(f"\n[TOTAL FICHES] {len(all_cards)}\n")

    rows = []

    for i, card in enumerate(all_cards, start=1):
        print(f"[{i}/{len(all_cards)}] {card['title'] or 'Sans titre'}")

        try:
            pdf_filename = download_pdf(card["pdf_url"], PDF_DIR, card["title"])
            pdf_path = PDF_DIR / pdf_filename

            print(f"  → Extraction texte ({pdf_filename})")
            text, page_count = extract_text_from_pdf(pdf_path)
            print(f"  → {page_count} page(s)")

            txt_filename = save_txt(
                card["title"],
                card["categories"],
                card["commune"],
                card["pdf_url"],
                text,
                TXT_DIR,
            )

            print(f"  → TXT créé : {txt_filename}\n")

            rows.append({
                "id": i,
                "title": card["title"],
                "categories": card["categories"],
                "commune": card["commune"],
                "listing_url": card["listing_url"],
                "pdf_url": card["pdf_url"],
                "pdf_file": pdf_filename,
                "txt_file": txt_filename,
                "page_count": page_count,
                "char_count": len(text),
                "word_count": len(text.split()),
            })

        except Exception as e:
            print(f"[ERREUR] {card['pdf_url']} -> {e}\n")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "title",
                "categories",
                "commune",
                "listing_url",
                "pdf_url",
                "pdf_file",
                "txt_file",
                "page_count",
                "char_count",
                "word_count",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== TERMINÉ ===")
    print(f"PDF : {PDF_DIR.resolve()}")
    print(f"TXT : {TXT_DIR.resolve()}")
    print(f"CSV : {CSV_PATH.resolve()}")


if __name__ == "__main__":
    main()