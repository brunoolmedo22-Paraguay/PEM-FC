"""
app.py
======
PEMFC Simulator -- interface Streamlit.

Modelo: "Modeling of a PEM Fuel Cell System in MATLAB", OTEKON 2024
(Altintas & Ertan, Bursa Uludag University).

Esta camada SO cuida da interface: recolhe parametros, chama
simulation/ e desenha com visualization/. Nenhuma equacao vive aqui.

Ponto central desta versao: TODO parametro exibido na aba Parameters
traz um selo de origem -- "ARTIGO" (valor citado explicitamente no
texto ou na Tabela 1) ou "GAP" (o artigo nao fornece o valor; e um
placeholder editavel). Isso evita apresentar como "do OTEKON" algo que
nao esta la.

Executar:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que a raiz do repositorio esteja em sys.path, independente do
# diretorio de trabalho que o ambiente de deploy (ex. Streamlit
# Community Cloud) usar para invocar este script. Sem isso, os pacotes
# locais (pemfc_config, models, simulation, visualization) podem falhar
# ao ser importados em certos ambientes de deploy.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import streamlit as st

from pemfc_config.parameters import CONSTANTS, DEFAULT_PARAMS, GAP_FIELDS, PEMFCParameters
from models.pemfc_model import PEMFCModel
from simulation import calculations as calc
from simulation.solver import run_polarization, run_transient
from visualization import plots

# ======================================================================
# Configuracao de pagina
# ======================================================================
st.set_page_config(
    page_title="PEMFC Simulator -- OTEKON 2024",
    page_icon=":zap:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; max-width: 1400px;}
      h1, h2, h3 {letter-spacing: -0.01em;}
      div[data-testid="stMetricValue"] {font-size: 1.30rem;}
      .stTabs [data-baseweb="tab"] {font-weight: 600;}
      .gap-badge {
        display:inline-block; background:#fdecea; color:#a13a2f;
        border:1px solid #f3c6bd; border-radius:4px; font-size:0.72rem;
        padding:1px 6px; margin-left:6px; font-weight:600;
      }
      .art-badge {
        display:inline-block; background:#eaf5ea; color:#2f6b2f;
        border:1px solid #c8e2c8; border-radius:4px; font-size:0.72rem;
        padding:1px 6px; margin-left:6px; font-weight:600;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def badge(field_name: str) -> str:
    """Selo ARTIGO / GAP renderizado ao lado do rotulo de cada campo."""
    if field_name in GAP_FIELDS:
        return '<span class="gap-badge">GAP</span>'
    return '<span class="art-badge">ARTIGO</span>'


def field_label(text: str, field_name: str) -> str:
    st.markdown(f"{text} {badge(field_name)}", unsafe_allow_html=True)


# ======================================================================
# Estado da sessao
# ======================================================================
def init_state() -> None:
    if "params" not in st.session_state:
        st.session_state.params = DEFAULT_PARAMS.copy_with()
    if "results" not in st.session_state:
        st.session_state.results = None
    if "transient" not in st.session_state:
        st.session_state.transient = None


init_state()
params: PEMFCParameters = st.session_state.params


# ======================================================================
# Barra lateral
# ======================================================================
with st.sidebar:
    st.title(":zap: PEMFC Simulator")
    st.caption("OTEKON 2024 -- Altintas & Ertan")

    if st.button("Restaurar valores do artigo", use_container_width=True):
        st.session_state.params = DEFAULT_PARAMS.copy_with()
        st.session_state.results = None
        st.rerun()

    st.divider()
    model = PEMFCModel(st.session_state.params)
    diag = model.diagnostics()
    st.markdown("**Diagnostico rapido**")
    st.metric("E (Nernst, Eq. 3)", f"{diag['E_nernst [V]']:.4f} V")
    st.metric("C_O2 (Eq. 5)", f"{diag['C_O2 [mol/cm3]']:.3e} mol/cm3")
    st.metric("R_mem @ I=0 (Eq. 10)", f"{diag['R_mem @ I=0 [kOhm.cm2]']:.3e} kOhm.cm2")

    if not diag["conc_model_valid"]:
        st.warning(
            "O coeficiente 'a' da Eq. 13 e <= 0 nesta temperatura "
            "(a = a1 - a2(T-273) se anula em T ~= 364.7 K). A formula, "
            "reproduzida literalmente, deixa de fazer sentido fisico "
            "acima disso."
        )
    if diag["sigma_fora_da_faixa_tipica"]:
        st.info(
            "sigma (Eq. 12), calculada com os numeros literais do "
            "artigo (D_H+ da Tabela 1, CH+ base = 1), sai fora da faixa "
            "tipica de literatura geral para Nafion hidratado "
            "(0.02-0.20 S/cm). Isto e reportado como consequencia direta "
            "dos valores do artigo, nao corrigido automaticamente."
        )

    st.divider()
    st.caption(
        "Fonte: Altintas, N.; Ertan, R. 'Modeling of a PEM Fuel Cell "
        "System in MATLAB', OTEKON 2024."
    )


st.title("Simulador PEMFC -- OTEKON 2024")
st.caption(
    "Reproducao do modelo de *Modeling of a PEM Fuel Cell System in "
    "MATLAB* (OTEKON 2024): Nernst (Eq. 3) + Henry (Eq. 5) + ativacao "
    "tipo Tafel (Eq. 4, 6, 8) + dupla camada (Eq. 7) + hidratacao e "
    "condutividade (Eq. 11, 12) + ohmica (Eq. 9, 10) + concentracao "
    "(Eq. 13) + stack (Eq. 14)."
)

tab_params, tab_sim, tab_results, tab_info, tab_audit = st.tabs(
    ["Parameters", "Simulation", "Results", "Model Information", "Fidelidade & Gaps"]
)


# ======================================================================
# TAB 1 -- PARAMETERS
# ======================================================================
with tab_params:
    st.subheader("Parametros do modelo")
    st.markdown(
        '<span class="art-badge">ARTIGO</span> = valor citado literalmente no '
        'texto ou na Tabela 1 do OTEKON 2024. '
        '<span class="gap-badge">GAP</span> = o artigo nao fornece este valor; '
        "e um placeholder editavel, necessario para a simulacao rodar, "
        "mas NAO e um dado do artigo. Veja a aba **Fidelidade & Gaps** "
        "para a justificativa de cada selo.",
        unsafe_allow_html=True,
    )

    p = st.session_state.params
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("##### Operacao -- Eq. 3 (Nernst)")
        T = st.number_input("Temperatura T [K]  (Tabela 1)", 293.0, 373.0, float(p.T), 1.0)
        P = st.number_input("Pressao da celula P [atm]  (Tabela 1)", 0.5, 6.0, float(p.P), 0.1)
        field_label("Pressao parcial p_H2 [atm]", "p_h2")
        p_h2 = st.number_input("p_H2", 0.01, 6.0, float(p.p_h2), 0.05, label_visibility="collapsed")
        field_label("Pressao parcial p_O2 [atm]", "p_o2")
        p_o2 = st.number_input("p_O2", 0.01, 6.0, float(p.p_o2), 0.01, label_visibility="collapsed")
        field_label("Pressao de vapor p_H2O [atm]", "p_h2o")
        p_h2o = st.number_input("p_H2O", 0.01, 6.0, float(p.p_h2o), 0.05, label_visibility="collapsed")

        st.markdown("##### Geometria -- Eq. 14 e Tabela 1")
        field_label("Area ativa A [cm2] (inferida do produto Cdl=0.035x232 da Tabela 1)", "A_active")
        A_active = st.number_input("A_active", 1.0, 2000.0, float(p.A_active), 1.0, label_visibility="collapsed")
        field_label("Numero de celulas N [-] (Eq. 14 e generica, N nao e dado)", "N_cells")
        N_cells = st.number_input("N_cells", 1, 500, int(p.N_cells), 1, label_visibility="collapsed")

    with c2:
        st.markdown("##### Nernst / Henry -- Eq. 3, 5 (Tabela 1)")
        E0 = st.number_input("E0 [V]  (Tabela 1)", 0.5, 1.5, float(p.E0), 0.001, format="%.3f")
        k_henry = st.number_input("k_Henry [atm.cm3/mol]  (Eq. 5)", 1e5, 1e8, float(p.k_henry), 1e5, format="%.3e")
        e_henry = st.number_input("E_Henry [K]  (Eq. 5)", 100.0, 1500.0, float(p.e_henry), 1.0)

        st.markdown("##### Ativacao (xi) -- Eq. 4 (citados no texto)")
        xi1 = st.number_input("xi1 [V]", -2.0, 0.0, float(p.xi1), 0.0001, format="%.4f")
        xi2 = st.number_input("xi2 [V/K]", 0.0, 0.01, float(p.xi2), 1e-5, format="%.5f")
        xi3 = st.number_input("xi3 . T.ln(I) [V/K]", -1e-3, 0.0, float(p.xi3), 1e-6, format="%.6f")
        xi4 = st.number_input("xi4 . T.ln(CO2) [V/K]", 0.0, 1e-3, float(p.xi4), 1e-6, format="%.6f")

    with c3:
        st.markdown("##### Membrana -- Eq. 10, 11, 12 (Tabela 1)")
        t_m = st.number_input("Espessura t_m [cm]  (Tabela 1)", 1e-4, 0.05, float(p.t_m), 1e-4, format="%.4f")
        D_H = st.number_input("D_H+ [cm2/s]  (Tabela 1)", 1e-8, 1e-4, float(p.D_H), 1e-8, format="%.3e")
        tau_H = st.number_input("tau_H+ [s]  (Tabela 1)", 0.1, 100.0, float(p.tau_H), 0.1)
        field_label("alpha_H+ [(cm2/mA)^3] -- NAO aparece no artigo", "alpha_H")
        alpha_H = st.number_input("alpha_H", 0.0, 1.0, float(p.alpha_H), format="%.3e", label_visibility="collapsed")
        st.caption("CH_BASE = 1.0 (literal da Eq. 11, fixo, nao editavel)")

        st.markdown("##### Concentracao / dupla camada -- Eq. 13, 7")
        a_1 = st.number_input("a1 [V]  (citado no texto)", 0.0, 1e-2, float(p.a_1), 1e-5, format="%.5e")
        a_2 = st.number_input("a2 [V/K]  (citado no texto)", 0.0, 1e-4, float(p.a_2), 1e-7, format="%.3e")
        b_conc = st.number_input("b [cm2/mA]  (citado no texto)", 0.0, 0.1, float(p.b_conc), 1e-4, format="%.4f")
        C_dl_specific = st.number_input(
            "C_dl especifica [F/cm2]  (Tabela 1: 0.035x232)",
            1e-4, 1.0, float(p.C_dl_specific), 0.001, format="%.3f",
        )

    st.session_state.params = p.copy_with(
        T=T, P=P, p_h2=p_h2, p_o2=p_o2, p_h2o=p_h2o,
        A_active=A_active, N_cells=int(N_cells),
        E0=E0, k_henry=k_henry, e_henry=e_henry,
        xi1=xi1, xi2=xi2, xi3=xi3, xi4=xi4,
        t_m=t_m, D_H=D_H, tau_H=tau_H, alpha_H=alpha_H,
        a_1=a_1, a_2=a_2, b_conc=b_conc, C_dl_specific=C_dl_specific,
    )

    st.divider()
    d1, d2, d3 = st.columns(3)
    dg = PEMFCModel(st.session_state.params).diagnostics()
    d1.metric("C_dl total (Tabela 1)", f"{dg['C_dl_total [F]']:.2f} F")
    d2.metric("R_mem @ I=0 (Eq. 10)", f"{dg['R_mem @ I=0 [kOhm.cm2]']:.3e} kOhm.cm2")
    d3.metric("a(T) da Eq. 13", f"{dg['a_conc(T) [V]']:.3e} V")

    with st.expander("Ver todos os parametros ativos (JSON)"):
        st.json(st.session_state.params.to_dict())


# ======================================================================
# TAB 2 -- SIMULATION
# ======================================================================
with tab_sim:
    p = st.session_state.params

    st.subheader("Sequencia de calculo -- exatamente como no artigo")
    st.latex(r"V_{cell} = E - V_{act} - V_{ohm} - V_{conc} \qquad \text{(Eq. 2)}")

    st.info(
        "**Convencao de unidade confirmada no texto do artigo:** a "
        "densidade de corrente I esta em **mA/cm2** em TODAS as equacoes "
        "abaixo -- nao em A/cm2. Evidencias diretas do texto: (1) 'I is "
        "the current density'; (2) R_act (Eq. 8) e R_mem (Eq. 10) sao "
        "rotuladas em **kOhm.cm2**, o que so surge de V/(mA/cm2); "
        "(3) o coeficiente b da Eq. 13 e rotulado em **cm2.mA-1**."
    )

    with st.expander("Sequencia completa (Eq. 3 a 14)", expanded=True):
        st.markdown("**Eq. 3 -- Potencial reversivel (Nernst)**")
        st.latex(
            r"E = E_0 - 0.85\times10^{-3}(T - 298.15) + \frac{RT}{2F}"
            r"\ln\!\left(\frac{p_{H_2}\,p_{O_2}^{0.5}}{p_{H_2O}\,P^{0.5}}\right)"
        )

        st.markdown("**Eq. 5 -- Concentracao de oxigenio (Henry)**")
        st.latex(r"C_{O_2} = \frac{p_{O_2}}{5.08\times10^{6}\exp(-498/T)} \quad [\mathrm{mol\,cm^{-3}}]")

        st.markdown("**Eq. 4 e 6 -- Ativacao (Tafel semi-empirico)**")
        st.latex(
            r"E_{act} = -0.9514 + 0.00312\,T - 1.87\times10^{-4}\,T\ln(I)"
            r" + 7.4\times10^{-5}\,T\ln(C_{O_2}) \qquad [I]=\mathrm{mA/cm^2}"
        )
        st.latex(r"V_{act} = -E_{act}")

        st.markdown("**Eq. 7 e 8 -- Dupla camada e resistencia de ativacao**")
        st.latex(r"\frac{dV_{act}}{dt} = \frac{I}{C_{dl}} - \frac{V_{act}}{R_{act}\,C_{dl}}")
        st.latex(r"R_{act} = \frac{V_{act}}{I} \quad [\mathrm{k\Omega\,cm^2}]")
        st.warning(
            "**Ponte de unidades necessaria na Eq. 7** (nao explicitada no "
            "artigo): a Tabela 1 da Cdl = 0.035x232 = 8.12 F como um valor "
            "TOTAL da celula especifica do artigo, mas o texto diz que I e "
            "densidade de corrente. dV/dt = I/Cdl so fecha em V/s se I e "
            "Cdl estiverem na MESMA base (total ou especifica). Convertemos "
            "I para corrente total [A] (via area ativa) e R_act de "
            "kOhm.cm2 especifico para Ohm total, documentado em "
            "models/dynamics.py. E uma interpretacao, nao um dado do artigo."
        )

        st.markdown("**Eq. 11 e 12 -- Hidratacao e condutividade**")
        st.latex(r"\frac{dC_{H^+}}{dt} + \frac{C_{H^+}}{\tau_{H^+}} = \frac{1 + \alpha_{H^+}\,I^{3}}{\tau_{H^+}}")
        st.latex(r"\sigma = \frac{F^{2}}{RT}\,D_{H^+}\,C_{H^+}")
        st.warning(
            "O **'1'** na Eq. 11 e literal no artigo -- nao ha um "
            "'C_H_ref' nomeado no texto. So faz sentido fisico como "
            "'1 mol/cm3' porque a Eq. 12 (Nernst-Einstein) exige que "
            "C_H+ seja uma concentracao molar para sigma sair em S/cm. "
            "Implementado como constante fixa CH_BASE=1.0, nao um knob "
            "de calibracao livre."
        )

        st.markdown("**Eq. 9 e 10 -- Perda ohmica**")
        st.latex(r"R_{mem} = \frac{t_m}{\sigma} \quad [\mathrm{k\Omega\,cm^2}] \qquad V_{ohm} = I\,R_{mem}")

        st.markdown("**Eq. 13 -- Concentracao**")
        st.latex(r"V_{conc} = a\,e^{\,b\,I}, \quad a = 1.1\times10^{-4} - 1.2\times10^{-6}(T-273), \quad b = 8\times10^{-3}\;[\mathrm{cm^2/mA}]")

        st.markdown("**Eq. 14 -- Stack**")
        st.latex(r"V_{stack} = N\,V_{cell}")

    st.divider()
    st.subheader("Configuracao da varredura estacionaria")

    c1, c2, c3, c4 = st.columns(4)
    i_max_default = float(np.round(1.0 * p.A_active, 0))
    with c1:
        i_min_A = st.number_input("Corrente minima [A]", 0.001, 1000.0, 0.1, 0.1)
    with c2:
        i_max_A = st.number_input("Corrente maxima [A]", 0.5, 5000.0, i_max_default, 1.0)
    with c3:
        n_points = st.number_input("N. de pontos", 20, 2000, 300, 10)
    with c4:
        log_spacing = st.checkbox("Espacamento log", value=False)

    st.caption(
        f"Faixa em densidade de corrente: "
        f"{p.current_to_density_mA(i_min_A):.2f} -> "
        f"{p.current_to_density_mA(i_max_A):.0f} mA/cm2 (A = {p.A_active:.0f} cm2)"
    )

    if st.button("Executar simulacao estacionaria", type="primary", use_container_width=True):
        df = run_polarization(p, i_min_A, i_max_A, int(n_points), log_spacing)
        df = calc.enrich(df, p)
        st.session_state.results = df
        st.success("Simulacao concluida. Resultados na aba **Results**.")

    st.divider()
    with st.expander("Simulacao temporal -- Eq. 7 + Eq. 11 (dupla camada + hidratacao)"):
        t1, t2, t3 = st.columns(3)
        with t1:
            profile_type = st.selectbox("Perfil de corrente", ["step", "ramp"])
            i_low_A = st.number_input("Corrente inicial [A]", 0.0, 5000.0, 20.0, 1.0)
        with t2:
            i_high_A = st.number_input("Corrente final [A]", 0.0, 5000.0, 150.0, 1.0)
            t_final = st.number_input("Tempo total [s]", 1.0, 600.0, 60.0, 1.0)
        with t3:
            t_event = st.number_input("Instante do evento [s]", 0.0, 600.0, 5.0, 1.0)
            t_event_end = st.number_input("Fim da rampa [s]", 0.0, 600.0, 25.0, 1.0)

        if st.button("Executar simulacao temporal", use_container_width=True):
            res = run_transient(
                params=p, profile_type=profile_type,
                i_low_A=i_low_A, i_high_A=i_high_A,
                t_final=t_final, t_event=t_event, t_event_end=t_event_end,
            )
            st.session_state.transient = res
            if res["success"]:
                st.success("Transitorio resolvido.")
            else:
                st.error(f"O integrador falhou: {res['message']}")

        if st.session_state.transient is not None:
            st.plotly_chart(plots.transient_plot(st.session_state.transient), use_container_width=True)


# ======================================================================
# TAB 3 -- RESULTS
# ======================================================================
with tab_results:
    df = st.session_state.results

    if df is None:
        st.info("Execute primeiro uma simulacao na aba **Simulation**.")
    else:
        p = st.session_state.params
        mpp = calc.maximum_power_point(df)

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("OCV do stack", f"{df['V_stack [V]'].iloc[0]:.2f} V")
        k2.metric("Potencia maxima", f"{mpp['P_stack [W]']:.1f} W")
        k3.metric("I no MPP", f"{mpp['I [A]']:.1f} A")
        k4.metric("V_cell no MPP", f"{mpp['V_cell [V]']:.3f} V")
        k5.metric("Densidade de potencia max.", f"{mpp['P_density [W/cm2]']:.3f} W/cm2")

        opt1, opt2 = st.columns([1, 1])
        x_col = opt1.radio("Eixo X", ["I [A]", "i [mA/cm2]"], horizontal=True)
        stack_view = opt2.radio("Tensao mostrada", ["Stack", "Celula"], horizontal=True) == "Stack"

        st.markdown("### Grafico 1 -- Curva de polarizacao (V vs I)")
        st.plotly_chart(plots.polarization_plot(df, x_col=x_col, stack=stack_view), use_container_width=True)

        st.markdown("### Grafico 2 -- Curva de potencia (P vs I)")
        st.plotly_chart(plots.power_plot(df, x_col=x_col, mpp=mpp), use_container_width=True)

        st.markdown("### Grafico 3 -- Separacao de perdas")
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(plots.losses_plot(df, x_col=x_col), use_container_width=True)
        with g2:
            st.plotly_chart(plots.losses_stacked_area(df, x_col=x_col), use_container_width=True)

        st.markdown("### Reparto de perdas em um ponto de operacao")
        i_query = st.slider(
            "Corrente de consulta [A]",
            float(df["I [A]"].min()), float(df["I [A]"].max()), float(mpp["I [A]"]),
        )
        bd = calc.loss_breakdown_at(df, i_query)
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("V_act", f"{bd['V_act [V]']*1000:.1f} mV", f"{bd['share_act [%]']:.1f} %")
        b2.metric("V_ohm", f"{bd['V_ohm [V]']*1000:.3f} mV", f"{bd['share_ohm [%]']:.2f} %")
        b3.metric("V_conc", f"{bd['V_conc [V]']*1000:.1f} mV", f"{bd['share_conc [%]']:.1f} %")
        b4.metric("V_cell resultante", f"{bd['V_cell [V]']:.3f} V")

        st.markdown("### Tabela de resultados")
        st.dataframe(df, use_container_width=True, height=320)
        st.download_button(
            "Baixar resultados (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="pemfc_polarization.csv",
            mime="text/csv",
        )


# ======================================================================
# TAB 4 -- MODEL INFORMATION
# ======================================================================
with tab_info:
    st.subheader("Referencia")
    st.markdown(
        "**Altintas, N.; Ertan, R.** *Modeling of a PEM Fuel Cell System "
        "in MATLAB*. OTEKON 2024. Bursa Uludag University, Department of "
        "Polymer Materials / Automotive Engineering."
    )
    st.markdown(
        "Modelo semi-empirico de celula: potencial reversivel "
        "termodinamico (Eq. 3) menos tres irreversibilidades -- ativacao "
        "(Eq. 4, 6, 8), ohmica (Eq. 9, 10) e concentracao (Eq. 13) -- com "
        "dois estados dinamicos: dupla camada (Eq. 7) e hidratacao da "
        "membrana (Eq. 11, 12). Formulacao citada pelo artigo como "
        "baseada em Spiegel (2008) e Barbir (2005)."
    )

    st.markdown("---")
    st.markdown("#### Tabela 1 do artigo (parametros base)")
    st.table(
        pd.DataFrame({
            "Parametro": ["E0", "R", "F", "T", "P", "t_m", "C_dl", "tau_H+", "D_H+"],
            "Valor": ["1.229 V", "8.314 J/mol.K", "96485 C/mol", "353 K", "1.2 atm",
                      "0.005 cm", "0.035 x 232 F", "12.78 s", "0.85e-6 cm2/s"],
        })
    )

    st.markdown("#### Coeficientes citados no texto (fora da Tabela 1)")
    st.table(
        pd.DataFrame({
            "Equacao": ["Eq. 4 (ativacao)"]*4 + ["Eq. 13 (concentracao)"]*2,
            "Coeficiente": ["xi1", "xi2", "xi3", "xi4", "a1, a2", "b"],
            "Valor": ["-0.9514", "0.00312", "-0.000187", "7.4e-5",
                      "1.1e-4 ; 1.2e-6", "8e-3"],
        })
    )

    st.markdown("---")
    st.markdown("#### O que este simulador NAO afirma vir do artigo")
    st.markdown(
        "Consulte a aba **Fidelidade & Gaps** para a lista completa, "
        "equacao por equacao e parametro por parametro, do que e "
        "reproducao literal, do que e inferencia razoavel e do que e "
        "placeholder por falta de informacao no artigo."
    )


# ======================================================================
# TAB 5 -- FIDELIDADE & GAPS (auditoria embutida)
# ======================================================================
with tab_audit:
    st.subheader("Rastreabilidade -- o que vem do artigo e o que nao vem")
    st.caption(
        "Esta aba existe para que nenhum numero deste simulador seja "
        "confundido com um dado do OTEKON 2024 sem que isso fique "
        "explicito."
    )

    st.markdown("#### Equacoes -- reproducao literal")
    st.table(pd.DataFrame({
        "Eq.": ["2", "3", "4/6", "5", "7", "8", "9", "10", "11", "12", "13", "14"],
        "Descricao": [
            "Vcell = E - Vact - Vohm - Vconc",
            "Nernst com correcao termica",
            "Ativacao tipo Tafel / Vact=-Eact",
            "Concentracao de O2 (Henry)",
            "Dinamica da dupla camada",
            "Ract = Vact/I",
            "Vohm = I.Rmem",
            "Rmem = tm/sigma",
            "Dinamica de hidratacao protonica",
            "sigma = F^2.D.C/(RT)",
            "Vconc = a.exp(b.I)",
            "Vstack = N.Vcell",
        ],
        "Status": [
            "Literal", "Literal", "Literal", "Literal",
            "Literal + ponte de unidades (ver aviso na aba Simulation)",
            "Literal", "Literal", "Literal",
            "Literal (constante '1' interpretada como 1 mol/cm3, ver Simulation)",
            "Literal", "Literal", "Literal",
        ],
    }))

    st.markdown("#### Parametros -- origem")
    gap_rows = []
    for f, just in GAP_FIELDS.items():
        gap_rows.append({"Campo": f, "Status": "GAP (nao esta no artigo)", "Justificativa": just})
    st.markdown("**GAP -- nao especificados pelo artigo:**")
    st.table(pd.DataFrame(gap_rows))

    st.markdown("**ARTIGO -- citados literalmente (Tabela 1 ou texto):**")
    st.table(pd.DataFrame({
        "Campo": ["E0", "T", "P", "k_henry, e_henry", "xi1..xi4",
                  "t_m, D_H, tau_H", "CH_BASE (o '1' da Eq.11)",
                  "a_1, a_2, b_conc", "C_dl_specific"],
        "Fonte": ["Tabela 1", "Tabela 1", "Tabela 1", "Eq. 5 (texto)",
                  "Eq. 4 (texto)", "Tabela 1",
                  "Eq. 11 (texto, literal '1')",
                  "Texto apos Eq. 13", "Tabela 1 (0.035x232)"],
    }))

    st.markdown("---")
    st.markdown("#### Extensoes desta implementacao (nao sao equacoes do artigo)")
    st.markdown(
        "- **Eficiencia** (eta_HHV, eta_LHV): relacao termodinamica "
        "padrao de literatura geral de celulas a combustivel.\n"
        "- **Consumo de H2**: lei de Faraday padrao, consumo "
        "estequiometrico ideal (sem excesso nem purga).\n"
        "- **Regularizacoes numericas**: piso de corrente para evitar "
        "ln(0); saturacao de V_act >= 0 (a Eq. 4 extrapolada para I muito "
        "baixo pode dar V_act negativo, o que violaria a Eq. 2)."
    )

    st.markdown("#### Lacunas conhecidas do proprio artigo")
    st.markdown(
        "- O texto diz 'Related parameters [p_H2, p_O2, p_H2O] are given "
        "in Table 1', mas a Tabela 1 **nao lista** essas tres pressoes "
        "parciais -- apenas a pressao total P=1.2 atm.\n"
        "- alpha_H+ (Eq. 11) nao aparece em nenhum lugar do artigo.\n"
        "- N (numero de celulas, Eq. 14) nao e especificado para o caso "
        "estudado.\n"
        "- A area ativa (232 cm2) so aparece embutida no produto "
        "'0.035x232' da Tabela 1 -- nunca rotulada explicitamente como "
        "'area ativa'."
    )
