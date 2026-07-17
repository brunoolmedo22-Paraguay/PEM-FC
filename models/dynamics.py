"""
models/dynamics.py
==================
Eq. 7 e Eq. 11 do artigo OTEKON 2024 -- os dois estados dinâmicos.

Eq. 7 (dupla camada):
    dVact/dt = I/Cdl - Vact/(Ract.Cdl)

Eq. 11 (hidratação, ver models/ohmic.py para a discussão completa do "1"):
    dCH+/dt + CH+/tauH+ = (1 + alphaH+.I^3)/tauH+

====================================================================
PONTE DE UNIDADES NA EQ. 7 -- leia isto antes de usar o transitório
====================================================================
A Tabela 1 dá Cdl = "0.035 x 232 F", ou seja, um número TOTAL (8.12 F)
para a célula específica do artigo. Mas o texto diz "I is the current
density" (mA/cm^2, ver models/activation.py). Substituir I [mA/cm^2]
diretamente em I/Cdl com Cdl=8.12 F NÃO fecha dimensionalmente
(mA/cm^2 dividido por F não é V/s).

O artigo não explicita a conversão. A única forma de tornar a Eq. 7
executável com os PRÓPRIOS números do artigo (Cdl total da Tabela 1,
Ract específico em kΩ.cm^2 da Eq. 8) é reconverter ambos para uma base
consistente. Implementamos a ponte MÍNIMA necessária:

    I_total [A]      = i [mA/cm^2] / 1000 * A_active [cm^2]
    Ract_total [Ω]   = Ract [kΩ.cm^2] * 1000 / A_active [cm^2]
    Cdl_total [F]    = C_dl_specific [F/cm^2] * A_active [cm^2]
                        (= 8.12 F exatos quando A_active = 232 cm^2,
                         batendo com a Tabela 1)

    dVact/dt = I_total/Cdl_total - Vact/(Ract_total . Cdl_total)

Verificação de plausibilidade (não é validação contra o artigo, apenas
checagem de sanidade): com esta ponte, tau_dl = Ract_total*Cdl_total
sai na faixa de dezenas de milissegundos para correntes moderadas --
consistente com constantes de tempo de dupla camada normalmente citadas
na literatura eletroquímica geral (não no OTEKON). Isso é um indício
de que a ponte escolhida é razoável, não uma confirmação do artigo.

Este é o único bloco do modelo em que uma interpretação própria foi
necessária para tornar a equação executável. Está isolado neste módulo
e não contamina os demais (ativação, ôhmico, concentração, Nernst
permanecem em mA/cm^2 puro, sem qualquer ponte).
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp

from pemfc_config.parameters import CONSTANTS, PEMFCParameters, PhysicalConstants
from models.activation import activation_overpotential, activation_resistance_kOhm_cm2
from models.ohmic import (
    membrane_conductivity,
    membrane_resistance_kOhm_cm2,
    ohmic_overpotential,
    proton_concentration_steady,
)


def state_derivatives(
    t: float,
    x: np.ndarray,
    current_density_mA: Callable[[float], float],
    c_o2: float,
    params: PEMFCParameters,
) -> list[float]:
    """
    Campo vetorial do sistema [V_act, C_H].

    current_density_mA : i(t) em [mA/cm^2] (unidade nativa de todo o
    modelo, ver nota de unidades em models/activation.py).
    """
    v_act, c_h = x

    i_mA = max(float(current_density_mA(t)), 0.0)

    # --- Eq. 11: hidratação (mesma unidade mA/cm^2 de todo o resto) -----
    c_h_ss = float(proton_concentration_steady(i_mA, params))
    dc_h_dt = (c_h_ss - c_h) / params.tau_H

    # --- Eq. 7: dupla camada, com a ponte de unidades documentada acima -
    v_act_ss = float(activation_overpotential(i_mA, c_o2, params))
    r_act_kOhm_cm2 = float(activation_resistance_kOhm_cm2(v_act_ss, i_mA))

    A = params.A_active
    i_total_A = i_mA / 1000.0 * A
    r_act_total_ohm = r_act_kOhm_cm2 * 1000.0 / A
    c_dl_total_F = params.C_dl_total  # = C_dl_specific * A_active

    dv_act_dt = i_total_A / c_dl_total_F - v_act / (r_act_total_ohm * c_dl_total_F)

    return [dv_act_dt, dc_h_dt]


def simulate_transient(
    current_profile_mA: Callable[[float], float],
    params: PEMFCParameters,
    e_nernst: float,
    c_o2: float,
    t_span: tuple[float, float] = (0.0, 60.0),
    n_points: int = 2000,
    x0: tuple[float, float] | None = None,
    const: PhysicalConstants = CONSTANTS,
) -> dict:
    """
    Integra a resposta temporal ante um perfil de corrente i(t) [mA/cm^2].

    Returns
    -------
    dict com t, i_mA, I_A, V_act, C_H, sigma, R_mem_kOhm_cm2, V_ohm,
    V_conc, V_cell, V_stack, P_stack.
    """
    from models.concentration import concentration_overpotential

    if x0 is None:
        i0_mA = max(float(current_profile_mA(t_span[0])), 0.0)
        v_act0 = float(activation_overpotential(i0_mA, c_o2, params))
        c_h0 = float(proton_concentration_steady(i0_mA, params))
        x0 = (v_act0, c_h0)

    t_eval = np.linspace(t_span[0], t_span[1], n_points)

    sol = solve_ivp(
        fun=state_derivatives,
        t_span=t_span,
        y0=list(x0),
        t_eval=t_eval,
        args=(current_profile_mA, c_o2, params),
        method="BDF",   # sistema potencialmente rígido (tau_dl << tau_H);
                        # escolha de engenharia numérica, não do artigo
        rtol=1e-6,
        atol=1e-9,
    )

    t = sol.t
    v_act = sol.y[0]
    c_h = sol.y[1]

    i_mA = np.array([max(float(current_profile_mA(ti)), 0.0) for ti in t])

    sigma = membrane_conductivity(c_h, params, const)
    r_mem = membrane_resistance_kOhm_cm2(sigma, params)
    v_ohm = ohmic_overpotential(i_mA, r_mem)
    v_conc = concentration_overpotential(i_mA, params)

    v_cell = e_nernst - v_act - v_ohm - v_conc
    v_stack = v_cell * params.N_cells
    current_A = i_mA / 1000.0 * params.A_active
    p_stack = v_stack * current_A

    return {
        "t": t,
        "i_mA": i_mA,
        "I_A": current_A,
        "V_act": v_act,
        "C_H": c_h,
        "sigma": sigma,
        "R_mem_kOhm_cm2": r_mem,
        "V_ohm": v_ohm,
        "V_conc": v_conc,
        "E_nernst": np.full_like(t, e_nernst),
        "V_cell": v_cell,
        "V_stack": v_stack,
        "P_stack": p_stack,
        "success": sol.success,
        "message": sol.message,
    }


# ----------------------------------------------------------------------
# Perfis de corrente predefinidos (helpers de UI, i em mA/cm^2)
# ----------------------------------------------------------------------
def step_profile(i_low: float, i_high: float, t_step: float) -> Callable[[float], float]:
    return lambda t: i_low if t < t_step else i_high


def ramp_profile(i_low: float, i_high: float, t_start: float, t_end: float):
    def profile(t: float) -> float:
        if t <= t_start:
            return i_low
        if t >= t_end:
            return i_high
        return i_low + (i_high - i_low) * (t - t_start) / (t_end - t_start)

    return profile
