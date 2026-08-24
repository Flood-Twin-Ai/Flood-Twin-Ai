"""
Short-term forecast logic.

Given a forecasted rainfall series (e.g. next 1h, 3h, 6h rainfall in mm,
usually sourced from a weather API by Member 6) plus the current water
level, this predicts the risk trajectory at each horizon.

Kept intentionally simple for MVP explainability:
  - reuses the trained RandomForest risk model for each horizon
  - water level is extrapolated forward using a simple cumulative-rainfall
    proportional model (no hydrology simulation -- that's Member 3's job
    with the full flood simulation; this is a fast approximate signal for
    the dashboard's "next few hours" widget)
"""

import os
import joblib
from typing import List, Dict

from app.models.train import FEATURE_COLUMNS, MODEL_PATH

_model_cache = None


def _load_model():
    global _model_cache
    if _model_cache is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"No trained model found at {MODEL_PATH}. "
                f"Run `python train_and_save_model.py` first."
            )
        bundle = joblib.load(MODEL_PATH)
        _model_cache = bundle["model"]
    return _model_cache


def risk_level_from_score(score: float) -> str:
    if score <= 25:
        return "low"
    elif score <= 50:
        return "moderate"
    elif score <= 75:
        return "high"
    return "severe"


def predict_risk_score(
    rainfall_mm_last_1h: float,
    rainfall_mm_last_6h: float,
    water_level_cm: float,
    drainage_capacity: float,
    elevation_m: float,
    historical_flood_frequency: float,
) -> float:
    model = _load_model()
    row = [[
        rainfall_mm_last_1h,
        rainfall_mm_last_6h,
        water_level_cm,
        drainage_capacity,
        elevation_m,
        historical_flood_frequency,
    ]]
    score = model.predict(row)[0]
    return float(max(0.0, min(100.0, score)))


def forecast_risk_trajectory(
    zone: Dict,
    rainfall_forecast_mm: List[float],
    current_water_level_cm: float,
) -> List[Dict]:
    """
    rainfall_forecast_mm: list of forecasted rainfall (mm) for each future
    hour, e.g. [12.0, 18.0, 25.0] means +1h, +2h, +3h.

    Returns a list of {hours_ahead, predicted_risk_score, risk_level}.
    """
    drainage = zone["drainage_capacity"]
    elevation = zone["elevation_m"]
    hist_freq = zone["historical_flood_frequency"]

    results = []
    cumulative_rainfall_6h = current_water_level_cm * 0  # placeholder start
    running_water_level = current_water_level_cm
    rainfall_window = []  # rolling last-6h window approximation

    for hour_index, hourly_rainfall in enumerate(rainfall_forecast_mm, start=1):
        rainfall_window.append(hourly_rainfall)
        if len(rainfall_window) > 6:
            rainfall_window.pop(0)

        rainfall_1h = hourly_rainfall
        rainfall_6h = sum(rainfall_window)

        # crude water level extrapolation: rises with rainfall, drains
        # proportionally to drainage_capacity each hour
        inflow = hourly_rainfall * 0.8
        outflow = running_water_level * drainage * 0.3
        running_water_level = max(0.0, running_water_level + inflow - outflow)

        score = predict_risk_score(
            rainfall_mm_last_1h=rainfall_1h,
            rainfall_mm_last_6h=rainfall_6h,
            water_level_cm=running_water_level,
            drainage_capacity=drainage,
            elevation_m=elevation,
            historical_flood_frequency=hist_freq,
        )

        results.append(
            {
                "hours_ahead": hour_index,
                "predicted_risk_score": round(score, 2),
                "risk_level": risk_level_from_score(score),
            }
        )

    return results
