from pathlib import Path

import pandas as pd

from models.pemfc_model import PEMFCModel
from pemfc_config import DEFAULT_PARAMS
from simulation.solver import build_figure3_dataset
from visualization.plots import figure3_percentage_error_plotly


def _reference_data():
    root = Path(__file__).resolve().parents[1] / "data" / "otekon_figure3"
    return {
        "voltage": {
            "T_298": pd.read_csv(root / "voltage_298K.csv"),
            "T_373": pd.read_csv(root / "voltage_373K.csv"),
        },
        "power": {
            "T_298": pd.read_csv(root / "power_298K.csv"),
            "T_373": pd.read_csv(root / "power_373K.csv"),
        },
        "efficiency": {
            "T_298": pd.read_csv(root / "efficiency_298K.csv"),
            "T_373": pd.read_csv(root / "efficiency_373K.csv"),
        },
        "pressure": {
            "P_1": pd.read_csv(root / "pressure_1atm.csv"),
            "P_5": pd.read_csv(root / "pressure_5atm.csv"),
        },
    }


def test_percentage_error_plot_has_all_curves_and_nonnegative_values():
    data = build_figure3_dataset(PEMFCModel(DEFAULT_PARAMS))
    figure = figure3_percentage_error_plotly(data, _reference_data())

    assert len(figure.data) == 8
    assert all(len(trace.x) == 101 for trace in figure.data)
    assert all(min(trace.y) >= 0 for trace in figure.data)
