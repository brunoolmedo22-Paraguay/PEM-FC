"""
simulation/solver.py
====================
Camada de simulação: orquestra varreduras estacionárias e simulações
temporais. Não contém física (vive em models/) nem interface (app.py).
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from pemfc_config.parameters import PEMFCParameters
from models.dynamics import ramp_profile, step_profile
from models.pemfc_model import PEMFCModel


def build_current_vector(
    i_min_A: float,
    i_max_A: float,
    n_points: int,
    log_spacing: bool = False,
) -> np.ndarray:
    """Vetor de corrente TOTAL [A] para a varredura."""
    i_min_A = max(i_min_A, 1e-4)
    if log_spacing:
        return np.logspace(np.log10(i_min_A), np.log10(i_max_A), n_points)
    return np.linspace(i_min_A, i_max_A, n_points)


def run_polarization(
    params: PEMFCParameters,
    i_min_A: float,
    i_max_A: float,
    n_points: int = 200,
    log_spacing: bool = False,
) -> pd.DataFrame:
    """Executa a varredura estacionária (Eq. 2-14) e devolve a curva V-I."""
    model = PEMFCModel(params)
    current = build_current_vector(i_min_A, i_max_A, n_points, log_spacing)
    return model.polarization_curve(current)


def run_transient(
    params: PEMFCParameters,
    profile_type: str,
    i_low_A: float,
    i_high_A: float,
    t_final: float,
    t_event: float,
    t_event_end: float | None = None,
    n_points: int = 2000,
) -> dict:
    """
    Executa uma simulação temporal (Eq. 7 + Eq. 11).

    i_low_A, i_high_A : corrente TOTAL [A] antes/depois do evento.
    """
    model = PEMFCModel(params)

    i_low_mA = params.current_to_density_mA(i_low_A)
    i_high_mA = params.current_to_density_mA(i_high_A)

    if profile_type == "ramp":
        t_end = t_event_end if t_event_end is not None else t_final
        profile: Callable[[float], float] = ramp_profile(i_low_mA, i_high_mA, t_event, t_end)
    else:
        profile = step_profile(i_low_mA, i_high_mA, t_event)

    return model.transient(profile, t_span=(0.0, t_final), n_points=n_points)
