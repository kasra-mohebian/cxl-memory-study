#!/usr/bin/env python3
"""
plot_results.py
---------------
Generate plots from the existing CXL / HBM / RAM benchmark result files.

This script ONLY reads result files that already exist in ../results and writes
reviewed PNG figures into a new --out directory (default: ../plots-reviewed). Historical plots are not replaced. It does not run benchmarks and does not modify any
result file. Paths are resolved relative to this script, so it works no matter
which directory it is launched from.

Requirements: python3, pandas, matplotlib.

Plots produced:
  1. plots/memory_bandwidth.png       - read/write bandwidth per tier (GiB/s)
  2. plots/page_read.png              - sequential vs random page reads (MPPS)
  3. plots/page_copy.png              - local page-copy bandwidth per tier (GiB/s)
  4. plots/page_copy_size_sweep.png   - copy bandwidth vs working-set size (GiB/s)
  5. plots/inter_tier_copy.png        - inter-tier copy bandwidth per direction (GiB/s)
  6. plots/tier_decision_simulation.png - accesses served per tier (placement policy)
"""

import re
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
os.environ.setdefault("MPL_IGNORE_SYSTEM_FONTS", "1")
import matplotlib
matplotlib.use("Agg")  # headless: no display needed on the server
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Paths (relative to this script -> portable when copied back to the repo)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
RESULTS = REPO_ROOT / "results"
PLOTS = REPO_ROOT / "plots-reviewed"

# ---------------------------------------------------------------------------
# Shared style
# ---------------------------------------------------------------------------
# Keep one display order across the plots. The measured fastest tier depends on
# the operation, so this order is not a universal performance ranking.
TIER_ORDER = ["HBM", "RAM", "CXL"]
TIER_COLORS = {"HBM": "#C0392B", "RAM": "#2E86C1", "CXL": "#27AE60"}

# For grouped bars the two series share one colour scheme everywhere:
#   first series  (write / sequential) -> blue
#   second series (read  / random)     -> orange
SERIES_A = "#4C72B0"   # write / sequential
SERIES_B = "#DD8452"   # read  / random

plt.rcParams.update({
    "figure.dpi": 110,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.axisbelow": True,
    "font.size": 11,
})

DPI = 200
notes = []  # collected assumptions / parsing remarks, printed at the end


def order_tiers(df, col="tier"):
    """Return df reordered to TIER_ORDER (tiers not in the list keep file order at the end)."""
    present = [t for t in TIER_ORDER if t in set(df[col])]
    extra = [t for t in df[col] if t not in present]
    cats = present + list(dict.fromkeys(extra))
    df = df.copy()
    df[col] = pd.Categorical(df[col], categories=cats, ordered=True)
    return df.sort_values(col).reset_index(drop=True)


def save(fig, name):
    out = PLOTS / name
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# 1. Memory bandwidth
# ---------------------------------------------------------------------------
def plot_memory_bandwidth():
    df = pd.read_csv(RESULTS / "memory_benchmark_summary.csv")
    df = order_tiers(df)
    raw = pd.read_csv(RESULTS / "memory_benchmark.csv")
    sd = raw.groupby("tier")[["write_gbs", "read_gbs"]].std().reindex(df["tier"]).fillna(0)
    x = np.arange(len(df))
    w = 0.38

    fig, ax = plt.subplots(figsize=(8, 5))
    b1 = ax.bar(x - w / 2, df["avg_write_gbs"], w, yerr=sd["write_gbs"].to_numpy(), capsize=4, label="Write", color=SERIES_A)
    b2 = ax.bar(x + w / 2, df["avg_read_gbs"], w, yerr=sd["read_gbs"].to_numpy(), capsize=4, label="Sampled read (1 B / 64 B)", color=SERIES_B)
    ax.bar_label(b1, fmt="%.1f", padding=2, fontsize=8)
    ax.bar_label(b2, fmt="%.1f", padding=2, fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(df["tier"])
    ax.set_xlabel("Memory tier")
    ax.set_ylabel("Address range processed (GiB/s)")
    ax.set_title("Bulk write vs sampled read")
    fig.text(0.5, 0.01, "Read: one byte per 64-byte stride; not full-byte read bandwidth.", ha="center", fontsize=8)
    fig.subplots_adjust(bottom=0.16)
    ax.legend(title="Operation")
    return save(fig, "memory_bandwidth.png")


# ---------------------------------------------------------------------------
# 2. Page read (sequential vs random)
# ---------------------------------------------------------------------------
def plot_page_read():
    df = pd.read_csv(RESULTS / "page_benchmark_summary.csv")
    df = order_tiers(df)
    raw = pd.read_csv(RESULTS / "page_benchmark.csv")
    sd = raw.groupby("tier")[["seq_page_mpps", "rand_page_mpps"]].std().reindex(df["tier"]).fillna(0)
    x = np.arange(len(df))
    w = 0.38

    fig, ax = plt.subplots(figsize=(8, 5))
    b1 = ax.bar(x - w / 2, df["avg_seq_page_mpps"], w, yerr=sd["seq_page_mpps"].to_numpy(), capsize=4, label="Sequential", color=SERIES_A)
    b2 = ax.bar(x + w / 2, df["avg_rand_page_mpps"], w, yerr=sd["rand_page_mpps"].to_numpy(), capsize=4, label="Random", color=SERIES_B)
    ax.bar_label(b1, fmt="%.1f", padding=2, fontsize=8)
    ax.bar_label(b2, fmt="%.1f", padding=2, fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(df["tier"])
    ax.set_xlabel("Memory tier")
    ax.set_ylabel("Page read rate (MPPS = million pages/s)")
    ax.set_title("Page-based read performance (sequential vs random)")
    ax.legend(title="Access pattern")
    return save(fig, "page_read.png")


# ---------------------------------------------------------------------------
# 3. Local page copy (within a tier)
# ---------------------------------------------------------------------------
def plot_page_copy():
    df = pd.read_csv(RESULTS / "page_copy_benchmark_summary.csv")
    df = order_tiers(df)
    raw = pd.read_csv(RESULTS / "page_copy_benchmark.csv")
    sd = raw.groupby("tier")[["seq_copy_gbs", "rand_copy_gbs"]].std().reindex(df["tier"]).fillna(0)
    x = np.arange(len(df))
    w = 0.38

    fig, ax = plt.subplots(figsize=(8, 5))
    b1 = ax.bar(x - w / 2, df["avg_seq_copy_gbs"], w, yerr=sd["seq_copy_gbs"].to_numpy(), capsize=4, label="Sequential copy", color=SERIES_A)
    b2 = ax.bar(x + w / 2, df["avg_rand_copy_gbs"], w, yerr=sd["rand_copy_gbs"].to_numpy(), capsize=4, label="Random copy", color=SERIES_B)
    ax.bar_label(b1, fmt="%.2f", padding=2, fontsize=8)
    ax.bar_label(b2, fmt="%.2f", padding=2, fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(df["tier"])
    ax.set_xlabel("Memory tier")
    ax.set_ylabel("Copy bandwidth (GiB/s)")
    ax.set_title("Local page-copy bandwidth within each tier")
    ax.legend(title="Access pattern")
    return save(fig, "page_copy.png")


# ---------------------------------------------------------------------------
# 4. Page copy size sweep (bandwidth vs working-set size)
# ---------------------------------------------------------------------------
def plot_page_copy_size_sweep():
    df = pd.read_csv(RESULTS / "page_copy_size_sweep_summary.csv")
    df = df.sort_values(["tier", "size_mb"])

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for tier in [t for t in TIER_ORDER if t in set(df["tier"])]:
        sub = df[df["tier"] == tier].sort_values("size_mb")
        color = TIER_COLORS.get(tier, None)
        invalid = (sub["size_mb"] >= 8192) & (tier == "HBM")
        if invalid.any():
            ax.scatter(sub.loc[invalid, "size_mb"], sub.loc[invalid, "avg_seq_copy_gbs"],
                       marker="x", color="red", s=80, label="HBM sequential: capacity-confounded")
            ax.scatter(sub.loc[invalid, "size_mb"], sub.loc[invalid, "avg_rand_copy_gbs"],
                       marker="+", color="red", s=80, label="HBM random: capacity-confounded")
            sub = sub.copy()
            sub.loc[invalid, ["avg_seq_copy_gbs", "avg_rand_copy_gbs"]] = np.nan

        ax.plot(sub["size_mb"], sub["avg_seq_copy_gbs"], marker="o",
                linestyle="-", color=color, label=f"{tier} sequential")
        ax.plot(sub["size_mb"], sub["avg_rand_copy_gbs"], marker="s",
                linestyle="--", color=color, label=f"{tier} random")

    # Highlight the HBM near-capacity anomaly if present.
    hbm = df[df["tier"] == "HBM"]
    if not hbm.empty:
        worst = hbm.loc[hbm["avg_seq_copy_gbs"].idxmin()]
        if worst["avg_seq_copy_gbs"] < 1.0:  # clearly collapsed, not normal HBM
            ax.annotate(
                "HBM near-capacity case\n(two buffers approach node capacity)",
                xy=(worst["size_mb"], worst["avg_seq_copy_gbs"]),
                xytext=(worst["size_mb"] * 0.50, 1.6),
                fontsize=8.5, color="#C0392B",
                arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.2),
            )

    sizes = sorted(df["size_mb"].unique())
    ax.set_xticks(sizes)
    ax.set_xlabel("Benchmark size per buffer (MiB)")
    ax.set_ylabel("Copy bandwidth (GiB/s)")
    ax.set_title("Page-copy bandwidth vs working-set size")
    ax.legend(fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    return save(fig, "page_copy_size_sweep.png")


# ---------------------------------------------------------------------------
# 5. Inter-tier copy (observed copy throughput by direction)
# ---------------------------------------------------------------------------
def plot_inter_tier_copy():
    df = pd.read_csv(RESULTS / "inter_tier_copy_benchmark_summary.csv")

    # Preferred ordering pairs promotion/demotion directions together.
    pref = ["RAM->HBM", "HBM->RAM", "RAM->CXL", "CXL->RAM", "HBM->CXL", "CXL->HBM"]
    df["__order"] = df["direction"].apply(lambda d: pref.index(d) if d in pref else len(pref))
    df = df.sort_values("__order").reset_index(drop=True)
    raw = pd.read_csv(RESULTS / "inter_tier_copy_benchmark.csv")
    raw["direction"] = raw["src_tier"] + "->" + raw["dst_tier"]
    sd = raw.groupby("direction")[["seq_copy_gbs", "rand_copy_gbs"]].std().reindex(df["direction"]).fillna(0)
    direction_labels = df["direction"].str.replace("->", "→", regex=False)

    y = np.arange(len(df))
    h = 0.38

    fig, ax = plt.subplots(figsize=(9, 6))
    b1 = ax.barh(y + h / 2, df["avg_seq_copy_gbs"], h, xerr=sd["seq_copy_gbs"].to_numpy(), capsize=4, label="Sequential", color=SERIES_A)
    b2 = ax.barh(y - h / 2, df["avg_rand_copy_gbs"], h, xerr=sd["rand_copy_gbs"].to_numpy(), capsize=4, label="Random", color=SERIES_B)
    ax.bar_label(b1, fmt="%.2f", padding=2, fontsize=8)
    ax.bar_label(b2, fmt="%.2f", padding=2, fontsize=8)

    ax.set_yticks(y)
    ax.set_yticklabels(direction_labels)
    ax.invert_yaxis()  # first direction on top
    ax.set_xlabel("Copy bandwidth (GiB/s)")
    ax.set_ylabel("Copy direction (source -> destination)")
    ax.set_title("Inter-tier page-copy bandwidth by direction")
    ax.legend(title="Access pattern")
    return save(fig, "inter_tier_copy.png")


# ---------------------------------------------------------------------------
# 6. Tier decision simulation (accesses served per tier)
# ---------------------------------------------------------------------------
def plot_tier_decision_simulation():
    text = (RESULTS / "tier_decision_simulation.txt").read_text(encoding="utf-8")
    pat = re.compile(
        r"^(HBM|RAM|CXL)\s+pages:\s*(\d+),\s*accesses served:\s*(\d+)",
        re.MULTILINE,
    )
    rows = [(m.group(1), int(m.group(2)), int(m.group(3))) for m in pat.finditer(text)]
    if not rows:
        raise ValueError("Could not parse any 'pages/accesses served' lines.")
    sim = pd.DataFrame(rows, columns=["tier", "pages", "accesses"])
    sim = order_tiers(sim)

    fig, ax = plt.subplots(figsize=(7.5, 5))
    colors = [TIER_COLORS.get(t, "#888888") for t in sim["tier"]]
    bars = ax.bar(np.arange(len(sim)), sim["accesses"], color=colors, width=0.6)
    ax.bar_label(bars, fmt="%d", padding=2, fontsize=9)

    total = sim["accesses"].sum()
    pct = [f"{100 * a / total:.1f}%" for a in sim["accesses"]]
    for i, p in enumerate(pct):
        ax.text(i, sim["accesses"].iloc[i] / 2, p, ha="center", va="center",
                color="white", fontsize=9, fontweight="bold")

    ax.set_xticks(np.arange(len(sim)))
    ax.set_xticklabels([f"{t}\n({p} pages)" for t, p in zip(sim["tier"], sim["pages"])])
    ax.set_xlabel("Tier (pages placed)")
    ax.set_ylabel("Accesses served")
    ax.set_title("Tier decision simulation: accesses served per tier")
    return save(fig, "tier_decision_simulation.png")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
PLOTTERS = [
    ("memory_bandwidth", plot_memory_bandwidth),
    ("page_read", plot_page_read),
    ("page_copy", plot_page_copy),
    ("page_copy_size_sweep", plot_page_copy_size_sweep),
    ("inter_tier_copy", plot_inter_tier_copy),
    ("tier_decision_simulation", plot_tier_decision_simulation),
]


def main():
    global PLOTS
    parser = argparse.ArgumentParser(description="Create reviewed plots without replacing historical artifacts")
    parser.add_argument("--out", type=Path, default=PLOTS)
    args = parser.parse_args()
    PLOTS = args.out.resolve()
    if PLOTS.exists():
        parser.error("Output already exists; choose a new directory")
    PLOTS.mkdir(parents=True)
    print(f"results dir : {RESULTS}")
    print(f"plots dir   : {PLOTS}\n")
    ok = 0
    for name, fn in PLOTTERS:
        try:
            out = fn()
            print(f"[ok]   {name:26s} -> {out.name}")
            ok += 1
        except Exception as exc:  # keep going so one bad file does not stop the rest
            print(f"[FAIL] {name:26s} : {exc}")
    print(f"\n{ok}/{len(PLOTTERS)} plots generated in {PLOTS}")
    if notes:
        print("\nNotes:")
        for n in notes:
            print(f"  - {n}")
    return 0 if ok == len(PLOTTERS) else 1


if __name__ == "__main__":
    sys.exit(main())
