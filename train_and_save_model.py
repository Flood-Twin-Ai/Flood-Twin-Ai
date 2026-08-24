"""
Run this once (and any time you want to retrain) to generate synthetic
training data and save the trained model to app/models/risk_model.pkl.

Usage:
    python train_and_save_model.py
"""

from app.models.train import train_model

if __name__ == "__main__":
    train_model(n_rows=5000, seed=42)
