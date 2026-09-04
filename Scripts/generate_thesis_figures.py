"""Génère des figures en anglais pour le mémoire Index_Insight."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "Figures"


def apply_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.dpi": 160,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def save_corpus_source_composition() -> None:
    sources = ["CNAV", "Fondation\nde France", "SIAGE action\nsheets", "HCFEA", "IReSP\nAutonomie", "RFVAA"]
    records = [42, 43, 60, 23, 131, 854]
    colors = ["#82a6c9", "#82a6c9", "#e6a65d", "#82a6c9", "#82a6c9", "#2d6c9f"]

    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    bars = ax.bar(sources, records, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_ylabel("Number of documents")
    ax.set_title("Composition of the final corpus by source")
    ax.set_ylim(0, 940)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.7)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, records):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 17, f"{value}", ha="center", va="bottom")
    ax.text(5, 885, "74% of corpus", ha="center", va="bottom", color="#2d6c9f", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "corpus-source-composition.png")
    plt.close(fig)


def save_human_judgment_distribution() -> None:
    fields = ["Territory", "Stakeholder", "Date", "Theme"]
    correct = [23, 37, 44, 60]
    correctly_absent = [30, 0, 0, 0]
    partial = [1, 0, 7, 0]
    incorrect = [0, 1, 5, 0]
    non_evaluable = [6, 22, 4, 0]
    categories = [
        ("Correct", correct, "#2d6c9f"),
        ("Correctly absent", correctly_absent, "#75a96f"),
        ("Partial", partial, "#e6a65d"),
        ("Incorrect", incorrect, "#c95555"),
        ("Non-evaluable", non_evaluable, "#b5b5b5"),
    ]

    fig, ax = plt.subplots(figsize=(8.2, 4.7))
    bottom = [0] * len(fields)
    for label, values, color in categories:
        bars = ax.bar(fields, values, bottom=bottom, label=label, color=color, edgecolor="white", linewidth=0.8)
        for bar, value, offset in zip(bars, values, bottom):
            if value >= 4:
                text_color = "black" if label == "Non-evaluable" else "white"
                ax.text(bar.get_x() + bar.get_width() / 2, offset + value / 2, str(value), ha="center", va="center", color=text_color, fontsize=9)
        bottom = [current + value for current, value in zip(bottom, values)]
    ax.set_ylabel("Documents in the reference sample")
    ax.set_title("Human judgments by metadata field (n=60 per field)")
    ax.set_ylim(0, 60)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.14), frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "human-judgment-distribution.png")
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(exist_ok=True)
    apply_style()
    save_corpus_source_composition()
    save_human_judgment_distribution()
    print(f"Created {FIGURES_DIR / 'corpus-source-composition.png'}")
    print(f"Created {FIGURES_DIR / 'human-judgment-distribution.png'}")


if __name__ == "__main__":
    main()
