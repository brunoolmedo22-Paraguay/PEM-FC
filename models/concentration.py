"""
models/concentration.py
=======================
Eq. 13 do artigo OTEKON 2024.

    Vconc = a . exp(b . I)                                    [V]
    a = a1 - a2.(T - 273)
    b = 8e-3

Citados literalmente no texto do artigo, imediatamente após a Eq. 13:
    "Here the coefficients a (V) and b (cm^2.mA^-1) vary with temperature.
     a = 1.1e-4 - 1.2e-6.(T-273)
     b = 8e-3"

UNIDADE DE I: mA/cm^2 -- confirmado diretamente pelo próprio artigo, que
rotula b com unidade "cm^2.mA^-1" (não cm^2/A).

NOTA FÍSICA (não corrigida automaticamente, apenas sinalizada): o
coeficiente a se anula em T = a1/a2 + 273 ≈ 364.7 K e fica NEGATIVO
acima disso. O artigo não discute essa condição nem restringe a faixa de
T válida. is_valid_temperature() apenas verifica e sinaliza; não há
saturação automática no cálculo de V_conc -- ela é reproduzida
literalmente, mesmo quando 'a' é negativo (resultado fisicamente
inválido, mas fiel ao que a fórmula, tomada ao pé da letra, produz).
"""

from __future__ import annotations

import numpy as np

from pemfc_config.parameters import PEMFCParameters


def concentration_coefficient_a(params: PEMFCParameters) -> float:
    """a = a1 - a2.(T - 273)      [V]"""
    return params.a_1 - params.a_2 * (params.T - params.T_conc_ref)


def concentration_overpotential(
    i_mA: np.ndarray | float,
    params: PEMFCParameters,
) -> np.ndarray | float:
    """
    Eq. 13 (reprodução literal, sem saturação): Vconc = a . exp(b . I)

    Parameters
    ----------
    i_mA : densidade de corrente [mA/cm^2]
    """
    a = concentration_coefficient_a(params)
    b = params.b_conc
    i = np.asarray(i_mA, dtype=float)
    return a * np.exp(b * i)


def is_valid_temperature(params: PEMFCParameters) -> bool:
    """True se a > 0 (faixa em que a Eq. 13, como escrita, ainda é
    fisicamente sensata). Apenas diagnóstico -- não altera o cálculo."""
    return concentration_coefficient_a(params) > 0.0
