from pathlib import Path
import csv
import re
import unicodedata
import requests # type: ignore
from pypdf import PdfReader # type: ignore


PDF_URL = "https://www.lassuranceretraite.fr/portail-info/files/live/sites/pub/files/PDF/pepites-assurance-retraite-pour-bien-vieillir-2023.pdf"

BASE_DIR = Path(__file__).resolve().parent.parent
WORK_DIR = BASE_DIR / "cnav_scrapping"
PDF_DIR = WORK_DIR / "pdf"
PDF_PATH = PDF_DIR / "pepites-assurance-retraite-pour-bien-vieillir-2023.pdf"
OUTPUT_DIR = WORK_DIR / "articles_txt"
CSV_PATH = WORK_DIR / "index_articles.csv"

WORK_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; M2-NLP-Scraper/1.0)"
}

SECTION_MARKERS = [
    "LES ACTEURS",
    "LA CIBLE",
    "LA FINALITÉ",
    "LA DESCRIPTION DE LA PÉPITE",
    "LA TEMPORALITÉ",
    "LA LOCALISATION",
]

NOISE_PATTERNS = [
    r"^LES PÉPITES DE L[’']ASSURANCE RETRAITE POUR BIEN VIEILLIR\s*\d*$",
    r"^LES PÉPITES DE L[’'] ASSURANCE RETRAITE POUR BIEN VIEILLIR\s*\d*$",
    r"^\d+$",
    r"^SOMMAIRE$",
    r"^AVANT-PROPOS$",
    r"^PÉPITES NATIONALES$",
    r"^PÉPITES RÉGIONALES$",
    r"^CAISSE NATIONALE$",
    r"^Actions collectives$",
    r"^Adapter la société, la ville au bien-vieillir$",
    r"^Adapter son habitat et cadre de vie pour bien vieillir$",
    r"^Adapter ses habitudes pour bien vieillir$",
    r"^Accompagner les plus fragiles et précaires dans leur bien-vieillir à domicile$",
]


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
    return name[:180] or "article"


def download_pdf(url: str, output_path: Path) -> None:
    if output_path.exists():
        return
    response = requests.get(url, headers=HEADERS, timeout=120)
    response.raise_for_status()
    output_path.write_bytes(response.content)


def extract_pages(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        text = normalize_text(text)
        pages.append(text)

    return pages


def is_noise_line(line: str) -> bool:
    s = normalize_text(line)
    if not s:
        return True

    for pattern in NOISE_PATTERNS:
        if re.fullmatch(pattern, s, flags=re.IGNORECASE):
            return True

    if re.fullmatch(r".*BIEN VIEILLIR\s*\d*$", s, flags=re.IGNORECASE):
        return True

    return False


def detect_article_start(page_text: str) -> tuple[bool, str]:
    if "LES ACTEURS" not in page_text or "LA CIBLE" not in page_text:
        return False, ""

    lines = [normalize_text(l) for l in page_text.splitlines() if normalize_text(l)]

    idx_acteurs = None
    for i, line in enumerate(lines):
        if line == "LES ACTEURS":
            idx_acteurs = i
            break

    if idx_acteurs is None or idx_acteurs == 0:
        return False, ""

    candidate_lines = []
    for line in lines[:idx_acteurs]:
        if is_noise_line(line):
            continue
        if line in SECTION_MARKERS:
            continue
        if line.isdigit():
            continue
        if len(line) < 3:
            continue
        candidate_lines.append(line)

    if not candidate_lines:
        return False, ""

    if len(candidate_lines) >= 2:
        title_lines = candidate_lines[-2:]
    else:
        title_lines = candidate_lines

    title = " ".join(title_lines)
    title = normalize_text(title)

    return (len(title) >= 5, title)


def split_articles(pages: list[str]) -> list[dict]:
    articles = []
    current = None

    for page_num, page_text in enumerate(pages, start=1):
        is_start, title = detect_article_start(page_text)

        if is_start:
            if current is not None:
                articles.append(current)

            current = {
                "title": title,
                "pages": [page_num],
                "text_parts": [page_text],
            }
        else:
            if current is not None:
                current["pages"].append(page_num)
                current["text_parts"].append(page_text)

    if current is not None:
        articles.append(current)

    return articles


def deduplicate_lines_keep_order(text: str) -> str:
    lines = [normalize_text(l) for l in text.splitlines()]
    output = []
    seen = set()

    for line in lines:
        if not line:
            continue
        if line not in seen:
            output.append(line)
            seen.add(line)

    return "\n".join(output)


def clean_article_text(text: str, title: str) -> str:
    text = normalize_text(text)

    for marker in SECTION_MARKERS:
        text = re.sub(rf"\s*{re.escape(marker)}\s*", f"\n{marker}\n", text)

    text = re.sub(r"\s*(Actions collectives)\s*", r"\n\1\n", text)
    text = re.sub(r"\s*(CAISSE NATIONALE)\s*", r"\n\1\n", text)

    lines = [normalize_text(l) for l in text.splitlines() if normalize_text(l)]

    cleaned = []
    for line in lines:
        if re.fullmatch(r"\d+", line):
            continue
        if re.fullmatch(r"LES PÉPITES DE L[’'] ?ASSURANCE RETRAITE POUR BIEN VIEILLIR\s*\d*", line, flags=re.IGNORECASE):
            continue
        if is_noise_line(line) and line != title:
            continue
        cleaned.append(line)

    text = "\n".join(cleaned)
    text = deduplicate_lines_keep_order(text)

    title_pattern = re.escape(title)
    text = re.sub(rf"^(?:{title_pattern}\s*)+", title + "\n", text, flags=re.IGNORECASE)

    return normalize_text(text)


def save_articles(articles: list[dict], output_dir: Path) -> list[dict]:
    rows = []

    for i, article in enumerate(articles, start=1):
        full_text = "\n\n".join(article["text_parts"])
        full_text = clean_article_text(full_text, article["title"])

        filename = f"{i:02d}_{clean_filename(article['title'])}.txt"
        output_path = output_dir / filename

        content = [
            f"Titre : {normalize_text(article['title'])}",
            f"Pages : {', '.join(map(str, article['pages']))}",
            "",
            full_text,
        ]

        output_path.write_text("\n".join(content), encoding="utf-8")

        rows.append({
            "id": i,
            "title": article["title"],
            "pages": "-".join(map(str, article["pages"])),
            "txt_file": filename,
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
        })

    return rows


def save_index(rows: list[dict], csv_path: Path) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "title", "pages", "txt_file", "char_count", "word_count"]
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    download_pdf(PDF_URL, PDF_PATH)

    pages = extract_pages(PDF_PATH)
    articles = split_articles(pages)

    print(f"{len(articles)} fiche(s) détectée(s).")
    for i, article in enumerate(articles, start=1):
        print(f"{i:02d}. {article['title']}")

    rows = save_articles(articles, OUTPUT_DIR)
    save_index(rows, CSV_PATH)

    print(f"PDF : {PDF_PATH.resolve()}")
    print(f"TXT créés dans : {OUTPUT_DIR.resolve()}")
    print(f"Index CSV : {CSV_PATH.resolve()}")


if __name__ == "__main__":
    main()