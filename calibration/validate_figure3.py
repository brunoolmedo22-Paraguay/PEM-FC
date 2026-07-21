"""Valida o único PEMFCModel contra os pontos digitalizados da Figura 3.

Uso: python calibration/validate_figure3.py
A aplicação não depende destes CSVs.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models.pemfc_model import PEMFCModel

DATA = ROOT / "data" / "otekon_figure3"


def metrics(target: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = predicted - target
    relative = np.abs(error) / np.maximum(np.abs(target), 1e-9)
    return {
        "RMSE": float(np.sqrt(np.mean(error**2))),
        "MAE": float(np.mean(np.abs(error))),
        "max_abs_error": float(np.max(np.abs(error))),
        "mean_relative_percent": float(100 * np.mean(relative)),
        "within_5_percent": float(100 * np.mean(relative <= 0.05)),
    }


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


def main() -> None:
    model = PEMFCModel()
    cases = [
        ("tensao_298K", "voltage_298K.csv", 298.15, 5.0, "V_cell_V"),
        ("tensao_373K", "voltage_373K.csv", 373.15, 5.0, "V_cell_V"),
        ("potencia_298K", "power_298K.csv", 298.15, 5.0, "P_stack_W"),
        ("potencia_373K", "power_373K.csv", 373.15, 5.0, "P_stack_W"),
        ("eficiencia_298K", "efficiency_298K.csv", 298.15, 5.0, "efficiency_percent"),
        ("eficiencia_373K", "efficiency_373K.csv", 373.15, 5.0, "efficiency_percent"),
        ("pressao_1atm", "pressure_1atm.csv", model.params.pressure_temperature_K, 1.0, "V_cell_V"),
        ("pressao_5atm", "pressure_5atm.csv", model.params.pressure_temperature_K, 5.0, "V_cell_V"),
    ]
    rows = []
    residual_rows = []
    for label, filename, T, pressure, column in cases:
        df = load(filename)
        pred = model.evaluate(df.current_density_A_cm2.to_numpy(), T, pressure)[column].to_numpy()
        m = metrics(df.value.to_numpy(), pred)
        rows.append({"case": label, **m})
        for j, target, estimate in zip(df.current_density_A_cm2, df.value, pred):
            residual_rows.append({"case": label, "current_density_A_cm2": j, "target": target, "model": estimate, "residual": estimate-target})
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "outputs" / "validation_metrics.csv", index=False)
    pd.DataFrame(residual_rows).to_csv(ROOT / "outputs" / "validation_residuals.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
