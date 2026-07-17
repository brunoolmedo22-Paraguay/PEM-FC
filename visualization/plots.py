"""
visualization/plots.py
======================
Todas las figuras del simulador (Plotly). Estética limpia, tema claro,
paleta contenida. Ninguna función de aquí calcula física: sólo dibuja.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Paleta contenida -------------------------------------------------
PALETTE = {
    "voltage": "#1f5f8b",      # azul profundo
    "power": "#d97b29",        # ámbar
    "nernst": "#2f2f2f",       # grafito
    "act": "#c0392b",          # rojo
    "ohm": "#2e8b57",          # verde
    "conc": "#8e44ad",         # violeta
    "grid": "#e6e9ec",
    "mpp": "#111111",
}

LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13, color="#2f2f2f"),
    margin=dict(l=60, r=30, t=60, b=55),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)


def _axes(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(showgrid=True, gridcolor=PALETTE["grid"], zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=PALETTE["grid"], zeroline=False)
    return fig


# ======================================================================
# 1. Curva de polarización (V-I) con potencia en eje secundario
# ======================================================================
def polarization_plot(
    df: pd.DataFrame,
    x_col: str = "I [A]",
    stack: bool = True,
    show_power: bool = True,
) -> go.Figure:
    """Gráfico 1: Voltaje vs Corriente (+ potencia opcional)."""
    v_col = "V_stack [V]" if stack else "V_cell [V]"

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[v_col],
            name=v_col,
            mode="lines",
            line=dict(color=PALETTE["voltage"], width=3),
        ),
        secondary_y=False,
    )

    if show_power:
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df["P_stack [W]"],
                name="P_stack [W]",
                mode="lines",
                line=dict(color=PALETTE["power"], width=2.5, dash="dot"),
            ),
            secondary_y=True,
        )

    fig.update_layout(title="Curva de polarización", **LAYOUT)
    fig.update_xaxes(title_text=x_col)
    fig.update_yaxes(title_text="Voltaje [V]", secondary_y=False)
    fig.update_yaxes(title_text="Potencia [W]", secondary_y=True, showgrid=False)
    return _axes(fig)


# ======================================================================
# 2. Curva de potencia
# ======================================================================
def power_plot(df: pd.DataFrame, x_col: str = "I [A]", mpp: dict | None = None) -> go.Figure:
    """Gráfico 2: Potencia vs Corriente, con marca del punto de máxima potencia."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df["P_stack [W]"],
            name="P_stack [W]",
            mode="lines",
            line=dict(color=PALETTE["power"], width=3),
            fill="tozeroy",
            fillcolor="rgba(217,123,41,0.10)",
        )
    )

    if mpp is not None:
        fig.add_trace(
            go.Scatter(
                x=[mpp["I [A]"]],
                y=[mpp["P_stack [W]"]],
                name="MPP",
                mode="markers+text",
                marker=dict(color=PALETTE["mpp"], size=10, symbol="circle"),
                text=[f"  {mpp['P_stack [W]']:.1f} W @ {mpp['I [A]']:.1f} A"],
                textposition="top center",
            )
        )

    fig.update_layout(title="Curva de potencia", **LAYOUT)
    fig.update_xaxes(title_text=x_col)
    fig.update_yaxes(title_text="Potencia del stack [W]")
    return _axes(fig)


# ======================================================================
# 3. Separación de pérdidas
# ======================================================================
def losses_plot(df: pd.DataFrame, x_col: str = "I [A]") -> go.Figure:
    """Gráfico 3: E, V_act, V_ohm, V_conc y V_cell resultante (por celda)."""
    fig = go.Figure()

    series = [
        ("E [V]", PALETTE["nernst"], "dash", "E (Nernst)"),
        ("V_act [V]", PALETTE["act"], "solid", "V_act (activación)"),
        ("V_ohm [V]", PALETTE["ohm"], "solid", "V_ohm (óhmica)"),
        ("V_conc [V]", PALETTE["conc"], "solid", "V_conc (concentración)"),
        ("V_cell [V]", PALETTE["voltage"], "solid", "V_cell (resultante)"),
    ]

    for col, color, dash, label in series:
        width = 3 if col in ("V_cell [V]", "E [V]") else 2
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[col],
                name=label,
                mode="lines",
                line=dict(color=color, width=width, dash=dash),
            )
        )

    fig.update_layout(title="Separación de pérdidas (por celda)", **LAYOUT)
    fig.update_xaxes(title_text=x_col)
    fig.update_yaxes(title_text="Voltaje [V]")
    return _axes(fig)


def losses_stacked_area(df: pd.DataFrame, x_col: str = "I [A]") -> go.Figure:
    """Variante: cascada acumulada desde E hasta V_cell."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df[x_col], y=df["V_cell [V]"], name="V_cell",
            mode="lines", line=dict(color=PALETTE["voltage"], width=2),
            stackgroup="one", fillcolor="rgba(31,95,139,0.18)",
        )
    )
    for col, color, label in [
        ("V_conc [V]", "rgba(142,68,173,0.35)", "V_conc"),
        ("V_ohm [V]", "rgba(46,139,87,0.35)", "V_ohm"),
        ("V_act [V]", "rgba(192,57,43,0.35)", "V_act"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=df[x_col], y=df[col], name=label, mode="lines",
                line=dict(width=0), stackgroup="one", fillcolor=color,
            )
        )

    fig.update_layout(title="Cascada de tensión: E = V_cell + pérdidas", **LAYOUT)
    fig.update_xaxes(title_text=x_col)
    fig.update_yaxes(title_text="Voltaje [V]")
    return _axes(fig)


# ======================================================================
# 4. Respuesta dinámica
# ======================================================================
def transient_plot(result: dict) -> go.Figure:
    """Respuesta temporal: corriente, V_act, C_H y V_cell."""
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.07,
        subplot_titles=(
            "Corriente aplicada",
            "Sobrepotencial de activación (doble capa)",
            "Tensión de celda e hidratación de membrana",
        ),
    )

    fig.add_trace(
        go.Scatter(x=result["t"], y=result["I_A"], name="I [A]",
                   line=dict(color=PALETTE["power"], width=2)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=result["t"], y=result["V_act"], name="V_act [V]",
                   line=dict(color=PALETTE["act"], width=2)),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(x=result["t"], y=result["V_cell"], name="V_cell [V]",
                   line=dict(color=PALETTE["voltage"], width=2)),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(x=result["t"], y=result["C_H"], name="C_H+ [mol/cm3]",
                   line=dict(color=PALETTE["ohm"], width=2, dash="dot"),
                   yaxis="y4"),
        row=3, col=1,
    )

    fig.update_layout(
        height=720,
        title="Respuesta dinámica del modelo",
        **{k: v for k, v in LAYOUT.items() if k != "hovermode"},
        hovermode="x unified",
    )
    fig.update_xaxes(title_text="Tiempo [s]", row=3, col=1)
    fig.update_yaxes(title_text="I [A]", row=1, col=1)
    fig.update_yaxes(title_text="V_act [V]", row=2, col=1)
    fig.update_yaxes(title_text="V [V] / C_H+", row=3, col=1)
    return _axes(fig)
