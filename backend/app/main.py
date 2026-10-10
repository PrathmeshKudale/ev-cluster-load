"""EV cluster load API: demo data, P10/P50/P90 forecast, transformer risk, recommendations."""
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

TRANSFORMER_KVA, PF, WARN, CRIT = 100.0, 0.95, 0.80, 0.90
SESSION_H = 1.0  # mean charging session, hours
STATIONS = [
    {"id": "S1", "name": "Market Road", "chargers": 8, "kw": 7.4, "pop": 1.25, "detour": 0},
    {"id": "S2", "name": "Station Plaza", "chargers": 6, "kw": 7.4, "pop": 0.90, "detour": 4},
    {"id": "S3", "name": "College Gate", "chargers": 6, "kw": 7.4, "pop": 0.60, "detour": 7},
    {"id": "S4", "name": "Ring Road Hub", "chargers": 4, "kw": 7.4, "pop": 0.50, "detour": 10},
]
# weights: wait, detour, imbalance, overload risk
MODES = {"fastest": (0.60, 0.15, 0.10, 0.15), "balanced": (0.35, 0.20, 0.25, 0.20),
         "grid_friendly": (0.20, 0.15, 0.30, 0.35)}
DELAY_W = 0.20


from app.ml.forecast import compute_forecasts

CLUSTER_PCT, STATION_UTIL, MODEL_VERSION = compute_forecasts(STATIONS, TRANSFORMER_KVA, PF)


def erlang_c_wait_min(c, util):
    """Mean queue wait in minutes for an M/M/c charging site; util in 0..1."""
    a = min(util, 0.995) * c
    term, total = 1.0, 1.0
    for k in range(1, c):
        term *= a / k
        total += term
    top = term * a / c / (1 - a / c)
    return min(top / (total + top) * SESSION_H / (c - a) * 60, 90.0)


def level(p):
    return "critical" if p > CRIT else "warning" if p > WARN else "ok"


app = FastAPI(title="EV Cluster Load API")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/cluster")
def cluster():
    return {"transformer_kva": TRANSFORMER_KVA, "power_factor": PF, "stations": STATIONS}


@app.get("/api/forecast")
def forecast(start_hour: int = 14):
    hrs = [(start_hour + i) % 24 for i in range(24)]
    pick = lambda arr: [round(float(arr[h]) * 100, 1) for h in hrs]
    return {"hours": hrs, "p10": pick(CLUSTER_PCT[0]), "p50": pick(CLUSTER_PCT[1]),
            "p90": pick(CLUSTER_PCT[2]), "warn": 80, "critical": 90}


@app.get("/api/transformer")
def transformer(start_hour: int = 14):
    f = forecast(start_hour)
    peak = max(f["p90"])
    return {"kva": TRANSFORMER_KVA, "peak_p90_pct": peak, "peak_hour": f["hours"][f["p90"].index(peak)],
            "first_warning_hour": next((h for h, v in zip(f["hours"], f["p90"]) if v > 80), None),
            "level": level(peak / 100)}


class Req(BaseModel):
    mode: str = "balanced"
    start_hour: int = 14
    horizon: int = 12


@app.post("/api/recommend")
def recommend(r: Req):
    w = MODES.get(r.mode, MODES["balanced"])
    hz = max(1, min(r.horizon, 24))
    cands = []
    for off in range(hz):
        h = (r.start_hour + off) % 24
        grid = float(CLUSTER_PCT[2][h]) * 100
        risk = float(np.clip((grid / 100 - WARN) / (1 - WARN), 0, 1))
        mean_u = float(np.mean([STATION_UTIL[i][2][h] for i in STATION_UTIL]))
        for s in STATIONS:
            u = float(STATION_UTIL[s["id"]][2][h])
            wait = erlang_c_wait_min(s["chargers"], u)
            j = (w[0] * wait / 60 + w[1] * s["detour"] / 15 + w[2] * max(u - mean_u, 0)
                 + w[3] * risk + DELAY_W * off / hz)
            cands.append({"station": s["name"], "station_id": s["id"], "hour": h, "starts_in_h": off,
                          "wait_min": round(wait, 1), "detour_min": s["detour"],
                          "grid_load_pct": round(grid, 1), "score": round(j, 3)})
    ok = [c for c in cands if c["grid_load_pct"] <= CRIT * 100] or cands  # hard transformer constraint
    best = {}
    for c in sorted(ok, key=lambda c: c["score"]):
        best.setdefault(c["station_id"], c)
    return {"mode": r.mode, "top3": list(best.values())[:3]}


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend", html=True), name="ui")
