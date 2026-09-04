from pathlib import Path
import json
import re
import time
from collections import Counter

import pandas as pd
import matplotlib

# Production de fichiers PNG sans dépendre d'une interface graphique locale.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


"""
Script d'analyse de la catégorie "nature_initiative".

Sorties :
- Graphiques PNG dans :
  Index_Insight/outputs_graphs/outputs_graphs_natures/

- Fichier Excel dans :
  Index_Insight/outputs_graphs/outputs_graphs_natures/stats_natures_initiatives.xlsx
"""


BASE_DIR = Path(__file__).resolve().parents[1]

LLM_DIR = BASE_DIR / "LLM_Tagged_Database"
OUTPUT_DIR = BASE_DIR / "outputs_graphs" / "outputs_graphs_natures"
OUTPUT_EXCEL = OUTPUT_DIR / "stats_natures_initiatives.xlsx"

FICHES_ACTIONS_KEYWORD = "Fiches_actions_database"

TOP_N = 20


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


def collect_rows():
    json_files = list(LLM_DIR.rglob("*.json"))
    rows = []
    error_count = 0

    for json_path in json_files:
        try:
            data = load_json(json_path)

            if not isinstance(data, dict):
                continue

            # Les libellés originaux restent disponibles, mais les graphiques
            # utilisent en priorité la taxonomie contrôlée lorsqu'elle a été
            # appliquée par normaliser_taxonomie.py.
            natures = extract_values(
                data.get(
                    "nature_initiative_normalisee",
                    data.get("nature_initiative"),
                )
            )

            if not natures:
                natures = ["non renseigné"]

            rows.append({
                "file": json_path.name,
                "path": str(json_path),
                "type_fiche": "fiche action" if is_fiche_action(json_path) else "autre fiche",
                "natures": natures
            })

        except Exception as e:
            error_count += 1
            print(f"Erreur avec {json_path.name} : {e}")

    return rows, len(json_files), error_count


def count_brut(rows, only_autres=False):
    counter = Counter()

    for row in rows:
        if only_autres and row["type_fiche"] == "fiche action":
            continue

        for nature in row["natures"]:
            counter[nature] += 1

    return counter


def count_pondere(rows, only_autres=False):
    counter = Counter()

    for row in rows:
        if only_autres and row["type_fiche"] == "fiche action":
            continue

        unique_natures = sorted(set(row["natures"]))

        if not unique_natures:
            continue

        poids = 1 / len(unique_natures)

        for nature in unique_natures:
            counter[nature] += poids

    return counter


def save_bar_chart(counter, title, output_path, top_n=TOP_N):
    items = counter.most_common(top_n)

    if not items:
        print(f"Aucune donnée pour : {title}")
        return False

    labels = [item[0] for item in items]
    values = [item[1] for item in items]

    plt.figure(figsize=(12, max(6, len(labels) * 0.4)))
    plt.barh(labels[::-1], values[::-1])
    plt.title(title)
    plt.xlabel("Nombre d'occurrences")
    plt.ylabel("Nature d'initiative")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    if output_path.exists():
        print(f"Graphe créé : {output_path}")
        return True

    print(f"Erreur : le graphe n'a pas été créé : {output_path}")
    return False


def save_comparison_chart(counter_all, counter_autres, output_path, top_n=TOP_N):
    top_natures = [
        nature for nature, _ in counter_all.most_common(top_n)
    ]

    data = []

    for nature in top_natures:
        data.append({
            "nature": nature,
            "toutes_fiches": counter_all.get(nature, 0),
            "hors_fiches_actions": counter_autres.get(nature, 0)
        })

    df = pd.DataFrame(data)

    if df.empty:
        print("Aucune donnée pour le comparatif.")
        return df, False

    x = range(len(df))

    plt.figure(figsize=(14, 7))

    plt.bar(
        [i - 0.2 for i in x],
        df["toutes_fiches"],
        width=0.4,
        label="Toutes fiches"
    )

    plt.bar(
        [i + 0.2 for i in x],
        df["hors_fiches_actions"],
        width=0.4,
        label="Hors fiches actions"
    )

    plt.xticks(x, df["nature"], rotation=45, ha="right")
    plt.title("Répartition des natures d'initiative : avec / sans fiches actions")
    plt.xlabel("Nature d'initiative")
    plt.ylabel("Occurrence pondérée")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    if output_path.exists():
        print(f"Graphe créé : {output_path}")
        return df, True

    print(f"Erreur : le graphe n'a pas été créé : {output_path}")
    return df, False


def counter_to_df(counter):
    return pd.DataFrame(
        [
            {
                "nature_initiative": nature,
                "valeur": round(value, 4)
            }
            for nature, value in counter.most_common()
        ]
    )


def export_excel(
    rows,
    brut_all,
    pondere_all,
    brut_autres,
    pondere_autres,
    comparison_df
):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows_for_excel = []

    for row in rows:
        rows_for_excel.append({
            "file": row["file"],
            "type_fiche": row["type_fiche"],
            "natures": ", ".join(row["natures"]),
            "path": row["path"]
        })

    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        pd.DataFrame(rows_for_excel).to_excel(
            writer,
            sheet_name="Données fichiers",
            index=False
        )

        counter_to_df(brut_all).to_excel(
            writer,
            sheet_name="Brut toutes fiches",
            index=False
        )

        counter_to_df(pondere_all).to_excel(
            writer,
            sheet_name="Pondéré toutes fiches",
            index=False
        )

        counter_to_df(brut_autres).to_excel(
            writer,
            sheet_name="Brut hors actions",
            index=False
        )

        counter_to_df(pondere_autres).to_excel(
            writer,
            sheet_name="Pondéré hors actions",
            index=False
        )

        comparison_df.to_excel(
            writer,
            sheet_name="Comparatif",
            index=False
        )

    if OUTPUT_EXCEL.exists():
        print(f"Excel créé : {OUTPUT_EXCEL}")
        return True

    print(f"Erreur : l'Excel n'a pas été créé : {OUTPUT_EXCEL}")
    return False


def main():
    start_time = time.time()

    print("Analyse des natures d'initiative...")
    print(f"Dossier JSON analysé : {LLM_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows, total_json_files, error_count = collect_rows()

    if not rows:
        print("Aucune donnée exploitable.")
        return

    print(f"{total_json_files} fichiers JSON trouvés.")
    print(f"{len(rows)} fichiers JSON analysés.")
    print(f"{error_count} erreurs rencontrées.")

    brut_all = count_brut(rows, only_autres=False)
    pondere_all = count_pondere(rows, only_autres=False)

    brut_autres = count_brut(rows, only_autres=True)
    pondere_autres = count_pondere(rows, only_autres=True)

    generated_graphs = 0

    if save_bar_chart(
        brut_all,
        "Natures d'initiative — occurrences brutes",
        OUTPUT_DIR / "natures_brut_toutes_fiches.png"
    ):
        generated_graphs += 1

    if save_bar_chart(
        pondere_all,
        "Natures d'initiative — occurrences pondérées",
        OUTPUT_DIR / "natures_pondere_toutes_fiches.png"
    ):
        generated_graphs += 1

    if save_bar_chart(
        pondere_autres,
        "Natures d'initiative — pondéré hors fiches actions",
        OUTPUT_DIR / "natures_pondere_hors_fiches_actions.png"
    ):
        generated_graphs += 1

    comparison_df, comparison_ok = save_comparison_chart(
        pondere_all,
        pondere_autres,
        OUTPUT_DIR / "comparatif_natures_avec_sans_fiches_actions.png"
    )

    if comparison_ok:
        generated_graphs += 1

    excel_ok = export_excel(
        rows,
        brut_all,
        pondere_all,
        brut_autres,
        pondere_autres,
        comparison_df
    )

    elapsed_time = round(time.time() - start_time, 2)

    print("\n" + "=" * 70)

    if generated_graphs == 4 and excel_ok:
        print("OK - Génération des graphiques terminée avec succès.")
    else:
        print("ATTENTION - Génération terminée, mais certains fichiers n'ont pas été créés.")

    print("=" * 70)
    print(f"Dossier de sortie : {OUTPUT_DIR}")
    print(f"Graphiques générés : {generated_graphs}/4")
    print(f"Excel généré : {'oui' if excel_ok else 'non'}")
    print(f"Fichiers JSON trouvés : {total_json_files}")
    print(f"Fichiers JSON analysés : {len(rows)}")
    print(f"Erreurs : {error_count}")
    print(f"Temps d'exécution : {elapsed_time} secondes")
    print("=" * 70)


if __name__ == "__main__":
    main()
