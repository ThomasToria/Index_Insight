import os
import re

MAX_FILENAME_LENGTH = 50

def clean_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.replace('’', '').replace('«', '').replace('»', '')
    name = name.strip()
    return name

def shorten_filename(filename, max_length=MAX_FILENAME_LENGTH):
    name, ext = os.path.splitext(filename)
    name = clean_filename(name)

    if len(name) <= max_length:
        return name + ext

    return name[:max_length] + ext

def make_unique(path, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(os.path.join(path, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1

    return new_filename

def process_directory(root_dir, renamed_files):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if not filename.lower().endswith(".txt"):
                continue

            old_path = os.path.join(dirpath, filename)
            new_filename = shorten_filename(filename)

            if new_filename != filename:
                new_filename = make_unique(dirpath, new_filename)
                new_path = os.path.join(dirpath, new_filename)
                os.rename(old_path, new_path)
                renamed_files.append((old_path, new_path))

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    renamed_files = []

    for folder in ["temp", "Database"]:
        target = os.path.join(base_dir, folder)
        if os.path.exists(target):
            process_directory(target, renamed_files)

    if renamed_files:
        print("\nFICHIERS MODIFIÉS :\n")
        for old_path, new_path in renamed_files:
            print(f"{old_path}")
            print(f"-> {new_path}\n")
        print(f"Total : {len(renamed_files)} fichier(s) renommé(s).")
    else:
        print("Aucun fichier renommé.")