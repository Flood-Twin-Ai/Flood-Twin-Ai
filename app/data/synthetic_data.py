"""
Synthetic data generator for FloodTwin AI risk model training.

Generates realistic-ish rainfall / water-level / drainage scenarios per zone.
Relationship baked in (with noise so it's not trivially linear):

    risk_score UP when:
        - rainfall_mm_last_1h is high
        - rainfall_mm_last_6h is high (soil/drainage already saturated)
        - water_level_cm is high
        - drainage_capacity is LOW
        - elevation_m is LOW
        - historical_flood_frequency is high

This file has zero external dependencies beyond numpy/pandas, and does not
need real sensor data to run -- it is a stand-in until Member 6 (Data/IoT)
wires up real feeds. The output schema is intentionally identical to what
the live API will receive, so swapping this out later is a drop-in change.
"""

import json
import os
import numpy as np
import pandas as pd

ZONES_PATH = os.path.join(os.path.dirname(__file__), "zones.json")


def load_zones():
    with open(ZONES_PATH, "r") as f:
        return json.load(f)


def _risk_formula(rainfall_1h, rainfall_6h, water_level, drainage, elevation, hist_freq, rng):
    """
    Deterministic-ish core formula + gaussian noise + a couple of nonlinear
    interaction terms so a plain linear regressor can't trivially ace it.
    Output is clipped to [0, 100].
    """
    # normalize elevation roughly (assume 0-25m range city)
    elev_norm = np.clip(elevation / 25.0, 0, 1)

    base = (
        0.35 * np.clip(rainfall_1h / 60.0, 0, 1) * 100      # heavy short burst
        + 0.20 * np.clip(rainfall_6h / 150.0, 0, 1) * 100   # saturation
        + 0.20 * np.clip(water_level / 200.0, 0, 1) * 100   # river/drain level
        + 0.15 * (1 - drainage) * 100                        # poor drainage
        + 0.10 * hist_freq * 100                             # historical prior
    )

    # nonlinear penalty: low elevation + low drainage compounds badly
    compounding = (1 - elev_norm) * (1 - drainage) * 25

    # nonlinear boost: very high rainfall_1h overwhelms drainage regardless
    overwhelm = 0
    if rainfall_1h > 45:
        overwhelm = (rainfall_1h - 45) * (1 - drainage) * 1.5

    noise = rng.normal(0, 6)  # sensor + randomness noise

    score = base + compounding + overwhelm + noise
    return float(np.clip(score, 0, 100))


def generate_training_data(n_rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    zones = load_zones()

    rows = []
    for _ in range(n_rows):
        zone = zones[rng.integers(0, len(zones))]

        # simulate a plausible weather scenario
        # occasionally simulate a "storm event" for higher-risk samples
        is_storm = rng.random() < 0.30
        if is_storm:
            rainfall_1h = float(rng.uniform(20, 90))
            rainfall_6h = rainfall_1h + float(rng.uniform(20, 120))
            water_level = float(rng.uniform(60, 220))
        else:
            rainfall_1h = float(rng.uniform(0, 25))
            rainfall_6h = rainfall_1h + float(rng.uniform(0, 40))
            water_level = float(rng.uniform(5, 80))

        drainage = zone["drainage_capacity"]
        elevation = zone["elevation_m"]
        hist_freq = zone["historical_flood_frequency"]

        risk = _risk_formula(
            rainfall_1h, rainfall_6h, water_level, drainage, elevation, hist_freq, rng
        )

        rows.append(
            {
                "zone_id": zone["zone_id"],
                "rainfall_mm_last_1h": round(rainfall_1h, 2),
                "rainfall_mm_last_6h": round(rainfall_6h, 2),
                "water_level_cm": round(water_level, 2),
                "drainage_capacity": drainage,
                "elevation_m": elevation,
                "historical_flood_frequency": hist_freq,
                "risk_score": round(risk, 2),
            }
        )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_training_data()
    print(df.head(10))
    print(f"\nGenerated {len(df)} rows")
    print(df["risk_score"].describe())
