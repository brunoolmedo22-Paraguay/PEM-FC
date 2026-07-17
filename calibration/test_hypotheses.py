"""
calibration/test_hypotheses.py
================================
Etapa 3 (teste sistematico de convencoes) + Etapa 4 (ajuste hierarquico)
do plano de engenharia reversa da Figura 3, OTEKON 2024.

Executar:
    cd PEMFC_Simulator
    python calibration/test_hypotheses.py
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from scipy.optimize import minimize, least_squares

from calibration.flexible_model import Conventions, cell_voltage, power_stack, efficiency
from calibration.load_digitized import load_all

DATA = load_all()


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def mae(a, b):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))


def max_err(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def r2(a, b):
    a, b = np.asarray(a), np.asarray(b)
    ss_res = np.sum((a - b) ** 2)
    ss_tot = np.sum((a - a.mean()) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


# ======================================================================
# ETAPA 3.1 -- Convencao de corrente na ativacao (A/cm2 vs mA/cm2)
#              testada contra os paineis "voltage-like" (panel1/panel4)
# ======================================================================
def test_activation_current_unit():
    """
    Testa mA/cm2 vs A/cm2 na Eq. 4, com os demais blocos em sua forma
    "melhor palpite" (ohmica desprezivel, concentracao no regime nao
    problematico), calibrando apenas xi1 (deslocamento vertical) para
    isolar o efeito da unidade na FORMA da curva (inclinacao),
    nao no nivel absoluto.
    """
    rows = []
    x298, y298 = DATA[("panel4", 298.15)]
    for unit in ["mA/cm2", "A/cm2"]:
        conv = Conventions(activation_current_unit=unit, alpha_H=0.0,
                            pressure_source="figure")

        def resid(params):
            xi1 = params[0]
            conv.xi1 = xi1
            out = cell_voltage(x298, 298.15, conv)
            return out["Vcell"] - y298

        res = least_squares(resid, x0=[-0.95])
        conv.xi1 = res.x[0]
        out = cell_voltage(x298, 298.15, conv)
        rows.append({
            "hipotese": f"I em {unit} na Eq.4",
            "xi1_ajustado": round(res.x[0], 5),
            "RMSE_V": round(rmse(out["Vcell"], y298), 5),
            "MAE_V": round(mae(out["Vcell"], y298), 5),
            "R2": round(r2(y298, out["Vcell"]), 4),
        })
    return pd.DataFrame(rows)


# ======================================================================
# ETAPA 3.2 -- log natural vs log10
# ======================================================================
def test_log_base():
    rows = []
    x298, y298 = DATA[("panel4", 298.15)]
    for base in ["ln", "log10"]:
        conv = Conventions(activation_log_base=base, alpha_H=0.0, pressure_source="figure")

        def resid(params):
            conv.xi1 = params[0]
            out = cell_voltage(x298, 298.15, conv)
            return out["Vcell"] - y298

        res = least_squares(resid, x0=[-0.95])
        conv.xi1 = res.x[0]
        out = cell_voltage(x298, 298.15, conv)
        rows.append({
            "hipotese": f"log base = {base}",
            "xi1_ajustado": round(res.x[0], 5),
            "RMSE_V": round(rmse(out["Vcell"], y298), 5),
            "R2": round(r2(y298, out["Vcell"]), 4),
        })
    return pd.DataFrame(rows)


# ======================================================================
# ETAPA 3.3 -- fonte de pressao (figura vs Tabela 1) contra panel4 (que
#              tem a legenda de pressao) e panel1 (que nao tem)
# ======================================================================
def test_pressure_source():
    rows = []
    for panel_key, label in [(("panel4", 298.15), "panel4 (com legenda P)"),
                              (("panel1", 298.15), "panel1 (sem legenda P)")]:
        x, y = DATA[panel_key]
        for src in ["figure", "table1"]:
            conv = Conventions(pressure_source=src, alpha_H=0.0)

            def resid(params):
                conv.xi1 = params[0]
                out = cell_voltage(x, 298.15, conv)
                return out["Vcell"] - y

            res = least_squares(resid, x0=[-0.95])
            conv.xi1 = res.x[0]
            out = cell_voltage(x, 298.15, conv)
            rows.append({
                "painel": label,
                "fonte_pressao": src,
                "E_Nernst": round(nernst_E_helper(conv), 4),
                "xi1_ajustado": round(res.x[0], 5),
                "RMSE_V": round(rmse(out["Vcell"], y), 5),
                "R2": round(r2(y, out["Vcell"]), 4),
            })
    return pd.DataFrame(rows)


def nernst_E_helper(conv):
    from calibration.flexible_model import nernst_E
    E, _ = nernst_E(298.15, conv)
    return E


# ======================================================================
# ETAPA 4 -- Ajuste hierarquico completo por temperatura, painel4
#            (pressao conhecida da legenda), variando xi1..xi4, alpha_H,
#            p_H2O (unico GAP remanescente do bloco de Nernst)
# ======================================================================
def hierarchical_fit():
    results = {}
    for T in [298.15, 373.15]:
        x, y = DATA[("panel4", T)]
        conv = Conventions(pressure_source="figure")

        def resid(params):
            xi1, xi3, p_h2o = params
            conv.xi1 = xi1
            conv.xi3 = xi3
            conv.p_h2o = p_h2o
            out = cell_voltage(x, T, conv)
            return out["Vcell"] - y

        res = least_squares(resid, x0=[-0.95, -0.000187, 0.5],
                             bounds=([-2.0, -0.01, 0.05], [0.0, -1e-6, 3.0]))
        xi1, xi3, p_h2o = res.x
        conv.xi1, conv.xi3, conv.p_h2o = xi1, xi3, p_h2o
        out = cell_voltage(x, T, conv)
        results[T] = dict(xi1=xi1, xi3=xi3, p_h2o=p_h2o,
                           RMSE=rmse(out["Vcell"], y), MAE=mae(out["Vcell"], y),
                           MaxErr=max_err(out["Vcell"], y), R2=r2(y, out["Vcell"]),
                           E=nernst_E_helper(conv), conv=conv)
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("ETAPA 3.1 -- Unidade de corrente na ativacao (Eq.4)")
    print("=" * 70)
    print(test_activation_current_unit().to_string(index=False))

    print("\n" + "=" * 70)
    print("ETAPA 3.2 -- Base do logaritmo (Eq.4)")
    print("=" * 70)
    print(test_log_base().to_string(index=False))

    print("\n" + "=" * 70)
    print("ETAPA 3.3 -- Fonte das pressoes parciais (Eq.3)")
    print("=" * 70)
    print(test_pressure_source().to_string(index=False))

    print("\n" + "=" * 70)
    print("ETAPA 4 -- Ajuste hierarquico completo (painel4, por temperatura)")
    print("=" * 70)
    res = hierarchical_fit()
    for T, r in res.items():
        print(f"\nT={T} K:")
        for k, v in r.items():
            if k != "conv":
                print(f"  {k:10s} = {v}")
