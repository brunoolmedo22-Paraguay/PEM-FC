from __future__ import annotations

import numpy as np
import pandas as pd

from models.pemfc_model import PEMFCModel


def build_figure3_dataset(model: PEMFCModel, points: int = 240) -> dict[str, pd.DataFrame]:
    return model.figure3_data(points=points)


def sensitivity_temperature(model: PEMFCModel, current_density_A_cm2: float, temperatures_K) -> pd.DataFrame:
    temperatures = np.asarray(temperatures_K, dtype=float)
    rows = []
    for T in temperatures:
        row = model.evaluate(np.array([current_density_A_cm2]), float(T), 5.0).iloc[0]
        rows.append(row)
    return pd.DataFrame(rows)


def sensitivity_pressure(model: PEMFCModel, current_density_A_cm2: float, pressures_atm) -> pd.DataFrame:
    pressures = np.asarray(pressures_atm, dtype=float)
    rows = []
    for pressure in pressures:
        row = model.evaluate(
            np.array([current_density_A_cm2]),
            model.params.pressure_temperature_K,
            float(pressure),
        ).iloc[0]
        rows.append(row)
    return pd.DataFrame(rows)
