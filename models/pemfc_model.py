"""
models/pemfc_model.py
=====================
Orquestrador. Monta a Eq. 2 e a Eq. 14 do artigo:

    Vcell  = E - Vact - Vohm - Vconc          (Eq. 2)
    Vstack = N . Vcell                         (Eq. 14)

Toda densidade de corrente interna ao modelo está em mA/cm^2 (ver nota
de unidades em models/activation.py e models/ohmic.py). A interface
externa (steady_state, polarization_curve) recebe CORRENTE TOTAL [A] e
faz a conversão via params.current_to_density_mA().

DESIGN PARA EXTENSÃO FUTURA
----------------------------
BasePEMFCModel define o contrato mínimo para qualquer modelo PEMFC.
PEMFCModel é a implementação fiel do OTEKON 2024. Para adicionar outro
modelo (Amphlett 1995 completo, Ballard Mark V, um equipamento real
calibrado por datasheet, etc.), basta herdar de BasePEMFCModel -- a app,
o solver e os gráficos não mudam.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import numpy as np
import pandas as pd

from pemfc_config.parameters import CONSTANTS, DEFAULT_PARAMS, PEMFCParameters, PhysicalConstants
from models.activation import (
    activation_overpotential,
    activation_resistance_kOhm_cm2,
    tafel_slope,
)
from models.concentration import (
    concentration_coefficient_a,
    concentration_overpotential,
    is_valid_temperature,
)
from models.dynamics import simulate_transient
from models.nernst import nernst_voltage, oxygen_concentration
from models.ohmic import ohmic_chain


class BasePEMFCModel(ABC):
    """Contrato comum a todos os modelos PEMFC do simulador."""

    def __init__(
        self,
        params: PEMFCParameters = DEFAULT_PARAMS,
        const: PhysicalConstants = CONSTANTS,
    ) -> None:
        self.params = params
        self.const = const

    @abstractmethod
    def reversible_voltage(self) -> float: ...

    @abstractmethod
    def losses(self, i_mA: np.ndarray | float) -> dict: ...

    def cell_voltage(self, i_mA: np.ndarray | float) -> np.ndarray | float:
        """Eq. 2: Vcell = E - Vact - Vohm - Vconc."""
        losses = self.losses(i_mA)
        return (
            self.reversible_voltage()
            - losses["V_act"]
            - losses["V_ohm"]
            - losses["V_conc"]
        )

    def stack_voltage(self, i_mA: np.ndarray | float) -> np.ndarray | float:
        """Eq. 14: Vstack = N . Vcell."""
        return self.params.N_cells * self.cell_voltage(i_mA)


class PEMFCModel(BasePEMFCModel):
    """Implementação fiel do modelo do artigo OTEKON 2024."""

    model_id = "otekon_2024"
    model_label = "OTEKON 2024 — Altıntaş & Ertan"

    # ------------------------------------------------------------------
    def reversible_voltage(self) -> float:
        """Eq. 3."""
        return nernst_voltage(self.params, self.const)

    def oxygen_concentration(self) -> float:
        """Eq. 5."""
        return oxygen_concentration(self.params)

    def losses(self, i_mA: np.ndarray | float) -> dict:
        """
        As três quedas de tensão em regime estacionário.

        Parameters
        ----------
        i_mA : densidade de corrente [mA/cm^2] -- unidade nativa do
               modelo inteiro (Eq. 4, 8, 9, 10, 11, 13).
        """
        i_mA = np.asarray(i_mA, dtype=float)
        c_o2 = self.oxygen_concentration()

        v_act = activation_overpotential(i_mA, c_o2, self.params)          # Eq. 4/6
        ohm = ohmic_chain(i_mA, self.params, self.const)                   # Eq. 9-12
        v_conc = concentration_overpotential(i_mA, self.params)            # Eq. 13

        return {
            "i_mA": i_mA,
            "C_O2": c_o2,
            "V_act": v_act,
            "R_act_kOhm_cm2": activation_resistance_kOhm_cm2(v_act, i_mA),
            "C_H": ohm["C_H"],
            "sigma": ohm["sigma"],
            "R_mem_kOhm_cm2": ohm["R_mem_kOhm_cm2"],
            "V_ohm": ohm["V_ohm"],
            "V_conc": v_conc,
        }

    # ------------------------------------------------------------------
    def steady_state(self, current_A: float) -> dict:
        """Ponto de operação a partir da CORRENTE TOTAL [A]."""
        p = self.params
        i_mA = p.current_to_density_mA(current_A)

        losses = self.losses(i_mA)
        e_rev = self.reversible_voltage()

        v_cell = e_rev - losses["V_act"] - losses["V_ohm"] - losses["V_conc"]
        v_stack = v_cell * p.N_cells

        return {
            "I_A": current_A,
            "i_mA_cm2": float(i_mA),
            "E_nernst": e_rev,
            "V_act": float(losses["V_act"]),
            "V_ohm": float(losses["V_ohm"]),
            "V_conc": float(losses["V_conc"]),
            "V_cell": float(v_cell),
            "V_stack": float(v_stack),
            "P_stack": float(v_stack * current_A),
            "sigma": float(losses["sigma"]),
            "R_mem_kOhm_cm2": float(losses["R_mem_kOhm_cm2"]),
            "R_act_kOhm_cm2": float(losses["R_act_kOhm_cm2"]),
            "C_H": float(losses["C_H"]),
            "C_O2": float(losses["C_O2"]),
        }

    def polarization_curve(self, current_A: np.ndarray) -> pd.DataFrame:
        """Curva de polarização completa a partir de um vetor de CORRENTE
        TOTAL [A]."""
        p = self.params
        current_A = np.asarray(current_A, dtype=float)
        i_mA = p.current_to_density_mA(current_A)

        e_rev = self.reversible_voltage()
        losses = self.losses(i_mA)

        v_cell = e_rev - losses["V_act"] - losses["V_ohm"] - losses["V_conc"]
        v_stack = v_cell * p.N_cells

        return pd.DataFrame(
            {
                "I [A]": current_A,
                "i [mA/cm2]": i_mA,
                "E [V]": np.full_like(current_A, e_rev),
                "V_act [V]": losses["V_act"],
                "V_ohm [V]": losses["V_ohm"],
                "V_conc [V]": losses["V_conc"],
                "V_cell [V]": v_cell,
                "V_stack [V]": v_stack,
                "P_stack [W]": v_stack * current_A,
                "P_density [W/cm2]": v_cell * i_mA / 1000.0,
                "sigma [S/cm]": losses["sigma"],
                "R_mem [kOhm.cm2]": losses["R_mem_kOhm_cm2"],
                "R_act [kOhm.cm2]": losses["R_act_kOhm_cm2"],
                "C_H [mol/cm3]": losses["C_H"],
            }
        )

    def transient(
        self,
        current_profile_mA: Callable[[float], float],
        t_span: tuple[float, float] = (0.0, 60.0),
        n_points: int = 2000,
    ) -> dict:
        """Resposta dinâmica (Eq. 7 + Eq. 11) a um perfil i(t) [mA/cm^2]."""
        return simulate_transient(
            current_profile_mA=current_profile_mA,
            params=self.params,
            e_nernst=self.reversible_voltage(),
            c_o2=self.oxygen_concentration(),
            t_span=t_span,
            n_points=n_points,
            const=self.const,
        )

    # ------------------------------------------------------------------
    def diagnostics(self) -> dict:
        """Indicadores de plausibilidade (não são cálculos do artigo)."""
        p = self.params
        sigma0 = (self.const.F**2 / (self.const.R * p.T)) * p.D_H * p.CH_BASE
        sigma_typical_min, sigma_typical_max = 0.02, 0.20  # faixa geral de
        # literatura para Nafion hidratado, citada de memória, FORA do
        # OTEKON -- apenas para contextualizar a magnitude, não é um
        # critério do artigo.

        return {
            "E_nernst [V]": self.reversible_voltage(),
            "C_O2 [mol/cm3]": self.oxygen_concentration(),
            "Tafel slope [V/dec]": tafel_slope(p),
            "sigma @ I=0 [S/cm]": sigma0,
            "R_mem @ I=0 [kOhm.cm2]": p.t_m / sigma0 / 1000.0,
            "C_dl_total [F]": p.C_dl_total,
            "a_conc(T) [V]": concentration_coefficient_a(p),
            "conc_model_valid": is_valid_temperature(p),
            "sigma_fora_da_faixa_tipica": not (sigma_typical_min <= sigma0 <= sigma_typical_max),
        }
