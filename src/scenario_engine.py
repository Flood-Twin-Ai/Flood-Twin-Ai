from dataclasses import asdict
import pandas as pd
from .config import SCENARIOS

def scenario_summary():
    rows = []
    for name, s in SCENARIOS.items():
        rows.append({
            "scenario": name,
            **asdict(s),
            "severity_index": round(s.severity, 3),
        })
    return pd.DataFrame(rows)
