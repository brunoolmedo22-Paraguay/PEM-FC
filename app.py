from __future__ import annotations

import io
import pandas as pd
import streamlit as st

from models.pemfc_model import PEMFCModel
from pemfc_config.parameters import DEFAULT_PARAMS, PARAMETER_METADATA
from simulation.solver import build_figure3_dataset, sensitivity_pressure, sensitivity_temperature
from visualization.plots import figure3_matplotlib_bytes, figure3_plotly

st.set_page_config(page_title="Modelo PEMFC - OTEKON 2024", layout="wide")


def _init_state() -> None:
    defaults = DEFAULT_PARAMS.to_dict()
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _reset() -> None:
    for key, value in DEFAULT_PARAMS.to_dict().items():
        st.session_state[key] = value


def _params_from_state():
    allowed = DEFAULT_PARAMS.to_dict().keys()
    values = {key: st.session_state[key] for key in allowed}
    values["N_cells"] = int(values["N_cells"])
    return DEFAULT_PARAMS.copy_with(**values)


def _combined_csv(data: dict[str, pd.DataFrame]) -> bytes:
    frames = []
    for case, df in data.items():
        out = df.copy()
        out.insert(0, "case", case)
        frames.append(out)
    return pd.concat(frames, ignore_index=True).to_csv(index=False).encode("utf-8")


_init_state()

st.title("Modelo eletroquímico PEMFC - OTEKON 2024")
st.caption("Uma única implementação em Python, com parâmetros ausentes reconstruídos por engenharia reversa da Figura 3.")

tab_config, tab_results, tab_sensitivity, tab_docs = st.tabs([
    "Configuração", "Resultados", "Análise de sensibilidade", "Documentação do modelo"
])

with tab_config:
    st.subheader("Parâmetros do caso publicado")
    st.button("Restaurar parâmetros do artigo", on_click=_reset)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("Número de células - INFERIDO", min_value=1, max_value=500, step=1, key="N_cells")
        st.number_input("Área ativa (cm²) - INFERIDO", min_value=1.0, max_value=2000.0, step=1.0, key="A_active_cm2")
        st.number_input("p_H2 (atm) - INFERIDO", min_value=0.05, max_value=20.0, step=0.05, key="p_h2")
        st.number_input("p_H2O (atm) - HIPÓTESE", min_value=0.01, max_value=10.0, step=0.01, key="p_h2o")
    with c2:
        st.number_input("ξ1 efetivo - INFERIDO", format="%.9f", key="xi1")
        st.number_input("ξ2 efetivo - INFERIDO", format="%.10f", key="xi2")
        st.number_input("ξ3 efetivo - INFERIDO", format="%.10f", key="xi3")
        st.number_input("ξ4 - ARTIGO", format="%.10f", key="xi4")
    with c3:
        st.number_input("R_mem,ref (Ω.cm²) - INFERIDO", min_value=0.001, max_value=2.0, format="%.8f", key="R_mem_ref_ohm_cm2")
        st.number_input("Expoente térmico R_mem - INFERIDO", min_value=-5.0, max_value=5.0, format="%.8f", key="R_mem_temperature_exponent")
        st.number_input("a_ref concentração (V) - INFERIDO", min_value=0.0, max_value=0.1, format="%.9f", key="concentration_a_ref_V")
        st.number_input("b concentração (cm²/A) - INFERIDO", min_value=0.0, max_value=20.0, format="%.8f", key="concentration_b_cm2_A")
    st.info("Os valores iniciais geram diretamente os quatro resultados reconstruídos do artigo. Não existe seletor de modelo nem cálculo especial para os gráficos.")

params = _params_from_state()
model = PEMFCModel(params)
data = build_figure3_dataset(model)

with tab_results:
    m1, m2, m3, m4 = st.columns(4)
    v298_1 = float(model.cell_voltage([1.0], 298.15, 5.0)[0])
    v373_1 = float(model.cell_voltage([1.0], 373.15, 5.0)[0])
    p298_1 = float(model.stack_power([1.0], 298.15, 5.0)[0])
    p373_1 = float(model.stack_power([1.0], 373.15, 5.0)[0])
    m1.metric("V_cell @ 1 A/cm², 298 K", f"{v298_1:.3f} V")
    m2.metric("V_cell @ 1 A/cm², 373 K", f"{v373_1:.3f} V")
    m3.metric("P_stack @ 1 A/cm², 298 K", f"{p298_1/1000:.2f} kW")
    m4.metric("P_stack @ 1 A/cm², 373 K", f"{p373_1/1000:.2f} kW")

    st.plotly_chart(figure3_plotly(data), width="stretch")
    png = figure3_matplotlib_bytes(data, "png")
    svg = figure3_matplotlib_bytes(data, "svg")
    csv = _combined_csv(data)
    d1, d2, d3 = st.columns(3)
    d1.download_button("Baixar gráficos em PNG", png, "figura3_modelo.png", "image/png")
    d2.download_button("Baixar gráficos em SVG", svg, "figura3_modelo.svg", "image/svg+xml")
    d3.download_button("Baixar curvas em CSV", csv, "curvas_otekon_modelo.csv", "text/csv")

with tab_sensitivity:
    st.subheader("Sensibilidade calculada pelo mesmo PEMFCModel")
    j_sens = st.slider("Densidade de corrente (A/cm²)", 0.05, 1.0, 0.70, 0.01)
    temp_df = sensitivity_temperature(model, j_sens, range(298, 374, 5))
    press_df = sensitivity_pressure(model, j_sens, [1, 2, 3, 4, 5])
    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(temp_df.set_index("temperature_K")[["V_cell_V", "efficiency_percent"]])
    with c2:
        st.line_chart(press_df.set_index("air_pressure_atm")[["V_cell_V"]])

with tab_docs:
    st.subheader("Equações implementadas")
    st.latex(r"V_{cell}=E-V_{act}-V_{ohm}-V_{conc}")
    st.latex(r"E=E_0-0.85\times10^{-3}(T-298.15)+\frac{RT}{2F}\ln\left(\frac{p_{H_2}p_{O_2}^{1/2}}{p_{H_2O}P^{1/2}}\right)")
    st.latex(r"V_{act}=-\left(\xi_1+\xi_2T+\xi_3T\ln I+\xi_4T\ln C_{O_2}\right)")
    st.latex(r"\sigma=\frac{F^2}{RT}D_{H^+}C_{H^+},\quad R_{mem}=\frac{t_m}{\sigma},\quad V_{ohm}=jR_{mem}")
    st.latex(r"V_{conc}=a(T)\exp(bj)")
    st.latex(r"P_{stack}=N\,V_{cell}\,jA,\quad \eta=100\,U_f\frac{V_{cell}}{E_0}")

    rows = []
    values = params.to_dict()
    for name, meta in PARAMETER_METADATA.items():
        rows.append({"Parâmetro": name, "Símbolo": meta["symbol"], "Valor": values[name], "Unidade": meta["unit"], "Origem": meta["origin"], "Justificativa": meta["justification"]})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.warning("A reprodução é computacional, não uma validação experimental. Os coeficientes identificados representam a interpretação mais provável compatível com os resultados publicados.")
