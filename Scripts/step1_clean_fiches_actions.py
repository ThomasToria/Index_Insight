from pathlib import Path
import re

PROJECT_ROOT = Path(r"C:\Users\PC\Desktop\Project_Internship\Index_Insight")

INPUT_DIR = PROJECT_ROOT / "Database"
OUTPUT_DIR = PROJECT_ROOT / "Cleaned_Database"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"Page\s+\d+(\s*/\s*\d+)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()

def main():
    txt_files = list(INPUT_DIR.rglob("*.txt"))

    if not txt_files:
        print(f"Aucun fichier .txt trouvé dans : {INPUT_DIR}")
        return

    print(f"{len(txt_files)} fichier(s) trouvé(s).")

    for txt_file in txt_files:
        try:
            text = txt_file.read_text(encoding="utf-8", errors="ignore")
            cleaned = clean_text(text)

            relative_path = txt_file.relative_to(INPUT_DIR)
            output_file = OUTPUT_DIR / relative_path

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(cleaned, encoding="utf-8")

            print(f"Nettoyé : {relative_path}")

        except Exception as e:
            print(f"Erreur avec {txt_file} : {e}")

    print("\nNettoyage terminé.")
    print(f"Dossier de sortie : {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
    