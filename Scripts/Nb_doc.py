from pathlib import Path

root = Path("Cleaned_Database\Vada_database")

txt_files = list(root.rglob("*.txt"))

print(f"Nombre total de fichiers txt : {len(txt_files)}")