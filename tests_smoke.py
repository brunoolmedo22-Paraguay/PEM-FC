"""
tests_smoke.py
==============
Validacao numerica do modelo (sem depender do Streamlit).

    python tests_smoke.py
"""

import numpy as np

from pemfc_config.parameters import DEFAULT_PARAMS
from models.dynamics import step_profile
from models.pemfc_model import PEMFCModel
from simulation import calculations as calc
from simulation.solver import run_polarization


def main() -> None:
    p = DEFAULT_PARAMS
    model = PEMFCModel(p)

    print("=" * 66)
    print("DIAGNOSTICO DO MODELO (parametros do artigo OTEKON 2024)")
    print("=" * 66)
    for k, v in model.diagnostics().items():
        print(f"  {k:<32} : {v}")

    print("\n" + "=" * 66)
    print("PONTOS DE OPERACAO ESTACIONARIOS  (I em mA/cm2, unidade nativa)")
    print("=" * 66)
    print(f"{'i [mA/cm2]':>11} {'I [A]':>8} {'V_act':>8} {'V_ohm':>10} "
          f"{'V_conc':>9} {'V_cell':>8} {'P [W]':>9}")
    for i_mA in [1, 10, 50, 100, 200, 400, 600, 800, 1000]:
        I = i_mA / 1000.0 * p.A_active
        s = model.steady_state(I)
        print(f"{i_mA:>11} {I:>8.1f} {s['V_act']:>8.4f} {s['V_ohm']:>10.6f} "
              f"{s['V_conc']:>9.5f} {s['V_cell']:>8.4f} {s['P_stack']:>9.2f}")

    df = run_polarization(p, 0.1, 1.0 * p.A_active, 300)
    df = calc.enrich(df, p)
    mpp = calc.maximum_power_point(df)

    print("\n" + "=" * 66)
    print("CURVA DE POLARIZACAO")
    print("=" * 66)
    print(f"  OCV (i->0)            : {df['V_cell [V]'].iloc[0]:.4f} V")
    print(f"  Monotonia decrescente : {bool(np.all(np.diff(df['V_cell [V]']) < 0))}")
    print(f"  MPP                   : {mpp['P_stack [W]']:.1f} W @ "
          f"{mpp['I [A]']:.1f} A ({mpp['i [mA/cm2]']:.0f} mA/cm2)")
    print(f"  Densidade de potencia : {mpp['P_density [W/cm2]']:.4f} W/cm2")

    bd = calc.loss_breakdown_at(df, mpp["I [A]"])
    print(f"  Reparto no MPP        : act {bd['share_act [%]']:.1f} % | "
          f"ohm {bd['share_ohm [%]']:.2f} % | conc {bd['share_conc [%]']:.1f} %")

    i_low_mA, i_high_mA = 20.0, 500.0
    res = model.transient(step_profile(i_low_mA, i_high_mA, 5.0), t_span=(0, 60), n_points=1200)

    v_ss_final = model.steady_state(i_high_mA / 1000.0 * p.A_active)["V_cell"]
    print("\n" + "=" * 66)
    print(f"TRANSITORIO -- degrau {i_low_mA:.0f} -> {i_high_mA:.0f} mA/cm2 em t=5s")
    print("=" * 66)
    print(f"  Integracao              : {res['success']} ({res['message']})")
    print(f"  V_cell antes (t=4.9s)   : {np.interp(4.9, res['t'], res['V_cell']):.4f} V")
    print(f"  V_cell em t=5.1 s       : {np.interp(5.1, res['t'], res['V_cell']):.4f} V")
    print(f"  V_cell em t=60 s        : {res['V_cell'][-1]:.4f} V")
    print(f"  V_cell estacionario     : {v_ss_final:.4f} V")
    err = abs(res["V_cell"][-1] - v_ss_final)
    print(f"  Erro vs estacionario    : {err:.2e} V  -> {'OK' if err < 5e-3 else 'REVISAR'}")


if __name__ == "__main__":
    main()
