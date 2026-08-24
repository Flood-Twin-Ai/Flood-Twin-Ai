"""
Trains a RandomForestRegressor on synthetic flood-risk data and saves it
to risk_model.pkl. Also saves the feature order used at train time so
inference code never has to guess column ordering.
"""

import os
import sys
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.data.synthetic_data import generate_training_data

FEATURE_COLUMNS = [
    "rainfall_mm_last_1h",
    "rainfall_mm_last_6h",
    "water_level_cm",
    "drainage_capacity",
    "elevation_m",
    "historical_flood_frequency",
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.pkl")


def train_model(n_rows: int = 5000, seed: int = 42):
    df = generate_training_data(n_rows=n_rows, seed=seed)

    X = df[FEATURE_COLUMNS]
    y = df["risk_score"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"Trained on {len(X_train)} rows, tested on {len(X_test)} rows")
    print(f"MAE:  {mae:.3f}")
    print(f"R^2:  {r2:.3f}")

    feature_importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_))
    print("\nFeature importances:")
    for feat, imp in sorted(feature_importances.items(), key=lambda x: -x[1]):
        print(f"  {feat:30s} {imp:.3f}")

    joblib.dump({"model": model, "feature_columns": FEATURE_COLUMNS}, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    return model


if __name__ == "__main__":
    train_model()
