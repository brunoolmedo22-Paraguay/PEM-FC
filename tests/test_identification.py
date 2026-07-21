from pathlib import Path

import numpy as np
import pandas as pd

from calibration.identify_parameters import load_voltage_cases, voltage_residuals
from pemfc_config import DEFAULT_PARAMS

ROOT = Path(__file__).resolve().parents[1]


def test_default_parameters_match_reproducible_identification_output():
    table = pd.read_csv(ROOT / "outputs" / "identified_parameters.csv")
    identified = dict(zip(table.parameter, table.identified_value))
    names = (
        "xi1",
        "xi2",
        "xi3",
        "xi4",
        "R_mem_ref_ohm_cm2",
        "R_mem_temperature_exponent",
        "concentration_a_ref_V",
        "concentration_a_temperature_V_K",
        "concentration_b_cm2_A",
        "fuel_utilization",
        "N_cells",
    )
    for name in names:
        assert np.isclose(getattr(DEFAULT_PARAMS, name), identified[name], rtol=1e-8, atol=1e-12)


def test_primary_voltage_identification_rmse_is_below_two_millivolts():
    vector_names = (
        "xi1",
        "xi2",
        "xi3",
        "xi4",
        "R_mem_ref_ohm_cm2",
        "R_mem_temperature_exponent",
        "concentration_a_ref_V",
        "concentration_a_temperature_V_K",
        "concentration_b_cm2_A",
    )
    vector = np.array([getattr(DEFAULT_PARAMS, name) for name in vector_names])
    residual_V = voltage_residuals(vector, load_voltage_cases(), sigma_V=1.0)
    assert np.sqrt(np.mean(residual_V**2)) < 0.002


def test_optimization_artifacts_are_present():
    required = (
        "identified_parameters.csv",
        "optimization_runs.csv",
        "optimization_residuals.csv",
        "parameter_correlation.csv",
        "optimization_summary.json",
        "optimization_report.md",
        "optimization_flowchart.png",
        "optimization_flowchart.svg",
    )
    assert all((ROOT / "outputs" / name).exists() for name in required)
