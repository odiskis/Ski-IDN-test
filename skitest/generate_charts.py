#!/usr/bin/env python3
"""
generate_charts.py

Genererer ferdige, publiseringsklare grafbilder (PNG) fra brukertestdataene,
basert pa samme analyseplan som admin panelet. Ment til direkte bruk i
masteroppgaven (sett inn bildene rett i Word/LaTeX).

Bruk:
    # Fra lokal fil (f.eks. lastet ned fra admin panelet eller kopiert fra
    # data/responses.json pa serveren)
    python3 generate_charts.py --file responses.json --outdir charts_output

    # Direkte fra serveren (henter data via admin-API-et)
    python3 generate_charts.py --url https://odinbo.folk.ntnu.no/skitest/app.cgi --pw DITT_PASSORD --outdir charts_output

Krever: matplotlib, scipy, numpy (pip install matplotlib scipy numpy --break-system-packages)
"""

import argparse
import json
import os
import sys
import urllib.request

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as scipy_stats

# ---------- Utseende ----------
COLOR_TOPP = "#C0392B"
COLOR_DAL = "#2563A8"
COLOR_GREEN = "#2D7D46"
COLOR_ORANGE = "#D97706"
COLOR_NAVY = "#1A3C5E"
COLOR_MUTED = "#64748B"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.edgecolor": "#CBD5E1",
    "axes.labelcolor": "#1E293B",
    "text.color": "#1E293B",
    "xtick.color": "#1E293B",
    "ytick.color": "#1E293B",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 200,
})

THRESHOLDS = [("Hoy (<=25m)", 25), ("Moderat (<=100m)", 100), ("Lav (<=250m)", 250)]

SURVEY_LABELS = {
    "nav1": "Enkelt a bevege seg med taster/kontroller",
    "task_topp_way": "Lett a finne vei til malet, Topp",
    "task_dal_way": "Lett a finne vei til malet, Dal",
    "task_topp_sure": "Sikker pa riktig sted, Topp",
    "task_dal_sure": "Sikker pa riktig sted, Dal",
    "map_orient": "Lett a forsta posisjon vs. kartet",
    "map_compare": "Bedre/darligere forstaelse enn 2D-kart",
    "presence1": "Folelse av a bevege seg i ekte terreng",
    "believe1": "Oppfattet som realistisk fremstilling",
    "believe2": "Oppfattet som palitelig fremstilling",
    "believe3": "Ville stolt pa modellen for planlegging",
}


# ---------- Datalasting ----------
def load_data(args):
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            return json.load(f)
    if args.url and args.pw:
        url = args.url.rstrip("/") + "/api/admin/data?pw=" + urllib.parse_quote(args.pw)
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read().decode("utf-8"))
    raise SystemExit("Du ma oppgi enten --file eller bade --url og --pw.")


# ---------- Statistikk-hjelpefunksjoner ----------
def distance_values(data, task):
    out = []
    for d in data:
        t = d.get("tasks", {}).get(task, {})
        if t.get("status") == "finished" and isinstance(t.get("distance_m"), (int, float)):
            out.append(t["distance_m"])
    return out


def time_values(data, task):
    out = []
    for d in data:
        v = d.get("tasks", {}).get(task, {}).get("time_seconds")
        if isinstance(v, (int, float)):
            out.append(v)
    return out


def completion_rate(data, task):
    attempted = [d for d in data if d.get("tasks", {}).get(task, {}).get("status")]
    if not attempted:
        return 0.0
    finished = [d for d in attempted if d["tasks"][task]["status"] == "finished"]
    return 100.0 * len(finished) / len(attempted)


def recognition_rate(data, task, threshold):
    attempted = [d for d in data if d.get("tasks", {}).get(task, {}).get("status")]
    if not attempted:
        return 0.0
    within = [
        d for d in attempted
        if d["tasks"][task]["status"] == "finished"
        and isinstance(d["tasks"][task].get("distance_m"), (int, float))
        and d["tasks"][task]["distance_m"] <= threshold
    ]
    return 100.0 * len(within) / len(attempted)


def has_any_distance(data):
    return bool(distance_values(data, "topp") or distance_values(data, "dal"))


def group_by_field(data, field, order=None):
    groups = {}
    for d in data:
        key = d.get(field) or "ukjent"
        groups.setdefault(key, []).append(d)
    if order:
        return {k: groups[k] for k in order if k in groups}
    return groups


def survey_values(data, key):
    out = []
    for d in data:
        v = d.get("survey", {}).get(key)
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return out


def no_data_note(ax, text="Ingen data tilgjengelig ennaa"):
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=11, color=COLOR_MUTED, transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])


def savefig(fig, outdir, name):
    path = os.path.join(outdir, name)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Lagret: {path}")


# ---------- Chart 1: Gjenkjenningsrate ----------
def chart_recognition_rate(data, outdir):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    if not has_any_distance(data):
        no_data_note(ax, "Ingen avstandsdata (distance_m) mottatt fra terrengmodellen ennaa")
        ax.set_title("Gjenkjenningsrate per presisjonsterskel")
        savefig(fig, outdir, "01_gjenkjenningsrate.png")
        return
    labels = [t[0] for t in THRESHOLDS]
    topp_vals = [recognition_rate(data, "topp", t[1]) for t in THRESHOLDS]
    dal_vals = [recognition_rate(data, "dal", t[1]) for t in THRESHOLDS]
    x = np.arange(len(labels)); w = 0.35
    ax.bar(x - w/2, topp_vals, w, label="Topp", color=COLOR_TOPP)
    ax.bar(x + w/2, dal_vals, w, label="Dal", color=COLOR_DAL)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("% av deltakere"); ax.set_ylim(0, 100)
    ax.set_title("Gjenkjenningsrate per presisjonsterskel")
    ax.legend()
    savefig(fig, outdir, "01_gjenkjenningsrate.png")


# ---------- Chart 2: Avstandsfordeling (histogram) ----------
def chart_distance_histogram(data, outdir):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    topp_vals, dal_vals = distance_values(data, "topp"), distance_values(data, "dal")
    if not topp_vals and not dal_vals:
        no_data_note(ax, "Ingen avstandsdata (distance_m) mottatt fra terrengmodellen ennaa")
        ax.set_title("Fordeling av sluttavstand")
        savefig(fig, outdir, "02_avstandsfordeling.png")
        return
    bins = [0, 25, 50, 100, 150, 250, 500, max(500, max(topp_vals + dal_vals, default=500) + 1)]
    ax.hist([topp_vals, dal_vals], bins=bins, label=["Topp", "Dal"], color=[COLOR_TOPP, COLOR_DAL])
    ax.set_xlabel("Avstand til mal (meter)"); ax.set_ylabel("Antall deltakere")
    ax.set_title("Fordeling av sluttavstand")
    ax.legend()
    savefig(fig, outdir, "02_avstandsfordeling.png")


# ---------- Chart 3: Fullfort vs gitt opp ----------
def chart_completion(data, outdir):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    tasks = ["topp", "dal"]
    finished = [completion_rate(data, t) for t in tasks]
    gaveup = [100 - f for f in finished]
    x = np.arange(len(tasks))
    ax.bar(x, finished, label="Fullfort", color=COLOR_GREEN)
    ax.bar(x, gaveup, bottom=finished, label="Gitt opp", color=COLOR_ORANGE)
    ax.set_xticks(x); ax.set_xticklabels(["Topp", "Dal"])
    ax.set_ylabel("%"); ax.set_ylim(0, 100)
    ax.set_title("Fullfort vs. gitt opp")
    ax.legend()
    savefig(fig, outdir, "03_fullfort_vs_gitt_opp.png")


# ---------- Chart 4: Tidsbruk (boxplot) ----------
def chart_time_distribution(data, outdir):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    topp_t, dal_t = time_values(data, "topp"), time_values(data, "dal")
    box_data = [v if v else [0] for v in [topp_t, dal_t]]
    bp = ax.boxplot(box_data, tick_labels=["Topp", "Dal"], patch_artist=True, widths=0.5)
    for patch, color in zip(bp["boxes"], [COLOR_TOPP, COLOR_DAL]):
        patch.set_facecolor(color); patch.set_alpha(0.6)
    ax.set_ylabel("Tidsbruk (sekunder)")
    ax.set_title("Fordeling av tidsbruk per oppgave")
    savefig(fig, outdir, "04_tidsbruk_boxplot.png")


# ---------- Chart 5: Topp vs Dal, tre paneler ----------
def chart_topp_vs_dal(data, outdir):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    metrics = [
        ("Snitt tid (s)", [np.mean(time_values(data, "topp")) if time_values(data, "topp") else 0,
                            np.mean(time_values(data, "dal")) if time_values(data, "dal") else 0]),
        ("Fullforingsgrad (%)", [completion_rate(data, "topp"), completion_rate(data, "dal")]),
        ("Snitt avstand (m)", [np.mean(distance_values(data, "topp")) if distance_values(data, "topp") else 0,
                                np.mean(distance_values(data, "dal")) if distance_values(data, "dal") else 0]),
    ]
    for ax, (title, vals) in zip(axes, metrics):
        ax.bar(["Topp", "Dal"], vals, color=[COLOR_TOPP, COLOR_DAL])
        ax.set_title(title)
    fig.suptitle("Topp vs. Dal, direkte sammenligning")
    savefig(fig, outdir, "05_topp_vs_dal.png")


# ---------- Chart 6 og 7: Gruppesammenligninger ----------
def chart_group_comparison(data, outdir, field, order, label_map, filename, title):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    groups = group_by_field(data, field, order)
    if not groups:
        no_data_note(ax); ax.set_title(title); savefig(fig, outdir, filename); return
    labels = [label_map.get(k, k) for k in groups]
    topp_vals = [completion_rate(v, "topp") for v in groups.values()]
    dal_vals = [completion_rate(v, "dal") for v in groups.values()]
    x = np.arange(len(labels)); w = 0.35
    ax.bar(x - w/2, topp_vals, w, label="Topp", color=COLOR_TOPP)
    ax.bar(x + w/2, dal_vals, w, label="Dal", color=COLOR_DAL)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("Fullforingsgrad (%)"); ax.set_ylim(0, 100)
    ax.set_title(title)
    ax.legend()
    savefig(fig, outdir, filename)


# ---------- Chart 8-10: Korrelasjons-scatterplot ----------
def _scatter_points(data, x_extractor):
    xs_topp, ys_topp, xs_dal, ys_dal = [], [], [], []
    for d in data:
        for task, xs, ys in [("topp", xs_topp, ys_topp), ("dal", xs_dal, ys_dal)]:
            dist = d.get("tasks", {}).get(task, {}).get("distance_m")
            if not isinstance(dist, (int, float)):
                continue
            x = x_extractor(d)
            if x is None:
                continue
            xs.append(x); ys.append(dist)
    return xs_topp, ys_topp, xs_dal, ys_dal


def chart_scatter(data, outdir, x_extractor, xlabel, filename, title):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    xs_topp, ys_topp, xs_dal, ys_dal = _scatter_points(data, x_extractor)
    all_x, all_y = xs_topp + xs_dal, ys_topp + ys_dal
    if len(all_x) < 2:
        no_data_note(ax, "Ingen avstandsdata (distance_m) mottatt fra terrengmodellen ennaa")
        ax.set_title(title)
        savefig(fig, outdir, filename)
        return
    ax.scatter(xs_topp, ys_topp, color=COLOR_TOPP, label="Topp", alpha=0.8)
    ax.scatter(xs_dal, ys_dal, color=COLOR_DAL, label="Dal", alpha=0.8)
    pearson_r, pearson_p = scipy_stats.pearsonr(all_x, all_y)
    spearman_r, spearman_p = scipy_stats.spearmanr(all_x, all_y)
    ax.set_xlabel(xlabel); ax.set_ylabel("Sluttavstand (m)")
    ax.set_title(f"{title}\nPearson r={pearson_r:.2f} (p={pearson_p:.3f}), Spearman rho={spearman_r:.2f} (p={spearman_p:.3f})",
                 fontsize=10)
    ax.legend()
    savefig(fig, outdir, filename)


# ---------- Chart 11: Survey Likert-gjennomsnitt ----------
def chart_survey_likert(data, outdir):
    fig, ax = plt.subplots(figsize=(8, 6))
    labels, means, errs = [], [], []
    for key, label in SURVEY_LABELS.items():
        vals = survey_values(data, key)
        if not vals:
            continue
        labels.append(label)
        means.append(np.mean(vals))
        errs.append(np.std(vals, ddof=1) if len(vals) > 1 else 0)
    if not labels:
        no_data_note(ax); savefig(fig, outdir, "11_survey_likert.png"); return
    y = np.arange(len(labels))
    ax.barh(y, means, xerr=errs, color=COLOR_NAVY, capsize=4)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, 5.5); ax.set_xlabel("Gjennomsnitt (Likert 1-5, feilfelt = standardavvik)")
    ax.invert_yaxis()
    ax.set_title("Survey, gjennomsnittsvurdering per pastand")
    savefig(fig, outdir, "11_survey_likert.png")


def main():
    parser = argparse.ArgumentParser(description="Generer grafbilder fra brukertestdata")
    parser.add_argument("--file", help="Sti til lokal responses.json")
    parser.add_argument("--url", help="Base-URL til appen, f.eks. https://odinbo.folk.ntnu.no/skitest/app.cgi")
    parser.add_argument("--pw", help="Admin-passord (brukes sammen med --url)")
    parser.add_argument("--outdir", default="charts_output", help="Mappe grafene lagres i")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    data = load_data(args)
    print(f"Lastet {len(data)} svar. Genererer grafer i '{args.outdir}/' ...")

    chart_recognition_rate(data, args.outdir)
    chart_distance_histogram(data, args.outdir)
    chart_completion(data, args.outdir)
    chart_time_distribution(data, args.outdir)
    chart_topp_vs_dal(data, args.outdir)
    chart_group_comparison(
        data, args.outdir, "ski_experience",
        ["ingen", "nybegynner", "middels", "erfaren", "ekspert"],
        {}, "06_skierfaring.png", "Skierfaring vs. fullforingsgrad",
    )
    chart_group_comparison(
        data, args.outdir, "map_experience",
        ["aldri", "under5", "5til15", "over15"],
        {"aldri": "Aldri", "under5": "<5/ar", "5til15": "5-15/ar", "over15": "15+/ar"},
        "07_karterfaring.png", "Karterfaring vs. fullforingsgrad",
    )
    chart_scatter(data, args.outdir, lambda d: (lambda v: int(v) if v and v.isdigit() else None)(d.get("survey", {}).get("presence1")),
                  "Presence (1-5)", "08_presence_vs_avstand.png", "Presence vs. sluttavstand")

    def believe_avg(d):
        vals = []
        for k in ("believe1", "believe2", "believe3"):
            v = d.get("survey", {}).get(k)
            if v and str(v).isdigit():
                vals.append(int(v))
        return float(np.mean(vals)) if vals else None

    chart_scatter(data, args.outdir, believe_avg, "Believability (snitt 1-5)",
                  "09_believability_vs_avstand.png", "Believability vs. sluttavstand")

    def time_extractor_factory():
        # Denne brukes ikke direkte, tid-vs-avstand handteres separat under
        pass

    # Tid vs avstand (egen handtering siden x-verdien er per-oppgave, ikke global per deltaker)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    xs_topp = [d["tasks"]["topp"]["time_seconds"] for d in data
               if isinstance(d.get("tasks", {}).get("topp", {}).get("distance_m"), (int, float))
               and isinstance(d["tasks"]["topp"].get("time_seconds"), (int, float))]
    ys_topp = [d["tasks"]["topp"]["distance_m"] for d in data
               if isinstance(d.get("tasks", {}).get("topp", {}).get("distance_m"), (int, float))
               and isinstance(d["tasks"]["topp"].get("time_seconds"), (int, float))]
    xs_dal = [d["tasks"]["dal"]["time_seconds"] for d in data
              if isinstance(d.get("tasks", {}).get("dal", {}).get("distance_m"), (int, float))
              and isinstance(d["tasks"]["dal"].get("time_seconds"), (int, float))]
    ys_dal = [d["tasks"]["dal"]["distance_m"] for d in data
              if isinstance(d.get("tasks", {}).get("dal", {}).get("distance_m"), (int, float))
              and isinstance(d["tasks"]["dal"].get("time_seconds"), (int, float))]
    all_x, all_y = xs_topp + xs_dal, ys_topp + ys_dal
    if len(all_x) < 2:
        no_data_note(ax, "Ingen avstandsdata (distance_m) mottatt fra terrengmodellen ennaa")
        ax.set_title("Tidsbruk vs. sluttavstand")
    else:
        ax.scatter(xs_topp, ys_topp, color=COLOR_TOPP, label="Topp", alpha=0.8)
        ax.scatter(xs_dal, ys_dal, color=COLOR_DAL, label="Dal", alpha=0.8)
        pearson_r, pearson_p = scipy_stats.pearsonr(all_x, all_y)
        spearman_r, spearman_p = scipy_stats.spearmanr(all_x, all_y)
        ax.set_xlabel("Tidsbruk (sekunder)"); ax.set_ylabel("Sluttavstand (m)")
        ax.set_title(f"Tidsbruk vs. sluttavstand\nPearson r={pearson_r:.2f} (p={pearson_p:.3f}), Spearman rho={spearman_r:.2f} (p={spearman_p:.3f})",
                     fontsize=10)
        ax.legend()
    savefig(fig, args.outdir, "10_tid_vs_avstand.png")

    chart_survey_likert(data, args.outdir)

    print("\nFerdig! Alle grafer ligger i:", os.path.abspath(args.outdir))


if __name__ == "__main__":
    import urllib.parse
    main()
