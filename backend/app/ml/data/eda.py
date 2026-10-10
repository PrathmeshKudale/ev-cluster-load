"""Exploratory Data Analysis (EDA) plotting module for EV Cluster Load."""
import os
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_eda_plots(
    sessions: List[Dict],
    station_loads: List[Dict],
    weather_records: List[Dict],
    output_dir: str = "../docs/img",
) -> List[str]:
    """
    Generate EDA charts and save to docs/img:
    1. hourly_load_profiles.png - Diurnal hourly charging curves per station
    2. session_duration_energy.png - Session duration vs delivered energy (kWh)
    3. weather_correlation.png - Ambient temperature vs cluster active load
    """
    # Resolve output directory
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    generated_files = []

    # 1. Hourly Load Profiles Plot
    df_load = pd.DataFrame(station_loads)
    if not df_load.empty:
        df_load["hour"] = pd.to_datetime(df_load["timestamp"]).dt.hour

        plt.figure(figsize=(10, 5))
        for sid, group in df_load.groupby("station_id"):
            hourly_means = group.groupby("hour")["active_kw"].mean()
            hourly_p90 = group.groupby("hour")["active_kw"].quantile(0.9)
            plt.plot(hourly_means.index, hourly_means.values, label=f"{sid} (mean)", linewidth=2)
            plt.fill_between(hourly_means.index, hourly_means.values, hourly_p90.values, alpha=0.15)

        plt.title("Diurnal Station Load Profiles (Mean & P90 Active kW)")
        plt.xlabel("Hour of Day (UTC)")
        plt.ylabel("Active Load (kW)")
        plt.xticks(range(0, 24, 2))
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(loc="upper left")
        plt.tight_layout()

        p1 = out_path / "hourly_load_profiles.png"
        plt.savefig(p1, dpi=150)
        plt.close()
        generated_files.append(str(p1))

    # 2. Session Duration vs Energy Plot
    df_sess = pd.DataFrame(sessions)
    if not df_sess.empty:
        df_sess["start"] = pd.to_datetime(df_sess["start_time"])
        df_sess["end"] = pd.to_datetime(df_sess["end_time"])
        df_sess["duration_h"] = (df_sess["end"] - df_sess["start"]).dt.total_seconds() / 3600.0

        plt.figure(figsize=(9, 5))
        colors = {"VS1": "#1f77b4", "VS2": "#ff7f0e", "VS3": "#2ca02c", "VS4": "#d62728"}
        for sid, group in df_sess.groupby("station_id"):
            plt.scatter(
                group["duration_h"],
                group["energy_kwh"],
                alpha=0.65,
                s=24,
                label=sid,
                color=colors.get(sid, "#333"),
            )

        plt.title("Charging Session Duration vs. Energy Delivered (kWh)")
        plt.xlabel("Session Duration (Hours)")
        plt.ylabel("Energy Delivered (kWh)")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()

        p2 = out_path / "session_duration_energy.png"
        plt.savefig(p2, dpi=150)
        plt.close()
        generated_files.append(str(p2))

    # 3. Weather Correlation Plot
    df_wx = pd.DataFrame(weather_records)
    if not df_load.empty and not df_wx.empty:
        df_wx["timestamp_dt"] = pd.to_datetime(df_wx["timestamp"])
        df_load["timestamp_dt"] = pd.to_datetime(df_load["timestamp"])
        
        # Aggregate cluster total load per timestamp
        cluster_load = df_load.groupby("timestamp_dt")["active_kw"].sum().reset_index()
        merged = pd.merge(cluster_load, df_wx, on="timestamp_dt")

        fig, ax1 = plt.subplots(figsize=(10, 5))
        color_load = "tab:blue"
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Cluster Total Load (kW)", color=color_load)
        ax1.plot(merged["timestamp_dt"][:168], merged["active_kw"][:168], color=color_load, label="Total Cluster kW", linewidth=1.8)
        ax1.tick_params(axis="y", labelcolor=color_load)

        ax2 = ax1.twinx()
        color_temp = "tab:red"
        ax2.set_ylabel("Ambient Temperature (°C)", color=color_temp)
        ax2.plot(merged["timestamp_dt"][:168], merged["temperature_c"][:168], color=color_temp, linestyle="--", label="Temperature (°C)", linewidth=1.5)
        ax2.tick_params(axis="y", labelcolor=color_temp)

        plt.title("Cluster Load vs. Ambient Temperature (7-Day Sample)")
        fig.tight_layout()

        p3 = out_path / "weather_correlation.png"
        plt.savefig(p3, dpi=150)
        plt.close()
        generated_files.append(str(p3))

    return generated_files
