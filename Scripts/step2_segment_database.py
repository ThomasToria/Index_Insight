from pathlib import Path
import re
import json

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Cleaned_Database"
OUTPUT_DIR = PROJECT_ROOT / "Segmented_Database"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]

def split_paragraphs(text: str) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]

def split_sentences(text: str) -> list[str]:
    text = text.replace("\n", " ")
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÉÈÀÂÊÎÔÛÇ0-9])", text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def segment_file(txt_path: Path) -> dict:
    text = txt_path.read_text(encoding="utf-8", errors="ignore")

    lines = split_lines(text)
    paragraphs = split_paragraphs(text)
    sentences = split_sentences(text)

    return {
        "fichier_source": str(txt_path),
        "nom_fichier": txt_path.name,
        "lignes": lines,
        "paragraphes": paragraphs,
        "phrases": sentences,
        "stats": {
            "nombre_lignes": len(lines),
            "nombre_paragraphes": len(paragraphs),
            "nombre_phrases": len(sentences),
            "nombre_caracteres": len(text)
        }
    }

def main():
    txt_files = list(INPUT_DIR.rglob("*.txt"))

    if not txt_files:
        print(f"Aucun fichier .txt trouvé dans : {INPUT_DIR}")
        return

    print(f"{len(txt_files)} fichier(s) trouvé(s).")

    for txt_file in txt_files:
        try:
            segmented_data = segment_file(txt_file)

            relative_path = txt_file.relative_to(INPUT_DIR)
            output_file = OUTPUT_DIR / relative_path.with_suffix(".json")
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open("w", encoding="utf-8") as f:
                json.dump(segmented_data, f, ensure_ascii=False, indent=4)

            print(f"Segmenté : {relative_path}")

        except Exception as e:
            print(f"Erreur avec {txt_file} : {e}")

    print("\nSegmentation terminée.")
    print(f"Dossier de sortie : {OUTPUT_DIR}")

if __name__ == "__main__":
    main()