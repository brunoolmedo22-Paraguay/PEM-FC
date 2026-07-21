from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from models.pemfc_model import PEMFCModel
from pemfc_config import DEFAULT_PARAMS, PARAMETER_METADATA
from simulation.solver import build_figure3_dataset, sensitivity_pressure, sensitivity_temperature
from visualization.plots import figure3_matplotlib_bytes, figure3_plotly
from visualization.optimization import (
    optimization_flowchart_article_bytes,
    optimization_flowchart_bytes,
    optimization_flowchart_plotly,
)
from calibration.identify_parameters import (
    RANDOM_SEED,
    SIGMA_DIGITIZATION_V,
    parameter_specification_table,
)

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
        out.insert(1, "source", "modelo")
        frames.append(out)
    return pd.concat(frames, ignore_index=True).to_csv(index=False).encode("utf-8")


@st.cache_data(show_spinner=False)
def _load_otekon_reference_curves() -> dict[str, dict[str, pd.DataFrame]]:
    """Carrega os pontos digitalizados da Figura 3 apenas para comparação."""
    root = Path(__file__).resolve().parent / "data" / "otekon_figure3"
    mapping = {
        "voltage": {
            "T_298": "voltage_298K.csv",
            "T_373": "voltage_373K.csv",
        },
        "power": {
            "T_298": "power_298K.csv",
            "T_373": "power_373K.csv",
        },
        "efficiency": {
            "T_298": "efficiency_298K.csv",
            "T_373": "efficiency_373K.csv",
        },
        "pressure": {
            "P_1": "pressure_1atm.csv",
            "P_5": "pressure_5atm.csv",
        },
    }
    return {
        quantity: {case: pd.read_csv(root / filename) for case, filename in cases.items()}
        for quantity, cases in mapping.items()
    }


def _comparison_csv(
    model_data: dict[str, pd.DataFrame],
    reference_data: dict[str, dict[str, pd.DataFrame]],
) -> bytes:
    """Exporta modelo e artigo em formato longo para rastreabilidade."""
    frames = []
    model_columns = {
        "voltage": "V_cell_V",
        "power": "P_stack_W",
        "efficiency": "efficiency_percent",
    }
    for quantity, column in model_columns.items():
        for case in ("T_298", "T_373"):
            frame = model_data[case][["current_density_A_cm2", column]].rename(columns={column: "value"})
            frame.insert(0, "quantity", quantity)
            frame.insert(1, "case", case)
            frame.insert(2, "source", "modelo")
            frames.append(frame)
    for case in ("P_1", "P_5"):
        frame = model_data[case][["current_density_A_cm2", "V_cell_V"]].rename(columns={"V_cell_V": "value"})
        frame.insert(0, "quantity", "pressure")
        frame.insert(1, "case", case)
        frame.insert(2, "source", "modelo")
        frames.append(frame)

    for quantity, cases in reference_data.items():
        for case, df in cases.items():
            frame = df[["current_density_A_cm2", "value"]].copy()
            frame.insert(0, "quantity", quantity)
            frame.insert(1, "case", case)
            frame.insert(2, "source", "artigo")
            frames.append(frame)

    return pd.concat(frames, ignore_index=True).to_csv(index=False).encode("utf-8")


_init_state()

st.title("Modelo eletroquímico PEMFC - OTEKON 2024")
st.caption("Uma única implementação em Python, com parâmetros ausentes reconstruídos por engenharia reversa da Figura 3.")

tab_config, tab_results, tab_sensitivity, tab_identification, tab_docs = st.tabs([
    "Configuração",
    "Resultados",
    "Análise de sensibilidade",
    "Identificação paramétrica",
    "Documentação do modelo",
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
        st.number_input("ξ4 efetivo - INFERIDO", format="%.10f", key="xi4")
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

    overlay_article = st.toggle(
        "Sobrepor curvas digitalizadas do artigo",
        value=False,
        help=(
            "Ativa a sobreposição dos pontos digitalizados da Figura 3 do OTEKON. "
            "As linhas contínuas permanecem sendo o resultado do PEMFCModel; "
            "as linhas tracejadas com marcadores representam o artigo."
        ),
    )
    reference_data = _load_otekon_reference_curves() if overlay_article else None

    if overlay_article:
        st.caption(
            "Linhas contínuas azul/vermelha: modelo. "
            "Linhas tracejadas laranja/ciano: curvas digitalizadas do artigo."
        )

    st.plotly_chart(figure3_plotly(data, reference_data=reference_data), width="stretch")
    png = figure3_matplotlib_bytes(data, "png", reference_data=reference_data)
    svg = figure3_matplotlib_bytes(data, "svg", reference_data=reference_data)
    csv = (
        _comparison_csv(data, reference_data)
        if reference_data is not None
        else _combined_csv(data)
    )
    suffix = "comparacao_otekon" if overlay_article else "modelo"
    d1, d2, d3 = st.columns(3)
    d1.download_button(
        "Baixar gráficos em PNG",
        png,
        f"figura3_{suffix}.png",
        "image/png",
    )
    d2.download_button(
        "Baixar gráficos em SVG",
        svg,
        f"figura3_{suffix}.svg",
        "image/svg+xml",
    )
    d3.download_button(
        "Baixar curvas em CSV",
        csv,
        f"curvas_{suffix}.csv",
        "text/csv",
    )

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


with tab_identification:
    st.subheader("Como os parâmetros foram identificados")
    st.markdown(
        """
A otimização não foi utilizada para desenhar artificialmente as curvas. Ela foi
aplicada porque o artigo fornece a estrutura do modelo, mas deixa parâmetros e
convenções insuficientes ou incompatíveis com os próprios resultados publicados.
O procedimento abaixo transforma essa lacuna em uma etapa rastreável e reprodutível
de engenharia reversa.
"""
    )

    st.plotly_chart(optimization_flowchart_plotly(), width="stretch")

    st.markdown("### 1. Dados utilizados")
    st.markdown(
        """
O ajuste eletroquímico primário utiliza **somente quatro curvas de tensão**:
298,15 K, 373,15 K, 1 atm e 5 atm. As curvas de potência e eficiência não entram
na função objetivo principal, porque são derivadas da tensão e causariam dupla
contagem da mesma informação. Elas são usadas depois para inferir, respectivamente,
a escala do stack e o fator de utilização.
"""
    )
    st.dataframe(
        pd.DataFrame(
            [
                {"Curva": "Temperatura", "Condição": "298,15 K e 5 atm", "Uso": "Ajuste primário"},
                {"Curva": "Temperatura", "Condição": "373,15 K e 5 atm", "Uso": "Ajuste primário"},
                {"Curva": "Pressão", "Condição": "373,15 K e 1 atm", "Uso": "Ajuste primário"},
                {"Curva": "Pressão", "Condição": "373,15 K e 5 atm", "Uso": "Ajuste primário"},
                {"Curva": "Potência", "Condição": "298,15 K e 373,15 K", "Uso": "Inferência de N×A e verificação"},
                {"Curva": "Eficiência", "Condição": "298,15 K e 373,15 K", "Uso": "Inferência escalar de U_f"},
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.markdown("### 2. Função objetivo")
    st.latex(
        r"J(\boldsymbol{\theta})="
        r"\frac{1}{N}\sum_{c=1}^{4}\sum_{k=1}^{n_c}"
        r"\left[\frac{V_{model}(j_k,T_c,P_c;\boldsymbol{\theta})-V_{fig,c}(j_k)}{\sigma_V}\right]^2"
    )
    st.markdown(
        rf"Foi adotada uma incerteza de digitalização de $\sigma_V={SIGMA_DIGITIZATION_V:.3f}$ V. "
        r"O vetor $\boldsymbol{\theta}$ contém os coeficientes efetivos de ativação, "
        "resistência da membrana e perda de concentração."
    )

    st.markdown("### 3. Estratégia numérica")
    st.markdown(
        f"""
O vetor inicial combina os coeficientes impressos no artigo com estimativas obtidas
pela leitura das regiões de ativação, ôhmica e de transporte de massa. Em seguida,
é aplicado **mínimos quadrados não lineares com limites físicos**, método Trust
Region Reflective, a partir de múltiplos inícios determinísticos. A semente fixada é
`{RANDOM_SEED}`, o que permite repetir exatamente o processo. O conjunto escolhido
é aquele que apresenta o menor RMSE conjunto das quatro curvas de tensão.
"""
    )
    st.dataframe(parameter_specification_table(), hide_index=True, width="stretch")

    st.markdown("### 4. Inferências posteriores")
    st.latex(r"P_{stack}=N\,A\,j\,V_{cell}")
    st.latex(r"\eta=100\,U_f\frac{V_{cell}}{E_0}")
    st.markdown(
        """
Após fechar as curvas de tensão, o produto contínuo $N\\times A$ é estimado pelas
curvas de potência. A área de 232 cm² é mantida pela interpretação da capacitância
da Tabela 1, e aplica-se a restrição física de número inteiro de células, resultando
em **N = 41 — INFERIDO**. O fator $U_f$ é obtido por mínimos quadrados escalares
a partir das curvas de eficiência.
"""
    )

    root = Path(__file__).resolve().parent
    summary_path = root / "outputs" / "optimization_summary.json"
    params_path = root / "outputs" / "identified_parameters.csv"
    runs_path = root / "outputs" / "optimization_runs.csv"
    corr_path = root / "outputs" / "parameter_correlation.csv"
    report_path = root / "outputs" / "optimization_report.md"

    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        st.markdown("### 5. Resultado da identificação")
        a, b, c, d = st.columns(4)
        a.metric("RMSE das curvas de tensão", f"{1000*summary['voltage_rmse_V']:.3f} mV")
        b.metric("Inícios da otimização", str(summary["number_of_starts"]))
        c.metric("N contínuo equivalente", f"{summary['effective_number_of_cells']:.2f}")
        d.metric("N inteiro adotado", str(int(summary["adopted_integer_cells"])))
        st.caption(
            f"Número de condição do Jacobiano escalado: "
            f"{summary['jacobian_condition_number_scaled']:.1f}. "
            "Esse diagnóstico registra correlações entre parâmetros e evita apresentar "
            "a solução como fisicamente única."
        )

    if params_path.exists():
        identified = pd.read_csv(params_path)
        st.dataframe(identified, hide_index=True, width="stretch")

    if runs_path.exists():
        runs = pd.read_csv(runs_path).sort_values("rmse_voltage_V")
        st.markdown("#### Robustez em relação ao valor inicial")
        st.dataframe(runs.head(8), hide_index=True, width="stretch")

    if corr_path.exists():
        corr = pd.read_csv(corr_path, index_col=0)
        pairs = []
        for i, name_i in enumerate(corr.index):
            for j, name_j in enumerate(corr.columns):
                if j <= i:
                    continue
                value = float(corr.iloc[i, j])
                if abs(value) >= 0.90:
                    pairs.append({"Parâmetro 1": name_i, "Parâmetro 2": name_j, "Correlação": value})
        if pairs:
            st.markdown("#### Correlações paramétricas relevantes")
            st.dataframe(
                pd.DataFrame(pairs).sort_values("Correlação", key=lambda col: col.abs(), ascending=False),
                hide_index=True,
                width="stretch",
            )
            st.info(
                "Correlação elevada não invalida a reprodução das curvas, mas indica "
                "que alguns coeficientes efetivos não podem ser interpretados como "
                "propriedades físicas independentes sem dados experimentais adicionais."
            )

    st.markdown("### 6. Reprodutibilidade")
    st.code("python calibration/identify_parameters.py --starts 16", language="bash")
    st.markdown(
        "O comando recria os parâmetros identificados, os resíduos, o histórico dos "
        "inícios, a matriz de correlação e o relatório da otimização. A interface não "
        "executa a calibração em tempo real; ela apenas registra o procedimento e usa "
        "os parâmetros finais no mesmo `PEMFCModel` das demais páginas."
    )

    flow_png = optimization_flowchart_bytes("png")
    flow_svg = optimization_flowchart_bytes("svg")
    article_svg = optimization_flowchart_article_bytes("svg")
    dl1, dl2, dl3, dl4 = st.columns(4)
    dl1.download_button("Fluxograma PNG", flow_png, "fluxograma_identificacao.png", "image/png")
    dl2.download_button("Fluxograma SVG", flow_svg, "fluxograma_identificacao.svg", "image/svg+xml")
    dl3.download_button("Versão compacta para artigo", article_svg, "fluxograma_identificacao_artigo.svg", "image/svg+xml")
    if report_path.exists():
        dl4.download_button(
            "Relatório da otimização",
            report_path.read_bytes(),
            "relatorio_identificacao.md",
            "text/markdown",
        )

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
