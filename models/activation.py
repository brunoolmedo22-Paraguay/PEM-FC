"""
models/activation.py
====================
Eq. 4, 6 e 8 do artigo OTEKON 2024.

Eq. 4 (Tafel semi-empírico):
    Eact = xi1 + xi2*T + xi3*T*ln(I) + xi4*T*ln(CO2)          [V]
    (coeficientes xi1..xi4 citados literalmente no texto do artigo)

Eq. 6:
    Vact = -Eact                                              [V]

Eq. 8:
    Ract = Vact / I                                     [kΩ.cm^2]

UNIDADE DE I: mA/cm^2. Confirmado por três evidências textuais
independentes do artigo (não é uma escolha desta implementação):
  1. O texto diz explicitamente "I is the current density".
  2. A Eq. 8 é rotulada com unidade "kΩ.cm^2" -- só surge de V/(mA/cm^2).
  3. A Eq. 13 usa b com unidade "cm^2.mA^-1", confirmando mA/cm^2 no
     mesmo símbolo I em outra equação do mesmo artigo.

REGULARIZAÇÃO NUMÉRICA (não está no artigo, documentada como tal):
  - i_min_mA: piso de corrente para evitar ln(0) -> -inf quando I->0.
  - clipping V_act >= 0: a correlação Eq. 4, extrapolada para I muito
    próximo de zero, pode produzir Eact>0 (isto é, Vact<0), o que
    inverteria o sinal de uma "perda". Fisicamente inválido; sem essa
    saturação o circuito aberto (OCV) sairia MAIOR que E (Nernst), o que
    viola a própria Eq. 2 do artigo (Vcell = E - Vact - Vohm - Vconc,
    que pressupõe todas as quedas >= 0). A correlação empírica da Eq. 4
    simplesmente não foi ajustada para correntes extremamente baixas.
"""

from __future__ import annotations

import numpy as np

from pemfc_config.parameters import PEMFCParameters


def activation_overpotential(
    i_mA: np.ndarray | float,
    c_o2: float,
    params: PEMFCParameters,
) -> np.ndarray | float:
    """
    Eq. 4 + Eq. 6. Sobrepotencial de ativação em regime estacionário.

    Parameters
    ----------
    i_mA : densidade de corrente [mA/cm^2]  (ver nota de unidade acima)
    c_o2 : concentração de O2 [mol/cm^3]  (Eq. 5)
    """
    T = params.T

    i_safe = np.maximum(np.asarray(i_mA, dtype=float), params.i_min_mA)

    e_act = (
        params.xi1
        + params.xi2 * T
        + params.xi3 * T * np.log(i_safe)
        + params.xi4 * T * np.log(c_o2)
    )

    v_act = -e_act  # Eq. 6

    # Regularização numérica (ver docstring do módulo). NÃO está na Eq. 4/6.
    return np.maximum(v_act, 0.0)


def activation_resistance_kOhm_cm2(
    v_act: np.ndarray | float,
    i_mA: np.ndarray | float,
    i_floor_mA: float = 1e-3,
) -> np.ndarray | float:
    """
    Eq. 8. Ract = Vact / I, unidade kΩ.cm^2 (literal, como no artigo).

    Parameters
    ----------
    v_act : sobrepotencial de ativação estacionário [V]
    i_mA  : densidade de corrente [mA/cm^2]
    """
    i_safe = np.maximum(np.asarray(i_mA, dtype=float), i_floor_mA)
    return v_act / i_safe


def tafel_slope(params: PEMFCParameters) -> float:
    """
    Pendente de Tafel implícita no modelo [V/década], não é uma equação
    do artigo -- é uma métrica de diagnóstico derivada do coeficiente
    xi3 para checar plausibilidade física (faixa típica PEMFC: 0.04-0.12
    V/dec segundo a literatura eletroquímica padrão, fora do OTEKON).

        b_Tafel = -xi3 * T * ln(10)
    """
    return -params.xi3 * params.T * np.log(10.0)
