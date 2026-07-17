"""
calibration/flexible_model.py
==============================
Modelo PEMFC com CONVENCOES CONFIGURAVEIS, usado para testar
sistematicamente diferentes interpretacoes das Eq. 3-14 do artigo
OTEKON 2024 contra os dados digitalizados da Figura 3.

Isto NAO substitui o modelo "OTEKON literal" (pemfc_config/ + models/,
que usa exatamente as equacoes e unidades impressas). Este modulo existe
especificamente para a etapa de engenharia reversa: cada "convencao"
abaixo é uma hipotese explicita, nomeada, testavel e registrada -- nunca
uma alteracao silenciosa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
import numpy as np

R = 8.314
F = 96485.0
T_REF = 298.15


@dataclass
class Conventions:
    """Cada campo eh uma hipotese explicita sobre como o artigo pode ter
    sido implementado no MATLAB original. Ver relatorio para a lista
    completa testada."""

    # --- Eq. 4: unidade e base do logaritmo na ativacao -------------------
    activation_current_unit: Literal["A/cm2", "mA/cm2"] = "mA/cm2"
    activation_log_base: Literal["ln", "log10"] = "ln"

    # --- Eq. 3: definicao das pressoes ------------------------------------
    # "figure": usa os valores da propria legenda da Figura 3 (P_H2=1atm,
    #           P_total_cathode=5atm, p_O2=0.21*P_total)
    # "table1": usa apenas P=1.2atm (Tabela 1), com p_H2,p_O2,p_H2O GAP
    pressure_source: Literal["figure", "table1"] = "figure"
    p_h2: float = 1.0
    p_total_cathode: float = 5.0
    o2_fraction: float = 0.21
    p_h2o: float = 0.5  # ainda GAP mesmo no modo "figure" -- nao esta na legenda

    # --- Eq. 13: tratamento de a(T) acima de ~364.7K ----------------------
    aT_mode: Literal["literal", "abs", "zero_floor", "sign_flip"] = "literal"

    # --- Eq. 11/12: hidratacao -----------------------------------------
    ch_mode: Literal["steady_state", "fixed_at_1"] = "fixed_at_1"
    alpha_H: float = 0.0  # comeca desligado; testado separadamente

    # --- Ohmica: unidade de corrente e de resistencia ----------------------
    ohmic_current_unit: Literal["A/cm2", "mA/cm2"] = "mA/cm2"
    r_mem_unit: Literal["Ohm.cm2", "kOhm.cm2"] = "kOhm.cm2"

    # --- Escalamento do stack ------------------------------------------
    N_cells: float = 1.0
    A_active_cm2: float = 232.0

    # --- Definicao de eficiencia -----------------------------------------
    efficiency_ref: Literal["E_local", "1.229", "1.254", "1.481"] = "E_local"

    # --- Coeficientes (podem ser recalibrados) ----------------------------
    xi1: float = -0.9514
    xi2: float = 0.00312
    xi3: float = -0.000187
    xi4: float = 7.4e-5
    a1: float = 1.1e-4
    a2: float = 1.2e-6
    b_conc: float = 8.0e-3
    t_m: float = 0.005
    D_H: float = 0.85e-6


def nernst_E(T: float, conv: Conventions) -> float:
    if conv.pressure_source == "figure":
        p_h2 = conv.p_h2
        P = conv.p_total_cathode
        p_o2 = conv.o2_fraction * P
    else:
        p_h2, p_o2, P = 1.0, 0.21, 1.2
    p_h2o = conv.p_h2o
    thermal = 0.85e-3 * (T - T_REF)
    log_term = (R * T) / (2 * F) * np.log((p_h2 * np.sqrt(p_o2)) / (p_h2o * np.sqrt(P)))
    return 1.229 - thermal + log_term, p_o2


def oxygen_concentration(T: float, p_o2: float) -> float:
    return p_o2 / (5.08e6 * np.exp(-498.0 / T))


def activation_loss(i_A_cm2: np.ndarray, T: float, c_o2: float, conv: Conventions) -> np.ndarray:
    i_A_cm2 = np.asarray(i_A_cm2, dtype=float)
    if conv.activation_current_unit == "mA/cm2":
        i_native = np.maximum(i_A_cm2 * 1000.0, 1e-3)
    else:
        i_native = np.maximum(i_A_cm2, 1e-6)
    logf = np.log10 if conv.activation_log_base == "log10" else np.log
    e_act = conv.xi1 + conv.xi2 * T + conv.xi3 * T * logf(i_native) + conv.xi4 * T * np.log(c_o2)
    return np.maximum(-e_act, 0.0)


def ohmic_loss(i_A_cm2: np.ndarray, T: float, conv: Conventions) -> np.ndarray:
    i_A_cm2 = np.asarray(i_A_cm2, dtype=float)
    if conv.ch_mode == "fixed_at_1":
        c_h = 1.0 + conv.alpha_H * (i_A_cm2 ** 3)
    else:
        c_h = 1.0 + conv.alpha_H * (i_A_cm2 ** 3)  # steady-state == mesma forma aqui
    sigma = (F ** 2 / (R * T)) * conv.D_H * c_h  # S/cm
    r_ohm_cm2 = conv.t_m / sigma  # Ohm.cm2
    if conv.ohmic_current_unit == "mA/cm2":
        i_native = i_A_cm2 * 1000.0
        r_native = r_ohm_cm2 / 1000.0 if conv.r_mem_unit == "kOhm.cm2" else r_ohm_cm2
    else:
        i_native = i_A_cm2
        r_native = r_ohm_cm2
    return i_native * r_native


def concentration_loss(i_A_cm2: np.ndarray, T: float, conv: Conventions) -> np.ndarray:
    i_A_cm2 = np.asarray(i_A_cm2, dtype=float)
    a = conv.a1 - conv.a2 * (T - 273.0)
    if conv.aT_mode == "abs":
        a = abs(a)
    elif conv.aT_mode == "zero_floor":
        a = max(a, 0.0)
    elif conv.aT_mode == "sign_flip" and a < 0:
        a = -a
    # "literal": nao mexe, deixa a ir negativo
    i_mA = i_A_cm2 * 1000.0  # b sempre em cm2/mA (confirmado no texto do artigo)
    return a * np.exp(conv.b_conc * i_mA)


def cell_voltage(i_A_cm2: np.ndarray, T: float, conv: Conventions):
    E, p_o2 = nernst_E(T, conv)
    c_o2 = oxygen_concentration(T, p_o2)
    vact = activation_loss(i_A_cm2, T, c_o2, conv)
    vohm = ohmic_loss(i_A_cm2, T, conv)
    vconc = concentration_loss(i_A_cm2, T, conv)
    vcell = E - vact - vohm - vconc
    return dict(E=E, Vact=vact, Vohm=vohm, Vconc=vconc, Vcell=vcell)


def power_stack(i_A_cm2: np.ndarray, T: float, conv: Conventions):
    out = cell_voltage(i_A_cm2, T, conv)
    I_total = i_A_cm2 * conv.A_active_cm2
    P_stack = conv.N_cells * out["Vcell"] * I_total
    out["P_stack"] = P_stack
    out["I_total"] = I_total
    return out


def efficiency(vcell: np.ndarray, E_local: float, conv: Conventions) -> np.ndarray:
    ref = {"E_local": E_local, "1.229": 1.229, "1.254": 1.254, "1.481": 1.481}[conv.efficiency_ref]
    return 100.0 * vcell / ref
