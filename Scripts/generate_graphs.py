from pathlib import Path
import json
import re
from collections import Counter, defaultdict

import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]

LLM_DIR = BASE_DIR / "LLM_Tagged_Database"
OUTPUT_DIR = BASE_DIR / "outputs_graphs"
OUTPUT_EXCEL = OUTPUT_DIR / "stats_graphs.xlsx"

FICHES_ACTIONS_KEYWORD = "Fiches_actions_database"

TOP_N_THEMATIQUES = 15
TOP_N_PORTEURS = 20


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(value):
    if value is None:
        return ""

    value = str(value).strip().lower()
    value = re.sub(r"\s+", " ", value)

    return value


def extract_values(value):
    values = []

    if value is None:
        return values

    if isinstance(value, list):
        for item in value:
            values.extend(extract_values(item))

    elif isinstance(value, dict):
        for item in value.values():
            values.extend(extract_values(item))

    else:
        cleaned = normalize_text(value)
        if cleaned:
            values.append(cleaned)

    return values


def is_fiche_action(json_path):
    return FICHES_ACTIONS_KEYWORD.lower() in str(json_path).lower()


def get_years(value):
    years = []

    for item in extract_values(value):
        found = re.findall(r"\b(19\d{2}|20\d{2})\b", item)
        years.extend(found)

    return years


def collect_data():
    json_files = list(LLM_DIR.rglob("*.json"))

    rows = []

    for json_path in json_files:
        try:
            data = load_json(json_path)

            if not isinstance(data, dict):
                continue

            thematiques = extract_values(data.get("thematique"))
            natures = extract_values(data.get("nature_initiative"))
            porteurs = extract_values(data.get("porteur_initiative"))
            territoires = extract_values(data.get("territoire"))
            years = get_years(data.get("date"))

            if not thematiques:
                thematiques = ["non renseigné"]

            if not natures:
                natures = ["non renseigné"]

            if not porteurs:
                porteurs = ["non renseigné"]

            if not territoires:
                territoires = ["non renseigné"]

            if not years:
                years = ["non renseigné"]

            rows.append({
                "file": json_path.name,
                "path": str(json_path),
                "type_fiche": "fiche action" if is_fiche_action(json_path) else "autre fiche",
                "thematiques": thematiques,
                "natures": natures,
                "porteurs": porteurs,
                "territoires": territoires,
                "years": years
            })

        except Exception as e:
            print(f"Erreur avec {json_path.name} : {e}")

    return rows


def count_from_rows(rows, field, filter_type=None):
    counter = Counter()

    for row in rows:
        if filter_type is not None and row["type_fiche"] != filter_type:
            continue

        for value in row[field]:
            counter[value] += 1

    return counter


def save_bar_chart(counter, title, xlabel, ylabel, output_path, top_n=None):
    if top_n is not None:
        items = counter.most_common(top_n)
    else:
        items = counter.most_common()

    if not items:
        print(f"Aucune donnée pour : {title}")
        return

    labels = [item[0] for item in items]
    values = [item[1] for item in items]

    plt.figure(figsize=(12, max(6, len(labels) * 0.35)))
    plt.barh(labels[::-1], values[::-1])
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Graphe créé : {output_path}")


def save_comparison_thematiques(rows, output_path, top_n=15):
    counter_fa = count_from_rows(rows, "thematiques", "fiche action")
    counter_autres = count_from_rows(rows, "thematiques", "autre fiche")

    all_counter = counter_fa + counter_autres
    top_thematiques = [theme for theme, _ in all_counter.most_common(top_n)]

    data = []

    for theme in top_thematiques:
        data.append({
            "thematique": theme,
            "fiches_actions": counter_fa.get(theme, 0),
            "autres_fiches": counter_autres.get(theme, 0)
        })

    df = pd.DataFrame(data)

    if df.empty:
        print("Aucune donnée pour le comparatif thématique.")
        return

    x = range(len(df))

    plt.figure(figsize=(14, 7))
    plt.bar(
        [i - 0.2 for i in x],
        df["fiches_actions"],
        width=0.4,
        label="Fiches actions"
    )
    plt.bar(
        [i + 0.2 for i in x],
        df["autres_fiches"],
        width=0.4,
        label="Autres fiches"
    )

    plt.xticks(x, df["thematique"], rotation=45, ha="right")
    plt.title("Comparaison des thématiques : fiches actions vs autres fiches")
    plt.xlabel("Thématique")
    plt.ylabel("Nombre d'occurrences")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Graphe créé : {output_path}")

    return df


def save_pie_chart(counter, title, output_path):
    items = counter.most_common()

    if not items:
        print(f"Aucune donnée pour : {title}")
        return

    labels = [item[0] for item in items]
    values = [item[1] for item in items]

    plt.figure(figsize=(8, 8))
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Graphe créé : {output_path}")


def save_year_chart(counter, output_path):
    items = [
        (year, count)
        for year, count in counter.items()
        if year != "non renseigné"
    ]

    items = sorted(items, key=lambda x: x[0])

    if not items:
        print("Aucune année exploitable.")
        return

    years = [item[0] for item in items]
    counts = [item[1] for item in items]

    plt.figure(figsize=(12, 6))
    plt.plot(years, counts, marker="o")
    plt.title("Nombre de fiches par année")
    plt.xlabel("Année")
    plt.ylabel("Nombre d'occurrences")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Graphe créé : {output_path}")


def counter_to_dataframe(counter, value_column, count_column="occurrences"):
    return pd.DataFrame(
        counter.most_common(),
        columns=[value_column, count_column]
    )


def export_excel(rows, comparison_df=None):
    thematiques_counter = count_from_rows(rows, "thematiques")
    natures_counter = count_from_rows(rows, "natures")
    porteurs_counter = count_from_rows(rows, "porteurs")
    territoires_counter = count_from_rows(rows, "territoires")
    years_counter = count_from_rows(rows, "years")
    type_counter = Counter(row["type_fiche"] for row in rows)

    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="Données brutes", index=False)

        counter_to_dataframe(thematiques_counter, "thematique").to_excel(
            writer, sheet_name="Thématiques", index=False
        )

        counter_to_dataframe(natures_counter, "nature_initiative").to_excel(
            writer, sheet_name="Natures", index=False
        )

        counter_to_dataframe(porteurs_counter, "porteur_initiative").to_excel(
            writer, sheet_name="Porteurs", index=False
        )

        counter_to_dataframe(territoires_counter, "territoire").to_excel(
            writer, sheet_name="Territoires", index=False
        )

        counter_to_dataframe(years_counter, "année").to_excel(
            writer, sheet_name="Dates", index=False
        )

        counter_to_dataframe(type_counter, "type_fiche").to_excel(
            writer, sheet_name="Types fiches", index=False
        )

        if comparison_df is not None:
            comparison_df.to_excel(
                writer,
                sheet_name="Comparatif thématiques",
                index=False
            )

    print(f"Excel créé : {OUTPUT_EXCEL}")


def main():
    print("Collecte des données JSON...")

    OUTPUT_DIR.mkdir(exist_ok=True)

    rows = collect_data()

    if not rows:
        print("Aucune donnée exploitable.")
        return

    print(f"{len(rows)} fichiers JSON analysés.")

    thematiques_counter = count_from_rows(rows, "thematiques")
    natures_counter = count_from_rows(rows, "natures")
    porteurs_counter = count_from_rows(rows, "porteurs")
    territoires_counter = count_from_rows(rows, "territoires")
    years_counter = count_from_rows(rows, "years")
    type_counter = Counter(row["type_fiche"] for row in rows)

    save_bar_chart(
        thematiques_counter,
        f"Top {TOP_N_THEMATIQUES} des thématiques",
        "Nombre d'occurrences",
        "Thématique",
        OUTPUT_DIR / "top_thematiques.png",
        TOP_N_THEMATIQUES
    )

    save_bar_chart(
        natures_counter,
        "Répartition des natures d'initiative",
        "Nombre d'occurrences",
        "Nature d'initiative",
        OUTPUT_DIR / "nature_initiative.png"
    )

    save_bar_chart(
        porteurs_counter,
        f"Top {TOP_N_PORTEURS} des porteurs d'initiative",
        "Nombre d'occurrences",
        "Porteur d'initiative",
        OUTPUT_DIR / "top_porteurs.png",
        TOP_N_PORTEURS
    )

    save_bar_chart(
        territoires_counter,
        "Top des territoires",
        "Nombre d'occurrences",
        "Territoire",
        OUTPUT_DIR / "territoires.png",
        20
    )

    save_pie_chart(
        type_counter,
        "Répartition fiches actions / autres fiches",
        OUTPUT_DIR / "repartition_fiches_actions_autres.png"
    )

    comparison_df = save_comparison_thematiques(
        rows,
        OUTPUT_DIR / "comparaison_thematiques_fiches_actions_autres.png",
        TOP_N_THEMATIQUES
    )

    save_year_chart(
        years_counter,
        OUTPUT_DIR / "evolution_par_annee.png"
    )

    export_excel(rows, comparison_df)

    print("\nTerminé.")
    print(f"Dossier des graphes : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()