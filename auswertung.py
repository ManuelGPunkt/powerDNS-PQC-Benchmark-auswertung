"""Auswertung des DNSSEC-Benchmarks (dnssec_bench.xlsx).

Erzeugt:
- kennzahlen.csv: Statistische Kennzahlen für alle Algorithmus/Operation-Kombinationen
- boxplot_<operation>.png: Boxplots aller Algorithmen pro Operation (logarithmisch)
- vergleich_median.png: Gruppiertes Balkendiagramm der Mediane aller Operationen
- variationskoeffizient.png: Vergleich der relativen Streuung (Std.-Abw./Mittelwert)
- normalitaet.csv: Shapiro-Wilk-Test auf Normalverteilung je Kombination
- iterationsverlauf.png: Laufzeit über die Iterationen (Warm-up-Effekte)
- histogramm_<algo>_<operation>.png: Verteilung einzelner Kombinationen
"""

import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats as scipy_stats

# Darstellung angelehnt an übliche Layouts wissenschaftlicher Arbeiten
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.alpha": 0.4,
    "figure.dpi": 300,
})

BILDBREITE = 6.3  # Zoll, entspricht ca. 16 cm Textbreite

ALGORITHMEN = [
    # Klassische Verfahren
    "RSASHA1", "RSASHA1-NSEC3-SHA1", "RSASHA256", "RSASHA512",
    "ECDSAP256SHA256", "ECDSAP384SHA384", "ED25519", "ED448",
    # Post-Quanten-Verfahren
    "MLDSA44", "FALCON512", "MAYO1", "SLHDSASHA2128S",
    "CROSSRSDP128", "MQOM3GF16", "SNOVAIK",
]

OPERATIONEN = {
    "keypair": "Schlüsselerzeugung",
    "sign": "Signaturerstellung",
    "verify": "Signaturverifikation",
}


def lade_daten(pfad="dnssec_bench.xlsx"):
    return pd.read_excel(pfad)


def werte(df, algorithmus, operation):
    maske = (df["algorithm"] == algorithmus) & (df["operation"] == operation)
    return df.loc[maske, "time_us"]


def kennzahlen(df):
    zeilen = []
    for algo in ALGORITHMEN:
        for op in OPERATIONEN:
            w = werte(df, algo, op)
            zeilen.append({
                "Algorithmus": algo,
                "Operation": OPERATIONEN[op],
                "Mittelwert [µs]": w.mean(),
                "Median [µs]": w.median(),
                "Std.-Abw. [µs]": w.std(),
                "Varianz [µs²]": w.var(),
                "Variationskoeff. [%]": w.std() / w.mean() * 100,
                "IQR [µs]": w.quantile(0.75) - w.quantile(0.25),
                "Schiefe": w.skew(),
                "Exzess": w.kurt(),
                "Minimum [µs]": w.min(),
                "Maximum [µs]": w.max(),
                "P5 [µs]": w.quantile(0.05),
                "P95 [µs]": w.quantile(0.95),
            })
    return pd.DataFrame(zeilen)


def boxplot_pro_operation(df, operation, datei):
    daten = [werte(df, algo, operation) for algo in ALGORITHMEN]

    fig, ax = plt.subplots(figsize=(BILDBREITE, 3.2))
    ax.boxplot(daten, tick_labels=ALGORITHMEN, showfliers=False,
               medianprops={"color": "firebrick"})
    ax.set_yscale("log")
    ax.set_ylabel("Laufzeit [µs] (log.)")
    ax.set_title(f"{OPERATIONEN[operation]} – Laufzeitvergleich "
                 f"(je 100 Wiederholungen)")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")

    fig.tight_layout()
    fig.savefig(datei, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Gespeichert: {datei}")


def vergleich_median(df, datei="vergleich_median.png"):
    fig, ax = plt.subplots(figsize=(BILDBREITE, 3.2))
    breite = 0.25
    x = range(len(ALGORITHMEN))

    for i, (op, name) in enumerate(OPERATIONEN.items()):
        mediane = [werte(df, algo, op).median() for algo in ALGORITHMEN]
        ax.bar([p + (i - 1) * breite for p in x], mediane,
               width=breite, label=name)

    ax.set_yscale("log")
    ax.set_ylabel("Median der Laufzeit [µs] (log.)")
    ax.set_title("Laufzeitvergleich der Operationen (Median)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(ALGORITHMEN, rotation=45, ha="right")
    ax.legend()

    fig.tight_layout()
    fig.savefig(datei, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Gespeichert: {datei}")


def variationskoeffizient(df, datei="variationskoeffizient.png"):
    fig, ax = plt.subplots(figsize=(BILDBREITE, 3.2))
    breite = 0.25
    x = range(len(ALGORITHMEN))

    for i, (op, name) in enumerate(OPERATIONEN.items()):
        vk = []
        for algo in ALGORITHMEN:
            w = werte(df, algo, op)
            vk.append(w.std() / w.mean() * 100)
        ax.bar([p + (i - 1) * breite for p in x], vk, width=breite, label=name)

    ax.set_yscale("log")
    ax.set_ylabel("Variationskoeffizient [%] (log.)")
    ax.set_title("Relative Streuung der Laufzeiten (Std.-Abw. / Mittelwert)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(ALGORITHMEN, rotation=45, ha="right")
    ax.legend()

    fig.tight_layout()
    fig.savefig(datei, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Gespeichert: {datei}")


def normalitaet(df, alpha=0.05, datei="normalitaet.csv"):
    zeilen = []
    for algo in ALGORITHMEN:
        for op in OPERATIONEN:
            w = werte(df, algo, op)
            statistik, p_wert = scipy_stats.shapiro(w)
            zeilen.append({
                "Algorithmus": algo,
                "Operation": OPERATIONEN[op],
                "Shapiro-W": statistik,
                "p-Wert": p_wert,
                f"Normalverteilt (α={alpha})": "ja" if p_wert >= alpha else "nein",
            })
    tabelle = pd.DataFrame(zeilen)
    tabelle.to_csv(datei, index=False, float_format="%.4f")
    print(f"Shapiro-Wilk-Test (auch als {datei} gespeichert):\n")
    print(tabelle.round(4).to_string(index=False))
    print()
    return tabelle


def iterationsverlauf(df, kombinationen, datei="iterationsverlauf.png"):
    fig, achsen = plt.subplots(1, len(kombinationen), sharex=True,
                               figsize=(BILDBREITE, 2.4))
    if len(kombinationen) == 1:
        achsen = [achsen]

    for ax, (algo, op) in zip(achsen, kombinationen):
        maske = (df["algorithm"] == algo) & (df["operation"] == op)
        g = df.loc[maske].sort_values("iteration")
        ax.plot(g["iteration"], g["time_us"], ".", markersize=2,
                alpha=0.6, label="Messwert")
        ax.plot(g["iteration"], g["time_us"].rolling(10, center=True).mean(),
                linewidth=1, color="firebrick", label="Gleitender Mittelwert (10)")
        ax.set_title(f"{algo} – {OPERATIONEN[op]}", fontsize=8)
        ax.set_xlabel("Iteration")
        ax.grid(True, axis="both", alpha=0.4)

    achsen[0].set_ylabel("Laufzeit [µs]")
    achsen[-1].legend(fontsize=7, loc="upper right")

    fig.tight_layout()
    fig.savefig(datei, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Gespeichert: {datei}")


def histogramm(df, algorithmus, operation, datei=None):
    w = werte(df, algorithmus, operation)
    datei = datei or f"histogramm_{algorithmus.lower()}_{operation}.png"

    fig, ax = plt.subplots(figsize=(BILDBREITE, 2.6))
    ax.hist(w, bins=20)
    ax.set_xlabel("Laufzeit [µs]")
    ax.set_ylabel("Häufigkeit")
    ax.set_title(f"{algorithmus} – {OPERATIONEN[operation]} "
                 f"(100 Wiederholungen)")

    fig.tight_layout()
    fig.savefig(datei, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Gespeichert: {datei}")


def main():
    df = lade_daten()

    tabelle = kennzahlen(df)
    tabelle.to_csv("kennzahlen.csv", index=False, float_format="%.2f")
    print("Kennzahlen (auch als kennzahlen.csv gespeichert):\n")
    print(tabelle.round(2).to_string(index=False))
    print()

    for op in OPERATIONEN:
        boxplot_pro_operation(df, op, f"boxplot_{op}.png")

    vergleich_median(df)
    variationskoeffizient(df)
    normalitaet(df)

    # Kombinationen mit erkennbarem Warm-up-Verhalten
    iterationsverlauf(df, [
        ("RSASHA256", "keypair"),
        ("ECDSAP256SHA256", "verify"),
        ("MLDSA44", "sign"),
    ])

    # Beispielhafte Verteilungen; bei Bedarf weitere Kombinationen ergänzen
    histogramm(df, "RSASHA1", "keypair")
    histogramm(df, "SLHDSASHA2128S", "sign")


if __name__ == "__main__":
    main()
