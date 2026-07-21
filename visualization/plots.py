from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Cores do modelo.
BLUE = "#006BBD"
RED = "#FF0000"

# Cores complementares utilizadas exclusivamente para as curvas digitalizadas
# do artigo. Azul -> laranja; vermelho -> ciano.
ARTICLE_BLUE_COMPLEMENT = "#FF8A00"
ARTICLE_RED_COMPLEMENT = "#00A6D6"


def _add_article_trace_plotly(
    fig,
    df,
    *,
    row: int,
    col: int,
    name: str,
    color: str,
    legendgroup: str,
    showlegend: bool,
):
    """Adiciona uma curva digitalizada do artigo ao gráfico Plotly."""
    fig.add_trace(
        go.Scatter(
            x=df.current_density_A_cm2,
            y=df.value,
            name=name,
            mode="lines+markers",
            line=dict(color=color, width=2.0, dash="dash"),
            marker=dict(color=color, size=4, symbol="circle-open"),
            legendgroup=legendgroup,
            showlegend=showlegend,
            hovertemplate=(
                "Densidade de corrente: %{x:.4f} A/cm²"
                "<br>Valor digitalizado: %{y:.4f}<extra></extra>"
            ),
        ),
        row=row,
        col=col,
    )


def figure3_plotly(data: dict, reference_data: dict | None = None):
    """Gera os quatro painéis do modelo, opcionalmente sobrepondo o artigo.

    ``reference_data`` deve possuir a estrutura::

        {
            "voltage": {"T_298": df, "T_373": df},
            "power": {"T_298": df, "T_373": df},
            "efficiency": {"T_298": df, "T_373": df},
            "pressure": {"P_1": df, "P_5": df},
        }

    Cada DataFrame de referência contém as colunas
    ``current_density_A_cm2`` e ``value``.
    """
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

    temperature_cases = [
        ("T_298", BLUE, "T = 298,15 K"),
        ("T_373", RED, "T = 373,15 K"),
    ]
    for key, color, label in temperature_cases:
        df = data[key]
        fig.add_trace(
            go.Scatter(
                x=df.current_density_A_cm2,
                y=df.V_cell_V,
                name=f"Modelo — {label}",
                line=dict(color=color, width=2.7),
                legendgroup=f"model_{key}",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.current_density_A_cm2,
                y=df.P_stack_W,
                name=f"Modelo — {label}",
                line=dict(color=color, width=2.7),
                legendgroup=f"model_{key}",
                showlegend=False,
            ),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Scatter(
                x=df.current_density_A_cm2,
                y=df.efficiency_percent,
                name=f"Modelo — {label}",
                line=dict(color=color, width=2.7),
                legendgroup=f"model_{key}",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    pressure_cases = [
        ("P_1", BLUE, "P_ar = 1 atm"),
        ("P_5", RED, "P_ar = 5 atm"),
    ]
    for key, color, label in pressure_cases:
        df = data[key]
        fig.add_trace(
            go.Scatter(
                x=df.current_density_A_cm2,
                y=df.V_cell_V,
                name=f"Modelo — {label}",
                line=dict(color=color, width=2.7),
                legendgroup=f"model_{key}",
            ),
            row=2,
            col=2,
        )

    if reference_data is not None:
        article_temperature_cases = [
            ("T_298", ARTICLE_BLUE_COMPLEMENT, "T = 298,15 K"),
            ("T_373", ARTICLE_RED_COMPLEMENT, "T = 373,15 K"),
        ]
        for key, color, label in article_temperature_cases:
            _add_article_trace_plotly(
                fig,
                reference_data["voltage"][key],
                row=1,
                col=1,
                name=f"Artigo — {label}",
                color=color,
                legendgroup=f"article_{key}",
                showlegend=True,
            )
            _add_article_trace_plotly(
                fig,
                reference_data["power"][key],
                row=1,
                col=2,
                name=f"Artigo — {label}",
                color=color,
                legendgroup=f"article_{key}",
                showlegend=False,
            )
            _add_article_trace_plotly(
                fig,
                reference_data["efficiency"][key],
                row=2,
                col=1,
                name=f"Artigo — {label}",
                color=color,
                legendgroup=f"article_{key}",
                showlegend=False,
            )

        article_pressure_cases = [
            ("P_1", ARTICLE_BLUE_COMPLEMENT, "P_ar = 1 atm"),
            ("P_5", ARTICLE_RED_COMPLEMENT, "P_ar = 5 atm"),
        ]
        for key, color, label in article_pressure_cases:
            _add_article_trace_plotly(
                fig,
                reference_data["pressure"][key],
                row=2,
                col=2,
                name=f"Artigo — {label}",
                color=color,
                legendgroup=f"article_{key}",
                showlegend=True,
            )

    for row, col in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        fig.update_xaxes(
            title_text="Densidade de corrente (A/cm²)",
            range=[0, 1.2],
            dtick=0.2,
            showgrid=True,
            gridcolor="rgba(100,100,100,0.35)",
            row=row,
            col=col,
        )

    fig.update_yaxes(title_text="Tensão da célula (V)", range=[0.5, 1.1], dtick=0.2, row=1, col=1)
    fig.update_yaxes(title_text="Potência (W)", range=[0, 6000], dtick=1000, row=1, col=2)
    fig.update_yaxes(title_text="Eficiência (%)", range=[25, 60], dtick=5, row=2, col=1)
    fig.update_yaxes(title_text="Tensão da célula (V)", range=[0.5, 1.1], dtick=0.1, row=2, col=2)
    fig.update_layout(
        height=820 if reference_data is not None else 760,
        margin=dict(l=40, r=30, t=110 if reference_data is not None else 80, b=40),
        legend=dict(orientation="h", y=1.12 if reference_data is not None else 1.08, x=0),
        hovermode="x unified",
    )
    return fig


def _plot_article_matplotlib(ax, df, *, color: str, label: str):
    ax.plot(
        df.current_density_A_cm2,
        df.value,
        color=color,
        linewidth=1.8,
        linestyle="--",
        marker="o",
        markersize=2.8,
        markerfacecolor="none",
        markeredgewidth=0.8,
        label=label,
    )


def _matplotlib_figure(data: dict, reference_data: dict | None = None):
    fig, axes = plt.subplots(2, 2, figsize=(13.34, 8.0), constrained_layout=True)
    ax1, ax2, ax3, ax4 = axes.flat

    for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
        df = data[key]
        ax1.plot(df.current_density_A_cm2, df.V_cell_V, color=color, linewidth=2.2, label=f"Modelo — {label}")
        ax2.plot(df.current_density_A_cm2, df.P_stack_W, color=color, linewidth=2.2, label=f"Modelo — {label}")
        ax3.plot(df.current_density_A_cm2, df.efficiency_percent, color=color, linewidth=2.2, label=f"Modelo — {label}")

    for key, color, label in [("P_1", BLUE, "P_ar = 1 atm"), ("P_5", RED, "P_ar = 5 atm")]:
        df = data[key]
        ax4.plot(df.current_density_A_cm2, df.V_cell_V, color=color, linewidth=2.2, label=f"Modelo — {label}")

    if reference_data is not None:
        article_temperature_cases = [
            ("T_298", ARTICLE_BLUE_COMPLEMENT, "T = 298,15 K"),
            ("T_373", ARTICLE_RED_COMPLEMENT, "T = 373,15 K"),
        ]
        for key, color, label in article_temperature_cases:
            _plot_article_matplotlib(
                ax1,
                reference_data["voltage"][key],
                color=color,
                label=f"Artigo — {label}",
            )
            _plot_article_matplotlib(
                ax2,
                reference_data["power"][key],
                color=color,
                label=f"Artigo — {label}",
            )
            _plot_article_matplotlib(
                ax3,
                reference_data["efficiency"][key],
                color=color,
                label=f"Artigo — {label}",
            )

        article_pressure_cases = [
            ("P_1", ARTICLE_BLUE_COMPLEMENT, "P_ar = 1 atm"),
            ("P_5", ARTICLE_RED_COMPLEMENT, "P_ar = 5 atm"),
        ]
        for key, color, label in article_pressure_cases:
            _plot_article_matplotlib(
                ax4,
                reference_data["pressure"][key],
                color=color,
                label=f"Artigo — {label}",
            )

    settings = [
        (ax1, "Tensão da célula (V)", (0.5, 1.1)),
        (ax2, "Potência (W)", (0, 6000)),
        (ax3, "Eficiência (%)", (25, 60)),
        (ax4, "Tensão da célula (V)", (0.5, 1.1)),
    ]
    for ax, ylabel, ylim in settings:
        ax.set_xlim(0, 1.2)
        ax.set_ylim(*ylim)
        ax.set_xlabel("Densidade de corrente (A/cm²)")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.55)
        ax.legend(loc="best", fontsize=8)

    ax1.set_title("Efeito da temperatura sobre a tensão")
    ax2.set_title("Potência do stack")
    ax3.set_title("Eficiência elétrica")
    ax4.set_title("Efeito da pressão do ar")
    return fig


def figure3_matplotlib_bytes(
    data: dict,
    fmt: str = "png",
    reference_data: dict | None = None,
) -> bytes:
    """Exporta os quatro painéis em PNG ou SVG.

    Quando ``reference_data`` é informado, o arquivo exportado contém a
    sobreposição das curvas digitalizadas do artigo.
    """
    fig = _matplotlib_figure(data, reference_data=reference_data)
    buffer = BytesIO()
    fig.savefig(buffer, format=fmt, dpi=180 if fmt == "png" else None, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()
