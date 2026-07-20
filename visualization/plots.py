from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots


BLUE = "#006BBD"
RED = "#FF0000"


def figure3_plotly(data: dict):
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Efeito da temperatura sobre a tensão",
            "Potência do stack",
            "Eficiência elétrica",
            "Efeito da pressão do ar",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.16,
    )

    for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
        df = data[key]
        fig.add_trace(go.Scatter(x=df.current_density_A_cm2, y=df.V_cell_V, name=label, line=dict(color=color, width=2.5), legendgroup=key), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.current_density_A_cm2, y=df.P_stack_W, name=label, line=dict(color=color, width=2.5), legendgroup=key, showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=df.current_density_A_cm2, y=df.efficiency_percent, name=label, line=dict(color=color, width=2.5), legendgroup=key, showlegend=False), row=2, col=1)

    for key, color, label in [("P_1", BLUE, "P_ar = 1 atm"), ("P_5", RED, "P_ar = 5 atm")]:
        df = data[key]
        fig.add_trace(go.Scatter(x=df.current_density_A_cm2, y=df.V_cell_V, name=label, line=dict(color=color, width=2.5), legendgroup=key), row=2, col=2)

    for row, col in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        fig.update_xaxes(title_text="Densidade de corrente (A/cm²)", range=[0, 1.2], dtick=0.2, showgrid=True, gridcolor="rgba(100,100,100,0.35)", row=row, col=col)

    fig.update_yaxes(title_text="Tensão da célula (V)", range=[0.5, 1.1], dtick=0.2, row=1, col=1)
    fig.update_yaxes(title_text="Potência (W)", range=[0, 6000], dtick=1000, row=1, col=2)
    fig.update_yaxes(title_text="Eficiência (%)", range=[25, 60], dtick=5, row=2, col=1)
    fig.update_yaxes(title_text="Tensão da célula (V)", range=[0.5, 1.1], dtick=0.1, row=2, col=2)
    fig.update_layout(height=760, margin=dict(l=40, r=30, t=80, b=40), legend=dict(orientation="h", y=1.08, x=0), hovermode="x unified")
    return fig


def _matplotlib_figure(data: dict):
    fig, axes = plt.subplots(2, 2, figsize=(13.34, 8.0), constrained_layout=True)
    ax1, ax2, ax3, ax4 = axes.flat
    for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
        df = data[key]
        ax1.plot(df.current_density_A_cm2, df.V_cell_V, color=color, linewidth=2, label=label)
        ax2.plot(df.current_density_A_cm2, df.P_stack_W, color=color, linewidth=2, label=label)
        ax3.plot(df.current_density_A_cm2, df.efficiency_percent, color=color, linewidth=2, label=label)
    for key, color, label in [("P_1", BLUE, "P_ar = 1 atm"), ("P_5", RED, "P_ar = 5 atm")]:
        df = data[key]
        ax4.plot(df.current_density_A_cm2, df.V_cell_V, color=color, linewidth=2, label=label)

    settings = [
        (ax1, "Tensão da célula (V)", (0.5, 1.1), 0.2),
        (ax2, "Potência (W)", (0, 6000), 1000),
        (ax3, "Eficiência (%)", (25, 60), 5),
        (ax4, "Tensão da célula (V)", (0.5, 1.1), 0.1),
    ]
    for ax, ylabel, ylim, _ in settings:
        ax.set_xlim(0, 1.2)
        ax.set_ylim(*ylim)
        ax.set_xlabel("Densidade de corrente (A/cm²)")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.55)
        ax.legend(loc="best")
    ax1.set_title("Efeito da temperatura sobre a tensão")
    ax2.set_title("Potência do stack")
    ax3.set_title("Eficiência elétrica")
    ax4.set_title("Efeito da pressão do ar")
    return fig


def figure3_matplotlib_bytes(data: dict, fmt: str = "png") -> bytes:
    fig = _matplotlib_figure(data)
    buffer = BytesIO()
    fig.savefig(buffer, format=fmt, dpi=180 if fmt == "png" else None, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()
