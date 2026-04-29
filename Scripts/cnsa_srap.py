from __future__ import annotations

import csv
import re
import time
import unicodedata
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "Database"
CNSA_DIR = DATABASE_DIR / "cnsa_database"
REJECTED_DIR = PROJECT_ROOT / "temp" / "cnsa_rejected"
REPORT_CSV = PROJECT_ROOT / "Scripts" / "cnsa_scraping_report.csv"

START_URL = "https://www.cnsa.fr/appels-projets?keywords=&close=today&type%5B0%5D=126"
BASE_URL = "https://www.cnsa.fr"

MIN_WORDS = 50
PERCENTILE = 5
REQUEST_DELAY = 0.5

KEYWORDS = OrderedDict({
    "agisme": 5,
    "ville amie des aines": 5,
    "vada": 5,
    "vieillissement": 3,
    "personnes agees": 3,
    "aines": 3,
    "seniors": 3,
    "retraites": 3,
    "vieillir": 3,
    "retraite": 3,
    "intergenerationnel": 3,
    "chez soi": 1,
    "ehpad": 1,
    "mobilite": 1,
    "hebergement": 1,
    "autonomie": 1,
    "citoyennete": 1,
    "isole": 1,
})


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def normalize_text(text: str) -> str:
    text = text.lower()
    text = strip_accents(text)
    text = text.replace("’", "'").replace("`", "'")
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("-", " ")
    text = text.replace("'", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_words(text: str) -> int:
    normalized = normalize_text(text)
    return len(normalized.split()) if normalized else 0


def build_keyword_pattern(keyword: str) -> re.Pattern:
    tokens = keyword.split()

    if keyword == "isole":
        return re.compile(r"\bisol\w*\b", re.IGNORECASE)

    if len(tokens) == 1:
        return re.compile(rf"\b{re.escape(tokens[0])}\b", re.IGNORECASE)

    pattern = r"\b" + r"\s+".join(re.escape(t) for t in tokens) + r"\b"
    return re.compile(pattern, re.IGNORECASE)


KEYWORD_PATTERNS = {
    keyword: build_keyword_pattern(keyword)
    for keyword in KEYWORDS
}


def score_text(text: str, title: str) -> dict:
    normalized = normalize_text(text)
    normalized_title = normalize_text(title)

    word_count = count_words(text)
    score_raw = 0

    for keyword, weight in KEYWORDS.items():
        pattern = KEYWORD_PATTERNS[keyword]
        count = len(pattern.findall(normalized))
        title_bonus = 2 if pattern.search(normalized_title) else 0
        score_raw += count * weight + title_bonus

    score_normalized = score_raw / word_count if word_count > 0 else 0.0

    return {
        "word_count": word_count,
        "score_raw": score_raw,
        "score_normalized": score_normalized,
    }


def compute_reference_threshold() -> float:
    scores = []

    for txt_file in DATABASE_DIR.rglob("*.txt"):
        if "cnsa_database" in txt_file.parts:
            continue

        try:
            text = txt_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        result = score_text(text, txt_file.stem)

        if result["word_count"] >= MIN_WORDS:
            scores.append(result["score_normalized"])

    if not scores:
        return 0.0

    scores = sorted(scores)
    index = int(len(scores) * PERCENTILE / 100)
    index = min(index, len(scores) - 1)

    return scores[index]


def get_soup(url: str) -> BeautifulSoup:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str, max_length: int = 120) -> str:
    text = strip_accents(text.lower())
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return (text or "sans_titre")[:max_length]


def is_project_url(url: str) -> bool:
    parsed = urlparse(url)

    if parsed.netloc != "www.cnsa.fr":
        return False

    if not parsed.path.startswith("/appels-projets/"):
        return False

    if parsed.path.rstrip("/") == "/appels-projets":
        return False

    return True


def extract_project_links_from_listing(soup: BeautifulSoup) -> list[str]:
    links = set()

    main = soup.find("main") or soup

    for h2 in main.find_all("h2"):
        a = h2.find("a", href=True)
        if not a:
            continue

        full_url = urljoin(BASE_URL, a["href"]).split("#")[0]

        if is_project_url(full_url):
            links.add(full_url)

    return sorted(links)


def find_next_page(soup: BeautifulSoup, current_url: str) -> str | None:
    main = soup.find("main") or soup

    for a in main.find_all("a", href=True):
        label = clean_text(a.get_text(" ")).lower()

        if "suivant" in label:
            return urljoin(current_url, a["href"])

    return None


def collect_all_project_links() -> list[str]:
    all_links = []
    seen_pages = set()
    seen_links = set()
    current_url = START_URL

    while current_url and current_url not in seen_pages:
        print(f"Page liste : {current_url}")

        seen_pages.add(current_url)
        soup = get_soup(current_url)

        links = extract_project_links_from_listing(soup)

        print(f"  liens projets trouvés sur cette page : {len(links)}")

        for link in links:
            if link not in seen_links:
                seen_links.add(link)
                all_links.append(link)

        next_page = find_next_page(soup, current_url)

        if next_page and next_page not in seen_pages:
            current_url = next_page
            time.sleep(REQUEST_DELAY)
        else:
            current_url = None

    return all_links


def remove_unwanted_blocks(soup: BeautifulSoup) -> None:
    for tag in soup(["script", "style", "nav", "header", "footer", "form", "aside"]):
        tag.decompose()


def extract_project_text(url: str) -> tuple[str, str]:
    soup = get_soup(url)
    remove_unwanted_blocks(soup)

    title_tag = soup.find("h1")
    title = clean_text(title_tag.get_text(" ")) if title_tag else "sans titre"

    main = soup.find("main") or soup

    lines = []
    for line in main.get_text("\n").splitlines():
        line = clean_text(line)
        if line:
            lines.append(line)

    text = "\n".join(lines)

    return title, text


def save_txt(directory: Path, title: str, url: str, text: str, score_info: dict, status: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)

    filename = slugify(title) + ".txt"
    path = directory / filename

    counter = 2
    while path.exists():
        path = directory / f"{slugify(title)}_{counter}.txt"
        counter += 1

    content = (
        f"{title}\n\n"
        f"Statut tri : {status}\n"
        f"URL : {url}\n"
        f"Nombre de mots : {score_info['word_count']}\n"
        f"Score brut : {score_info['score_raw']}\n"
        f"Score normalisé : {score_info['score_normalized']:.8f}\n\n"
        f"{text}"
    )

    path.write_text(content, encoding="utf-8")
    return path


def write_report(rows: list[dict]) -> None:
    fieldnames = [
        "status",
        "title",
        "url",
        "path",
        "word_count",
        "score_raw",
        "score_normalized",
        "threshold",
    ]

    with REPORT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    CNSA_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    threshold = compute_reference_threshold()

    print(f"\nURL cible : {START_URL}")
    print(f"Seuil calculé : {threshold:.8f}")
    print(f"Dossier accepté : {CNSA_DIR}")
    print(f"Dossier rejeté  : {REJECTED_DIR}\n")

    project_links = collect_all_project_links()

    print(f"\nNombre total de projets trouvés : {len(project_links)}\n")

    report_rows = []
    accepted = 0
    rejected = 0
    errors = 0

    for i, url in enumerate(project_links, start=1):
        try:
            print(f"[{i}/{len(project_links)}] {url}")

            title, text = extract_project_text(url)
            result = score_text(text, title)

            is_acceptable = (
                result["word_count"] >= MIN_WORDS
                and result["score_normalized"] >= threshold
            )

            if is_acceptable:
                status = "accepted"
                path = save_txt(CNSA_DIR, title, url, text, result, status)
                accepted += 1
            else:
                status = "rejected"
                path = save_txt(REJECTED_DIR, title, url, text, result, status)
                rejected += 1

            report_rows.append({
                "status": status,
                "title": title,
                "url": url,
                "path": str(path),
                "word_count": result["word_count"],
                "score_raw": result["score_raw"],
                "score_normalized": f"{result['score_normalized']:.8f}",
                "threshold": f"{threshold:.8f}",
            })

            print(
                f"    {status.upper()} | "
                f"mots={result['word_count']} | "
                f"score_brut={result['score_raw']} | "
                f"score_norm={result['score_normalized']:.8f}"
            )

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            errors += 1
            print(f"    ERREUR : {e}")

    write_report(report_rows)

    print("\nTerminé.")
    print(f"Acceptés : {accepted}")
    print(f"Rejetés  : {rejected}")
    print(f"Erreurs  : {errors}")
    print(f"Rapport  : {REPORT_CSV}")


if __name__ == "__main__":
    main()