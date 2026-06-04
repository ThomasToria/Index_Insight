from pathlib import Path

DATABASE_PATH = r"C:\Users\PC\Desktop\Project_Internship\Index_Insight\Database"

txt_files = list(Path(DATABASE_PATH).rglob("*.txt"))

word_counts = []

for file_path in txt_files:
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        words = text.split()
        word_counts.append(len(words))

    except Exception as e:
        print(f"Erreur avec {file_path.name} : {e}")

if not word_counts:
    print("Aucun fichier trouvé.")
    exit()

min_words = min(word_counts)
max_words = max(word_counts)
avg_words = sum(word_counts) / len(word_counts)

print("\n===== STATISTIQUES DATABASE =====")
print(f"Nombre de fichiers analysés : {len(word_counts)}")
print(f"Nombre minimum de mots : {min_words}")
print(f"Nombre maximum de mots : {max_words}")
print(f"Nombre moyen de mots : {avg_words:.2f}")