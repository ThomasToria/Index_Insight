from pathlib import Path
from zipfile import ZipFile
from lxml import etree # type: ignore
from pypdf import PdfReader # type: ignore
import re
import unicodedata
import csv


INPUT_DIR = Path("fiches_actions")
OUTPUT_DIR = Path("corpus_txt")
OUTPUT_DIR.mkdir(exist_ok=True)

CSV_PATH = Path("index_fiches.csv")

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\t", " ")
    text = re.sub(r"[ ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_duplicate_lines(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    seen = set()

    for line in lines:
        if not line:
            continue

        normalized_line = re.sub(r"\s+", " ", line).strip()

        if normalized_line not in seen:
            cleaned.append(normalized_line)
            seen.add(normalized_line)

    return "\n".join(cleaned)


def clean_filename(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\- ]+", "", name)
    return name.strip().replace(" ", "_")


def extract_docx_text(docx_path: Path) -> str:
    with ZipFile(docx_path) as z:
        xml_content = z.read("word/document.xml")

    root = etree.fromstring(xml_content)

    paragraphs = []

    for p in root.xpath(".//w:p", namespaces=NS):
        texts = p.xpath(".//w:t", namespaces=NS)
        if not texts:
            continue

        paragraph_text = "".join(t.text for t in texts if t.text)
        paragraph_text = normalize_text(paragraph_text)

        if paragraph_text:
            paragraphs.append(paragraph_text)

    text = "\n".join(paragraphs)
    text = normalize_text(text)
    text = remove_duplicate_lines(text)

    return text


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages_text = []

    for i, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""

        page_text = normalize_text(page_text)

        if page_text:
            pages_text.append(f"--- PAGE {i} ---\n{page_text}")

    text = "\n\n".join(pages_text)
    text = normalize_text(text)
    text = remove_duplicate_lines(text)

    return text


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".docx":
        return extract_docx_text(file_path)

    if suffix == ".pdf":
        return extract_pdf_text(file_path)

    raise ValueError(f"Format non pris en charge : {suffix}")


def process_file(file_path: Path):
    text = extract_text(file_path)

    output_name = clean_filename(file_path.stem) + ".txt"
    output_path = OUTPUT_DIR / output_name

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "source_file": file_path.name,
        "source_type": file_path.suffix.lower(),
        "txt_file": output_name,
        "char_count": len(text),
        "word_count": len(text.split()),
        "category": "",
        "text": text
    }


def main():
    files = sorted(
        [
            p for p in INPUT_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in {".docx", ".pdf"}
        ]
    )

    print("INPUT_DIR =", INPUT_DIR.resolve())
    print("OUTPUT_DIR =", OUTPUT_DIR.resolve())
    print("CSV_PATH =", CSV_PATH.resolve())

    if not files:
        print(f"Aucun fichier .docx ou .pdf trouvé dans : {INPUT_DIR.resolve()}")
        return

    rows = []

    for file_path in files:
        try:
            print(f"\n--- Traitement de : {file_path.resolve()} ---")
            row = process_file(file_path)
            rows.append(row)
            print(f"[OK] {file_path.name} -> {row['txt_file']} ({row['char_count']} caractères)")
        except Exception as e:
            print(f"[ERREUR] {file_path.name} : {e}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_file",
                "source_type",
                "txt_file",
                "char_count",
                "word_count",
                "category",
                "text",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV créé : {CSV_PATH.resolve()}")
    print("Traitement terminé.")


if __name__ == "__main__":
    main()