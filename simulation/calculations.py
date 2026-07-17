"""
simulation/calculations.py
==========================
Pos-processamento: potencia, eficiencia, ponto de maxima potencia,
consumo de hidrogenio e balanco de perdas.

IMPORTANTE: nada neste modulo e uma equacao do artigo OTEKON 2024. Sao
EXTENSOES desta implementacao, baseadas em relacoes eletroquimicas
padrao (termodinamica de celulas a combustivel, lei de Faraday), citadas
como tal na interface. Mantido separado de models/ para nao misturar
"o que o artigo diz" com "o que foi acrescentado por conveniencia de
engenharia".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pemfc_config.parameters import CONSTANTS, PEMFCParameters, PhysicalConstants

# Potenciais termoneutros do H2 -- valores termodinamicos padrao de
# literatura geral de celulas a combustivel (ex. O'Hayre et al., Barbir),
# NAO citados no artigo OTEKON.
E_HHV = 1.481   # [V] poder calorifico superior
E_LHV = 1.254   # [V] poder calorifico inferior
MOLAR_MASS_H2 = 2.016  # [g/mol]


def add_power_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "P_stack [W]" not in df:
        df["P_stack [W]"] = df["V_stack [V]"] * df["I [A]"]
    return df


def add_efficiency_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    eta_HHV = V_cell / 1.481 ; eta_LHV = V_cell / 1.254

    EXTENSAO (nao esta no OTEKON). Relacao padrao: a eficiencia de uma
    celula a combustivel e a razao entre a tensao real e o potencial
    termoneutro correspondente ao poder calorifico do combustivel.
    """
    df["eta_HHV [-]"] = df["V_cell [V]"] / E_HHV
    df["eta_LHV [-]"] = df["V_cell [V]"] / E_LHV
    return df


def add_hydrogen_consumption(
    df: pd.DataFrame,
    params: PEMFCParameters,
    const: PhysicalConstants = CONSTANTS,
) -> pd.DataFrame:
    """
    Consumo ESTEQUIOMETRICO IDEAL de H2 (lei de Faraday), sem excesso
    estequiometrico nem purga:

        n_H2 = N . I / (2F)             [mol/s]
        m_H2 = n_H2 . M_H2 . 3600       [g/h]

    EXTENSAO (nao esta no OTEKON). Lei de Faraday padrao, nao especifica
    deste artigo.
    """
    n_dot = params.N_cells * df["I [A]"] / (const.n_electrons * const.F)
    df["H2 [mol/s]"] = n_dot
    df["H2 [g/h]"] = n_dot * MOLAR_MASS_H2 * 3600.0
    return df


def maximum_power_point(df: pd.DataFrame) -> dict:
    idx = int(np.nanargmax(df["P_stack [W]"].values))
    row = df.iloc[idx]
    return {
        "I [A]": float(row["I [A]"]),
        "i [mA/cm2]": float(row["i [mA/cm2]"]),
        "V_stack [V]": float(row["V_stack [V]"]),
        "V_cell [V]": float(row["V_cell [V]"]),
        "P_stack [W]": float(row["P_stack [W]"]),
        "P_density [W/cm2]": float(row["P_density [W/cm2]"]),
    }


def loss_breakdown_at(df: pd.DataFrame, current_A: float) -> dict:
    idx = int(np.argmin(np.abs(df["I [A]"].values - current_A)))
    row = df.iloc[idx]
    total = row["V_act [V]"] + row["V_ohm [V]"] + row["V_conc [V]"]
    total = total if total > 0 else np.nan
    return {
        "I [A]": float(row["I [A]"]),
        "E [V]": float(row["E [V]"]),
        "V_act [V]": float(row["V_act [V]"]),
        "V_ohm [V]": float(row["V_ohm [V]"]),
        "V_conc [V]": float(row["V_conc [V]"]),
        "V_cell [V]": float(row["V_cell [V]"]),
        "share_act [%]": float(100 * row["V_act [V]"] / total),
        "share_ohm [%]": float(100 * row["V_ohm [V]"] / total),
        "share_conc [%]": float(100 * row["V_conc [V]"] / total),
    }


def enrich(df: pd.DataFrame, params: PEMFCParameters) -> pd.DataFrame:
    """Pipeline completo de pos-processamento (extensoes, ver acima)."""
    df = add_power_columns(df)
    df = add_efficiency_columns(df)
    df = add_hydrogen_consumption(df, params)
    return df
