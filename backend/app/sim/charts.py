"""Matplotlib charts for the simulation study results.

Generates:
  sim_wait_time.png        — Box plot of avg wait time across seeds (FCFS vs Smart)
  sim_transformer_peak.png — Box plot of transformer peak kVA
  sim_overload.png         — Bar chart of mean overload intervals (±95% CI)
  sim_utilization_gini.png — Box plot of Gini coefficient
  sim_energy_served.png    — Bar chart of total energy served (±95% CI)
  sim_utilization_heatmap.png — Per-station utilization heatmap
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")  # headless / CI-safe backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from app.sim.engine import SimResult

PALETTE = {"fcfs": "#e67e22", "smart": "#2980b9"}
STYLE_KWARGS = {"edgecolor": "white", "linewidth": 0.6}


def _ci95(values: List[float]) -> tuple[float, float]:
    """Return (mean, half-width of 95% CI) using t-distribution."""
    from scipy.stats import t as t_dist
    n = len(values)
    if n < 2:
        return float(np.mean(values)), 0.0
    mean = float(np.mean(values))
    se = float(np.std(values, ddof=1)) / np.sqrt(n)
    half = float(t_dist.ppf(0.975, df=n - 1)) * se
    return mean, half


def plot_boxplot(
    fcfs_vals: List[float],
    smart_vals: List[float],
    ylabel: str,
    title: str,
    out_path: Path,
    ylog: bool = False,
):
    fig, ax = plt.subplots(figsize=(6, 4))
    bp = ax.boxplot(
        [fcfs_vals, smart_vals],
        tick_labels=["FCFS", "Smart"],
        patch_artist=True,
        widths=0.4,
        medianprops={"color": "white", "linewidth": 2},
    )
    for patch, color in zip(bp["boxes"], [PALETTE["fcfs"], PALETTE["smart"]]):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold")
    if ylog:
        ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_bar_ci(
    categories: List[str],
    fcfs_vals: List[float],
    smart_vals: List[float],
    ylabel: str,
    title: str,
    out_path: Path,
):
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(categories))
    width = 0.32

    for i, (label, vals, color) in enumerate([
        ("FCFS", fcfs_vals, PALETTE["fcfs"]),
        ("Smart", smart_vals, PALETTE["smart"]),
    ]):
        mean, half = _ci95(vals)
        ax.bar(
            x + (i - 0.5) * width,
            [mean] * len(categories),
            width,
            label=label,
            color=color,
            alpha=0.85,
            **STYLE_KWARGS,
        )
        ax.errorbar(
            x + (i - 0.5) * width,
            [mean] * len(categories),
            yerr=[half] * len(categories),
            fmt="none",
            color="black",
            capsize=4,
            linewidth=1.2,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_utilization_heatmap(
    fcfs_results: List[SimResult],
    smart_results: List[SimResult],
    station_ids: List[str],
    out_path: Path,
):
    fcfs_util = np.array([r.utilization_rates for r in fcfs_results])
    smart_util = np.array([r.utilization_rates for r in smart_results])

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, data, label in [
        (axes[0], fcfs_util, "FCFS"),
        (axes[1], smart_util, "Smart"),
    ]:
        im = ax.imshow(data.T, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1)
        ax.set_title(f"[DES] Station Utilization — {label}", fontsize=10, fontweight="bold")
        ax.set_xlabel("Seed", fontsize=9)
        ax.set_yticks(range(len(station_ids)))
        ax.set_yticklabels(station_ids)
    fig.colorbar(im, ax=axes.ravel().tolist(), label="Utilization Rate")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def generate_all_charts(
    fcfs_results: List[SimResult],
    smart_results: List[SimResult],
    station_ids: List[str],
    out_dir: Path,
):
    """Generate all simulation study PNG charts into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Average wait time
    plot_boxplot(
        [r.avg_wait_time_min for r in fcfs_results],
        [r.avg_wait_time_min for r in smart_results],
        ylabel="[DES] Avg Wait Time (minutes)",
        title="Average EV Wait Time: FCFS vs Smart (30 seeds)",
        out_path=out_dir / "sim_wait_time.png",
    )

    # 2. Transformer peak kVA
    plot_boxplot(
        [r.transformer_peak_kva for r in fcfs_results],
        [r.transformer_peak_kva for r in smart_results],
        ylabel="[DES] Transformer Peak kVA",
        title="Transformer Peak kVA: FCFS vs Smart (30 seeds)",
        out_path=out_dir / "sim_transformer_peak.png",
    )

    # 3. Overload intervals bar chart
    plot_bar_ci(
        categories=["Overload Intervals"],
        fcfs_vals=[float(r.overload_intervals) for r in fcfs_results],
        smart_vals=[float(r.overload_intervals) for r in smart_results],
        ylabel="[DES] 15-min windows above 100 kVA",
        title="Transformer Overload Intervals (mean ± 95% CI)",
        out_path=out_dir / "sim_overload.png",
    )

    # 4. Utilization Gini
    plot_boxplot(
        [r.utilization_gini for r in fcfs_results],
        [r.utilization_gini for r in smart_results],
        ylabel="[DES] Utilization Gini Coefficient",
        title="Station Utilization Fairness: FCFS vs Smart (30 seeds)",
        out_path=out_dir / "sim_utilization_gini.png",
    )

    # 5. Energy served bar chart
    plot_bar_ci(
        categories=["Energy Served"],
        fcfs_vals=[r.energy_served_kwh for r in fcfs_results],
        smart_vals=[r.energy_served_kwh for r in smart_results],
        ylabel="[DES] Total Energy Served (kWh)",
        title="Total Energy Served (mean ± 95% CI)",
        out_path=out_dir / "sim_energy_served.png",
    )

    # 6. Per-station utilization heatmap
    plot_utilization_heatmap(
        fcfs_results, smart_results, station_ids,
        out_path=out_dir / "sim_utilization_heatmap.png",
    )

    return [
        str(out_dir / f)
        for f in [
            "sim_wait_time.png",
            "sim_transformer_peak.png",
            "sim_overload.png",
            "sim_utilization_gini.png",
            "sim_energy_served.png",
            "sim_utilization_heatmap.png",
        ]
    ]
