from __future__ import annotations

import csv
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "Database"

OUTPUT_DIR = DATABASE_DIR / "iresp_autonomie_database"
REJECTED_DIR = PROJECT_ROOT / "temp" / "iresp_rejected"

REPORT_CSV = PROJECT_ROOT / "Scripts" / "iresp_autonomie_report.csv"

LIST_URL = "https://iresp.net/projets-finances/"
BASE_URL = "https://iresp.net"

REQUEST_DELAY = 0.3


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str, max_length: int = 120) -> str:
    text = strip_accents(text.lower())
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return (text or "sans_titre")[:max_length]


def get_soup(url: str) -> BeautifulSoup:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def remove_unwanted_blocks(soup: BeautifulSoup) -> None:
    for tag in soup(["script", "style", "nav", "header", "footer", "form", "aside"]):
        tag.decompose()


def is_project_link(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc == "iresp.net"
        and parsed.path.startswith("/projets_finances/")
        and parsed.path.rstrip("/") != "/projets_finances"
    )


def collect_project_links() -> list[str]:
    soup = get_soup(LIST_URL)
    links = set()

    for a in soup.find_all("a", href=True):
        url = urljoin(BASE_URL, a["href"]).split("#")[0]
        if is_project_link(url):
            links.add(url)

    return sorted(links)


def extract_text_lines(soup: BeautifulSoup) -> list[str]:
    remove_unwanted_blocks(soup)
    main = soup.find("main") or soup

    lines = []
    for line in main.get_text("\n").splitlines():
        line = clean_text(line)
        if line:
            lines.append(line)

    return lines


def get_value_after_label(lines: list[str], label: str) -> str:
    label_norm = clean_text(label).lower()

    for i, line in enumerate(lines):
        if clean_text(line).lower() == label_norm and i + 1 < len(lines):
            return lines[i + 1]

    return ""


def is_autonomie_project(lines: list[str]) -> bool:
    programme = get_value_after_label(lines, "Programme concerné")
    return strip_accents(programme.lower()) == "autonomie"


def extract_project(url: str) -> dict:
    soup = get_soup(url)
    lines = extract_text_lines(soup)

    title_tag = soup.find("h1")
    title = clean_text(title_tag.get_text(" ")) if title_tag else "sans titre"

    return {
        "title": title,
        "url": url,
        "programme": get_value_after_label(lines, "Programme concerné"),
        "appel": get_value_after_label(lines, "Nom de l'appel"),
        "annee": get_value_after_label(lines, "Année"),
        "etat": get_value_after_label(lines, "État du projet"),
        "duree": get_value_after_label(lines, "Durée"),
        "subvention": get_value_after_label(lines, "Subvention allouée"),
        "financeurs": get_value_after_label(lines, "Financeurs"),
        "disciplines": get_value_after_label(lines, "Disciplines"),
        "text": "\n".join(lines),
        "is_autonomie": is_autonomie_project(lines),
    }


def save_project(project: dict, index: int, directory: Path, status: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)

    year = project["annee"] or "annee_inconnue"
    filename = f"{index:03d}_{year}_{slugify(project['title'])}.txt"
    path = directory / filename

    content = (
        f"{project['title']}\n\n"
        f"Statut tri : {status}\n"
        f"Source : IReSP\n"
        f"URL : {project['url']}\n"
        f"Programme concerné : {project['programme']}\n"
        f"Nom de l'appel : {project['appel']}\n"
        f"Année : {project['annee']}\n"
        f"État du projet : {project['etat']}\n"
        f"Durée : {project['duree']}\n"
        f"Subvention allouée : {project['subvention']}\n"
        f"Financeurs : {project['financeurs']}\n"
        f"Disciplines : {project['disciplines']}\n\n"
        f"{project['text']}"
    )

    path.write_text(content, encoding="utf-8")
    return path


def write_report(rows: list[dict]) -> None:
    fieldnames = [
        "status",
        "title",
        "url",
        "programme",
        "appel",
        "annee",
        "etat",
        "duree",
        "subvention",
        "financeurs",
        "disciplines",
        "path",
    ]

    with REPORT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nURL cible : {LIST_URL}")
    print(f"Dossier acceptés : {OUTPUT_DIR}")
    print(f"Dossier rejetés  : {REJECTED_DIR}")

    links = collect_project_links()
    print(f"\nNombre total de liens projets trouvés : {len(links)}\n")

    rows = []
    accepted = 0
    rejected = 0
    errors = 0

    for i, url in enumerate(links, start=1):
        try:
            print(f"[{i}/{len(links)}] {url}")

            project = extract_project(url)

            if project["is_autonomie"]:
                accepted += 1
                status = "accepted"
                path = save_project(project, accepted, OUTPUT_DIR, status)
                print(f"    OK AUTONOMIE -> {path}:1")
            else:
                rejected += 1
                status = "rejected"
                path = save_project(project, rejected, REJECTED_DIR, status)
                print(f"    REJETÉ -> {path}:1")

            rows.append({
                "status": status,
                "title": project["title"],
                "url": project["url"],
                "programme": project["programme"],
                "appel": project["appel"],
                "annee": project["annee"],
                "etat": project["etat"],
                "duree": project["duree"],
                "subvention": project["subvention"],
                "financeurs": project["financeurs"],
                "disciplines": project["disciplines"],
                "path": str(path),
            })

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            errors += 1
            print(f"    ERREUR : {e}")

    write_report(rows)

    print("\nTerminé.")
    print(f"Projets Autonomie créés : {accepted}")
    print(f"Projets rejetés         : {rejected}")
    print(f"Erreurs                 : {errors}")
    print(f"Rapport                 : {REPORT_CSV}")


if __name__ == "__main__":
    main()