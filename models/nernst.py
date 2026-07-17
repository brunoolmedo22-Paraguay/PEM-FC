"""
models/nernst.py
================
Eq. 3 e Eq. 5 do artigo OTEKON 2024.

Eq. 3 (potencial reversível, Nernst com correção térmica) -- confirmada
por OCR de alta resolução da imagem da fórmula (image3.wmf do .docx
original), que mostra literalmente:

    E = E0 - 0.85e-3(T - 298.15) + (RT/2F) * ln[ (PH2 . PO2^0.5)
                                                    / (PH2O . P^0.5) ]

Eq. 5 (concentração de oxigênio, lei de Henry), texto simbólico dado
diretamente no corpo do artigo:

    CO2 = PO2 / (5.08e6 * exp(-498/T))    [mol.cm^-3]
"""

from __future__ import annotations

import numpy as np

from pemfc_config.parameters import CONSTANTS, PEMFCParameters, PhysicalConstants


def nernst_voltage(
    params: PEMFCParameters,
    const: PhysicalConstants = CONSTANTS,
) -> float:
    """
    Eq. 3 do artigo. Potencial reversível de circuito aberto de UMA célula.

    p_h2, p_o2, p_h2o são parâmetros [GAP] (ver pemfc_config/parameters.py):
    o artigo cita essas pressões parciais na Eq. 3 mas não fornece seus
    valores numéricos na Tabela 1.
    """
    T = params.T

    thermal_term = 0.85e-3 * (T - const.T_ref)

    numerator = params.p_h2 * np.sqrt(params.p_o2)
    denominator = params.p_h2o * np.sqrt(params.P)

    nernst_term = (const.R * T) / (2 * const.F) * np.log(numerator / denominator)

    return params.E0 - thermal_term + nernst_term


def oxygen_concentration(params: PEMFCParameters) -> float:
    """
    Eq. 5 do artigo. Concentração de O2 na interface catalítica.

    CO2 = PO2 / (5.08e6 * exp(-498/T))      [mol/cm^3]
    """
    henry_coefficient = params.k_henry * np.exp(-params.e_henry / params.T)
    return params.p_o2 / henry_coefficient
