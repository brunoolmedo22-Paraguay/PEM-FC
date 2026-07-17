"""
models/ohmic.py
===============
Eq. 9, 10, 11 e 12 do artigo OTEKON 2024.

Eq. 11 (hidratação protônica, dinâmica):
    dCH+/dt + CH+/tauH+ = (1 + alphaH+ . I^3) / tauH+

Eq. 12 (condutividade, relação de Nernst-Einstein):
    sigma = (F^2/(R.T)) . DH+ . CH+                            [confirmada
    por OCR de alta resolução da imagem da fórmula: "F^2/(RT) . DH+ . CH+"]

Eq. 10 (resistência da membrana):
    Rmem = tm / sigma                                    [kΩ.cm^2]

Eq. 9 (perda ôhmica):
    Vohm = I . Rmem                                             [V]

------------------------------------------------------------------
SOBRE O "1" NA EQ. 11 -- leitura literal vs. exigência dimensional
------------------------------------------------------------------
O artigo escreve LITERALMENTE "(1 + alphaH+ . I^3)/tauH+", sem nomear um
"CH_ref" nem dar unidade para o "1". Isolada, a Eq. 11 sugere uma
variável de estado adimensional/normalizada.

Só que a Eq. 12 (sigma = F^2 D C /(RT)) é a relação de Nernst-Einstein
padrão, e ela só resulta em [S/cm] se C for uma concentração molar
[mol/cm^3] -- não um número adimensional. As duas equações, tomadas
juntas, só fecham dimensionalmente se o "1" da Eq. 11 for lido como
"1 mol/cm^3" implícito.

Esta é uma PONTE DE INTERPRETAÇÃO exigida pela própria inconsistência
interna do artigo entre Eq. 11 e Eq. 12 -- não uma afirmação explícita
do texto. Está implementada aqui como CH_BASE = 1.0 [mol/cm^3], uma
constante fixa (não um parâmetro de calibração livre).

------------------------------------------------------------------
UNIDADE DE I: mA/cm^2 (mesma convenção de todo o resto do artigo --
confirmada pela unidade kΩ.cm^2 impressa nas Eq. 8 e 10). alpha_H+ NÃO
aparece em lugar nenhum do artigo: é a única incógnita de fato livre
deste bloco (parâmetro [GAP], ver pemfc_config/parameters.py).

------------------------------------------------------------------
RESULTADO NUMÉRICO LITERAL (não uma falha desta implementação):
Com CH_BASE=1 mol/cm^3, DH+=0.85e-6 cm^2/s (Tabela 1) e T=353 K, a
Eq. 12 dá sigma ~= 2.7 S/cm -- 1-2 ordens de grandeza acima da faixa
experimental conhecida de Nafion hidratado (~0.02-0.20 S/cm, valor de
literatura geral, fora do OTEKON). Consequência: Vohm sai desprezível
(~1 mV mesmo em corrente alta) quando os números do artigo são usados
ao pé da letra. Isto é reportado, não corrigido silenciosamente.
"""

from __future__ import annotations

import numpy as np

from pemfc_config.parameters import CONSTANTS, PEMFCParameters, PhysicalConstants


def proton_concentration_steady(
    i_mA: np.ndarray | float,
    params: PEMFCParameters,
) -> np.ndarray | float:
    """
    Solução estacionária da Eq. 11:  CH+,ss = CH_BASE + alphaH+ . I^3

    Parameters
    ----------
    i_mA : densidade de corrente [mA/cm^2]
    """
    i = np.asarray(i_mA, dtype=float)
    return params.CH_BASE + params.alpha_H * i**3


def membrane_conductivity(
    c_h: np.ndarray | float,
    params: PEMFCParameters,
    const: PhysicalConstants = CONSTANTS,
) -> np.ndarray | float:
    """Eq. 12: sigma = (F^2/(R.T)) . DH+ . CH+        [S/cm]"""
    prefactor = (const.F**2) / (const.R * params.T)
    return prefactor * params.D_H * np.asarray(c_h, dtype=float)


def membrane_resistance_kOhm_cm2(
    sigma: np.ndarray | float,
    params: PEMFCParameters,
) -> np.ndarray | float:
    """
    Eq. 10: Rmem = tm/sigma, convertida para kΩ.cm^2 (unidade literal
    impressa no artigo). tm/sigma dá Ω.cm^2 diretamente (cm / (S/cm) =
    Ω.cm^2); dividimos por 1000 para chegar a kΩ.cm^2.
    """
    r_ohm_cm2 = params.t_m / np.asarray(sigma, dtype=float)
    return r_ohm_cm2 / 1000.0


def ohmic_overpotential(
    i_mA: np.ndarray | float,
    r_mem_kOhm_cm2: np.ndarray | float,
) -> np.ndarray | float:
    """
    Eq. 9: Vohm = I . Rmem       [V]

    Com I em mA/cm^2 e Rmem em kΩ.cm^2: mA . kΩ = (1e-3 A)(1e3 Ω) = A.Ω = V.
    """
    return np.asarray(i_mA, dtype=float) * np.asarray(r_mem_kOhm_cm2, dtype=float)


def ohmic_chain(
    i_mA: np.ndarray | float,
    params: PEMFCParameters,
    const: PhysicalConstants = CONSTANTS,
) -> dict:
    """Cadeia completa estacionária: I -> CH+ -> sigma -> Rmem -> Vohm."""
    c_h = proton_concentration_steady(i_mA, params)
    sigma = membrane_conductivity(c_h, params, const)
    r_mem = membrane_resistance_kOhm_cm2(sigma, params)
    v_ohm = ohmic_overpotential(i_mA, r_mem)
    return {"C_H": c_h, "sigma": sigma, "R_mem_kOhm_cm2": r_mem, "V_ohm": v_ohm}
