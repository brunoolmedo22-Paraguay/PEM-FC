"""Elementos visuais da metodologia de identificação paramétrica."""
from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import plotly.graph_objects as go


FLOW_STEPS = (
    ("1", "Artigo e Figura 3", "Equações, parâmetros publicados e quatro painéis"),
    ("2", "Digitalização auditada", "Conversão pixel→dados e verificação dos eixos"),
    ("3", "Engenharia reversa", "A=232 cm², escala N×A, temperatura e unidades"),
    ("4", "Vetor inicial e limites", "Coeficientes publicados + estimativas físicas"),
    ("5", "Otimização primária", "4 curvas de tensão; multistart + mínimos quadrados"),
    ("6", "Diagnóstico", "Resíduos, robustez, Jacobiano e correlações"),
    ("7", "Inferências escalares", "N inteiro pela potência e U_f pela eficiência"),
    ("8", "PEMFCModel único", "Parâmetros finais em todas as páginas e gráficos"),
)


def optimization_flowchart_plotly() -> go.Figure:
    y_values = list(range(len(FLOW_STEPS), 0, -1))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0.5] * len(FLOW_STEPS),
            y=y_values,
            mode="markers+text",
            marker=dict(size=48, color="#1f4e79", line=dict(width=2, color="white")),
            text=[step[0] for step in FLOW_STEPS],
            textfont=dict(color="white", size=16),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    for y, (_, title, description) in zip(y_values, FLOW_STEPS):
        fig.add_annotation(
            x=0.57,
            y=y,
            text=f"<b>{title}</b><br><span style='font-size:12px'>{description}</span>",
            showarrow=False,
            xanchor="left",
            align="left",
            font=dict(size=14, color="#17202a"),
        )
    for y0, y1 in zip(y_values[:-1], y_values[1:]):
        fig.add_annotation(
            x=0.5,
            y=y1 + 0.25,
            ax=0.5,
            ay=y0 - 0.25,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=2,
            arrowcolor="#5d6d7e",
        )
    fig.update_xaxes(range=[0.43, 1.35], visible=False)
    fig.update_yaxes(range=[0.45, len(FLOW_STEPS) + 0.55], visible=False)
    fig.update_layout(
        height=720,
        margin=dict(l=0, r=20, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def optimization_flowchart_bytes(fmt: str = "png") -> bytes:
    fig, ax = plt.subplots(figsize=(9, 11))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(FLOW_STEPS) + 0.7)
    ax.axis("off")

    for index, (number, title, description) in enumerate(FLOW_STEPS):
        y = len(FLOW_STEPS) - index - 0.15
        box = FancyBboxPatch(
            (0.10, y - 0.36),
            0.80,
            0.68,
            boxstyle="round,pad=0.025,rounding_size=0.035",
            linewidth=1.4,
            edgecolor="black",
            facecolor="white",
        )
        ax.add_patch(box)
        ax.text(0.15, y, number, ha="center", va="center", fontsize=14, weight="bold")
        ax.text(0.22, y + 0.10, title, ha="left", va="center", fontsize=12, weight="bold")
        ax.text(0.22, y - 0.12, description, ha="left", va="center", fontsize=10)
        if index < len(FLOW_STEPS) - 1:
            ax.annotate(
                "",
                xy=(0.50, y - 0.50),
                xytext=(0.50, y - 0.35),
                arrowprops=dict(arrowstyle="-|>", linewidth=1.5),
            )

    buffer = BytesIO()
    fig.savefig(buffer, format=fmt, dpi=220 if fmt == "png" else None, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def optimization_flowchart_article_bytes(fmt: str = "png") -> bytes:
    """Versão compacta em duas linhas, adequada para inclusão no artigo."""
    compact_steps = (
        ("1", "Artigo e Fig. 3", "Equações e dados"),
        ("2", "Digitalização", "Pixel → grandeza"),
        ("3", "Engenharia reversa", "Unidades e escala"),
        ("4", "Limites e início", "Valores publicados"),
        ("5", "Ajuste multistart", "4 curvas de tensão"),
        ("6", "Diagnóstico", "Resíduos e Jacobiano"),
        ("7", "Inferências escalares", "N e U_f"),
        ("8", "PEMFCModel único", "Gráficos finais"),
    )
    fig, ax = plt.subplots(figsize=(13.5, 5.8))
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 2)
    ax.axis("off")

    positions = [
        (0.05, 1.10), (1.05, 1.10), (2.05, 1.10), (3.05, 1.10),
        (3.05, 0.15), (2.05, 0.15), (1.05, 0.15), (0.05, 0.15),
    ]
    width, height = 0.90, 0.68
    centers = []
    for (x, y), (number, title, description) in zip(positions, compact_steps):
        box = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.03",
            linewidth=1.25,
            edgecolor="black",
            facecolor="white",
        )
        ax.add_patch(box)
        ax.text(x + 0.10, y + 0.47, number, ha="center", va="center", fontsize=11, weight="bold")
        ax.text(x + 0.20, y + 0.47, title, ha="left", va="center", fontsize=9.8, weight="bold")
        ax.text(x + 0.10, y + 0.19, description, ha="left", va="center", fontsize=8.1)
        centers.append((x + width / 2, y + height / 2))

    for index in range(3):
        ax.annotate("", xy=(positions[index + 1][0] - 0.02, centers[index + 1][1]),
                    xytext=(positions[index][0] + width + 0.02, centers[index][1]),
                    arrowprops=dict(arrowstyle="-|>", linewidth=1.3))
    ax.annotate("", xy=(centers[4][0], positions[4][1] + height + 0.02),
                xytext=(centers[3][0], positions[3][1] - 0.02),
                arrowprops=dict(arrowstyle="-|>", linewidth=1.3))
    for index in range(4, 7):
        ax.annotate("", xy=(positions[index + 1][0] + width + 0.02, centers[index + 1][1]),
                    xytext=(positions[index][0] - 0.02, centers[index][1]),
                    arrowprops=dict(arrowstyle="-|>", linewidth=1.3))

    buffer = BytesIO()
    fig.savefig(buffer, format=fmt, dpi=220 if fmt == "png" else None, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()
