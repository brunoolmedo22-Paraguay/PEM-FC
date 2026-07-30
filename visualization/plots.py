from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
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


def _percentage_error_series(model_df, reference_df, model_column: str):
    """Calcula o erro percentual absoluto nos pontos x digitalizados do artigo."""
    x_reference = reference_df["current_density_A_cm2"].to_numpy(dtype=float)
    article_values = reference_df["value"].to_numpy(dtype=float)
    model_values = np.interp(
        x_reference,
        model_df["current_density_A_cm2"].to_numpy(dtype=float),
        model_df[model_column].to_numpy(dtype=float),
    )
    denominator = np.maximum(np.abs(article_values), 1e-12)
    error_percent = np.abs(model_values - article_values) / denominator * 100.0
    return x_reference, error_percent, model_values, article_values


def _add_percentage_error_trace(
    fig,
    model_df,
    reference_df,
    *,
    model_column: str,
    row: int,
    col: int,
    name: str,
    color: str,
    legendgroup: str,
    showlegend: bool,
):
    x, error_percent, model_values, article_values = _percentage_error_series(
        model_df, reference_df, model_column
    )
    customdata = np.column_stack((model_values, article_values))
    fig.add_trace(
        go.Scatter(
            x=x,
            y=error_percent,
            name=name,
            mode="lines+markers",
            line=dict(color=color, width=2.2),
            marker=dict(color=color, size=4),
            legendgroup=legendgroup,
            showlegend=showlegend,
            customdata=customdata,
            hovertemplate=(
                "Densidade de corrente: %{x:.4f} A/cm²"
                "<br>Modelo: %{customdata[0]:.4f}"
                "<br>Artigo: %{customdata[1]:.4f}"
                "<br>Erro absoluto: %{y:.3f}%<extra></extra>"
            ),
        ),
        row=row,
        col=col,
    )


def figure3_percentage_error_plotly(data: dict, reference_data: dict):
    """Gera o erro percentual absoluto ponto a ponto da replicação da Figura 3."""
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Erro na tensão — efeito da temperatura",
            "Erro na potência do stack",
            "Erro na eficiência elétrica",
            "Erro na tensão — efeito da pressão",
        ),
        horizontal_spacing=0.12,
        vertical_spacing=0.18,
    )

    temperature_cases = [
        ("T_298", BLUE, "T = 298,15 K"),
        ("T_373", RED, "T = 373,15 K"),
    ]
    quantity_columns = {
        "voltage": "V_cell_V",
        "power": "P_stack_W",
        "efficiency": "efficiency_percent",
    }
    panel_positions = {
        "voltage": (1, 1),
        "power": (1, 2),
        "efficiency": (2, 1),
    }

    for quantity, model_column in quantity_columns.items():
        row, col = panel_positions[quantity]
        for key, color, label in temperature_cases:
            _add_percentage_error_trace(
                fig,
                data[key],
                reference_data[quantity][key],
                model_column=model_column,
                row=row,
                col=col,
                name=label,
                color=color,
                legendgroup=f"error_temperature_{key}",
                showlegend=quantity == "voltage",
            )

    pressure_cases = [
        ("P_1", BLUE, "P_ar = 1 atm"),
        ("P_5", RED, "P_ar = 5 atm"),
    ]
    for key, color, label in pressure_cases:
        _add_percentage_error_trace(
            fig,
            data[key],
            reference_data["pressure"][key],
            model_column="V_cell_V",
            row=2,
            col=2,
            name=label,
            color=color,
            legendgroup=f"error_pressure_{key}",
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
        fig.update_yaxes(
            title_text="Erro percentual absoluto (%)",
            rangemode="tozero",
            showgrid=True,
            gridcolor="rgba(100,100,100,0.35)",
            row=row,
            col=col,
        )

    fig.update_layout(
        height=820,
        margin=dict(l=40, r=30, t=115, b=40),
        legend=dict(orientation="h", y=1.13, x=0),
        hovermode="x unified",
    )
    return fig


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

def _plot_voltage_error_matplotlib(ax, model_df, reference_df, *, model_column: str, color: str, label: str):
    x, error_percent, _, _ = _percentage_error_series(model_df, reference_df, model_column)
    ax.plot(
        x,
        error_percent,
        color=color,
        linewidth=2.0,
        marker="o",
        markersize=2.8,
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


def _voltage_error_matplotlib_figure(data: dict, reference_data: dict):
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), constrained_layout=True)
    ax1, ax2 = axes.flat

    for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
        _plot_voltage_error_matplotlib(
            ax1,
            data[key],
            reference_data["voltage"][key],
            model_column="V_cell_V",
            color=color,
            label=label,
        )

    for key, color, label in [("P_1", BLUE, "P_ar = 1 atm"), ("P_5", RED, "P_ar = 5 atm")]:
        _plot_voltage_error_matplotlib(
            ax2,
            data[key],
            reference_data["pressure"][key],
            model_column="V_cell_V",
            color=color,
            label=label,
        )

    for ax in (ax1, ax2):
        ax.set_xlim(0, 1.2)
        ax.set_xlabel("Densidade de corrente (A/cm²)")
        ax.set_ylabel("Erro percentual absoluto (%)")
        ax.grid(True, alpha=0.55)
        ax.legend(loc="best", fontsize=8)

    ax1.set_title("Erro na tensão — efeito da temperatura")
    ax2.set_title("Erro na tensão — efeito da pressão")
    return fig


def _single_panel_matplotlib_figure(
    data: dict,
    panel: str,
    reference_data: dict | None = None,
):
    fig, ax = plt.subplots(1, 1, figsize=(6.6, 4.8), constrained_layout=True)

    if panel == "voltage_temperature":
        for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
            df = data[key]
            ax.plot(df.current_density_A_cm2, df.V_cell_V, color=color, linewidth=2.2, label=f"Modelo — {label}")
        if reference_data is not None:
            for key, color, label in [("T_298", ARTICLE_BLUE_COMPLEMENT, "T = 298,15 K"), ("T_373", ARTICLE_RED_COMPLEMENT, "T = 373,15 K")]:
                _plot_article_matplotlib(ax, reference_data["voltage"][key], color=color, label=f"Artigo — {label}")
        ax.set_title("Efeito da temperatura sobre a tensão")
        ax.set_ylabel("Tensão da célula (V)")
        ax.set_ylim(0.5, 1.1)

    elif panel == "power_stack":
        for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
            df = data[key]
            ax.plot(df.current_density_A_cm2, df.P_stack_W, color=color, linewidth=2.2, label=f"Modelo — {label}")
        if reference_data is not None:
            for key, color, label in [("T_298", ARTICLE_BLUE_COMPLEMENT, "T = 298,15 K"), ("T_373", ARTICLE_RED_COMPLEMENT, "T = 373,15 K")]:
                _plot_article_matplotlib(ax, reference_data["power"][key], color=color, label=f"Artigo — {label}")
        ax.set_title("Potência do stack")
        ax.set_ylabel("Potência (W)")
        ax.set_ylim(0, 6000)

    elif panel == "efficiency":
        for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
            df = data[key]
            ax.plot(df.current_density_A_cm2, df.efficiency_percent, color=color, linewidth=2.2, label=f"Modelo — {label}")
        if reference_data is not None:
            for key, color, label in [("T_298", ARTICLE_BLUE_COMPLEMENT, "T = 298,15 K"), ("T_373", ARTICLE_RED_COMPLEMENT, "T = 373,15 K")]:
                _plot_article_matplotlib(ax, reference_data["efficiency"][key], color=color, label=f"Artigo — {label}")
        ax.set_title("Eficiência elétrica")
        ax.set_ylabel("Eficiência (%)")
        ax.set_ylim(25, 60)

    elif panel == "voltage_pressure":
        for key, color, label in [("P_1", BLUE, "P_ar = 1 atm"), ("P_5", RED, "P_ar = 5 atm")]:
            df = data[key]
            ax.plot(df.current_density_A_cm2, df.V_cell_V, color=color, linewidth=2.2, label=f"Modelo — {label}")
        if reference_data is not None:
            for key, color, label in [("P_1", ARTICLE_BLUE_COMPLEMENT, "P_ar = 1 atm"), ("P_5", ARTICLE_RED_COMPLEMENT, "P_ar = 5 atm")]:
                _plot_article_matplotlib(ax, reference_data["pressure"][key], color=color, label=f"Artigo — {label}")
        ax.set_title("Efeito da pressão do ar")
        ax.set_ylabel("Tensão da célula (V)")
        ax.set_ylim(0.5, 1.1)

    else:
        raise ValueError(f"Painel desconhecido: {panel}")

    ax.set_xlim(0, 1.2)
    ax.set_xlabel("Densidade de corrente (A/cm²)")
    ax.grid(True, alpha=0.55)
    ax.legend(loc="best", fontsize=8)
    return fig


def figure3_single_panel_bytes(
    data: dict,
    panel: str,
    fmt: str = "svg",
    reference_data: dict | None = None,
) -> bytes:
    """Exporta individualmente um dos painéis da Figura 3.

    Panels aceitos: voltage_temperature, power_stack, efficiency, voltage_pressure.
    """
    fig = _single_panel_matplotlib_figure(data, panel, reference_data=reference_data)
    buffer = BytesIO()
    fig.savefig(buffer, format=fmt, dpi=180 if fmt == "png" else None, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def _single_error_panel_matplotlib_figure(data: dict, panel: str, reference_data: dict):
    fig, ax = plt.subplots(1, 1, figsize=(6.6, 4.8), constrained_layout=True)

    if panel == "error_voltage_temperature":
        for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
            _plot_voltage_error_matplotlib(
                ax,
                data[key],
                reference_data["voltage"][key],
                model_column="V_cell_V",
                color=color,
                label=label,
            )
        ax.set_title("Erro na tensão — efeito da temperatura")

    elif panel == "error_voltage_pressure":
        for key, color, label in [("P_1", BLUE, "P_ar = 1 atm"), ("P_5", RED, "P_ar = 5 atm")]:
            _plot_voltage_error_matplotlib(
                ax,
                data[key],
                reference_data["pressure"][key],
                model_column="V_cell_V",
                color=color,
                label=label,
            )
        ax.set_title("Erro na tensão — efeito da pressão")

    else:
        raise ValueError(f"Painel de erro desconhecido: {panel}")

    ax.set_xlim(0, 1.2)
    ax.set_xlabel("Densidade de corrente (A/cm²)")
    ax.set_ylabel("Erro percentual absoluto (%)")
    ax.grid(True, alpha=0.55)
    ax.legend(loc="best", fontsize=8)
    return fig


def figure3_single_error_panel_bytes(data: dict, panel: str, fmt: str = "svg", reference_data: dict | None = None) -> bytes:
    """Exporta individualmente um painel de erro percentual da tensão.

    Panels aceitos: error_voltage_temperature, error_voltage_pressure.
    """
    if reference_data is None:
        raise ValueError("reference_data é obrigatório para exportar gráficos de erro.")
    fig = _single_error_panel_matplotlib_figure(data, panel, reference_data)
    buffer = BytesIO()
    fig.savefig(buffer, format=fmt, dpi=180 if fmt == "png" else None, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def figure3_voltage_error_svg_bytes(data: dict, reference_data: dict) -> bytes:
    """Exporta em SVG apenas os gráficos de erro percentual da tensão.

    O arquivo contém dois painéis: tensão vs. temperatura e tensão vs. pressão.
    """
    fig = _voltage_error_matplotlib_figure(data, reference_data)
    buffer = BytesIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


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
