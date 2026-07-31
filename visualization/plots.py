from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from plotly.subplots import make_subplots


# Cores do modelo.
BLUE = "#006BBD"
RED = "#FF0000"

# Cores complementares utilizadas exclusivamente para as curvas digitalizadas
# do artigo. Azul -> laranja; vermelho -> ciano.
ARTICLE_BLUE_COMPLEMENT = "#FF8A00"
ARTICLE_RED_COMPLEMENT = "#00A6D6"

# Identificação padronizada das curvas de tensão × temperatura. Estes textos
# são usados em todas as rotas (Plotly, SVG geral e SVG individual) para evitar
# que cada botão exporte uma legenda diferente.
PROPOSED_MODEL_LABEL = "MODELO PROPOSTO"
ARTICLE_SHORT_REFERENCE = "N. ALTINTAŞ AND R. ERTAN"


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


def _temperature_voltage_error_extrema(data: dict, reference_data: dict):
    """Retorna os extremos globais das duas curvas entre 0 e 1 A/cm²."""
    candidates = []
    temperature_cases = [
        ("T_298", "T = 298,15 K"),
        ("T_373", "T = 373,15 K"),
    ]

    for key, temperature_label in temperature_cases:
        x, error_percent, _, _ = _percentage_error_series(
            data[key],
            reference_data["voltage"][key],
            "V_cell_V",
        )
        valid = (
            np.isfinite(x)
            & np.isfinite(error_percent)
            & (x >= 0.0)
            & (x <= 1.0)
        )
        x_valid = x[valid]
        error_valid = error_percent[valid]
        if len(x_valid) == 0:
            continue

        for index in (int(np.argmin(error_valid)), int(np.argmax(error_valid))):
            candidates.append(
                {
                    "current_density": float(x_valid[index]),
                    "error_percent": float(error_valid[index]),
                    "temperature": temperature_label,
                }
            )

    if not candidates:
        raise ValueError("Não há pontos válidos para calcular os extremos do erro.")

    minimum = min(candidates, key=lambda point: point["error_percent"])
    maximum = max(candidates, key=lambda point: point["error_percent"])
    return minimum, maximum


def _temperature_voltage_difference_extrema(data: dict, reference_data: dict):
    """Retorna as diferenças absolutas mínima e máxima entre modelo e artigo."""
    candidates = []
    for key, temperature_label in [
        ("T_298", "T = 298,15 K"),
        ("T_373", "T = 373,15 K"),
    ]:
        x, _, model_values, article_values = _percentage_error_series(
            data[key], reference_data["voltage"][key], "V_cell_V"
        )
        differences = np.abs(model_values - article_values)
        valid = (
            np.isfinite(x)
            & np.isfinite(differences)
            & (x >= 0.0)
            & (x <= 1.0)
        )
        x_valid = x[valid]
        differences_valid = differences[valid]
        model_valid = model_values[valid]
        article_valid = article_values[valid]
        if len(x_valid) == 0:
            continue

        for index in (int(np.argmin(differences_valid)), int(np.argmax(differences_valid))):
            candidates.append(
                {
                    "key": key,
                    "temperature": temperature_label,
                    "current_density": float(x_valid[index]),
                    "difference_V": float(differences_valid[index]),
                    "model_V": float(model_valid[index]),
                    "article_V": float(article_valid[index]),
                }
            )

    if not candidates:
        raise ValueError("Não há pontos válidos para calcular as diferenças de tensão.")
    return (
        min(candidates, key=lambda point: point["difference_V"]),
        max(candidates, key=lambda point: point["difference_V"]),
    )


def _decimal_comma(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _add_temperature_error_extrema_annotations_plotly(
    fig,
    data: dict,
    reference_data: dict,
):
    minimum, maximum = _temperature_voltage_error_extrema(data, reference_data)
    annotations = [
        ("Máx.", maximum, 95, 38, "#8B1A1A", 3),
        ("Mín.", minimum, 75, -58, "#176B3A", 4),
    ]
    for label, point, ax_offset, ay_offset, color, digits in annotations:
        text = (
            f"<b>{label}: {_decimal_comma(point['error_percent'], digits)}%</b>"
            f"<br>em {_decimal_comma(point['current_density'], 3)} A/cm²"
            f"<br>{point['temperature']}"
        )
        fig.add_annotation(
            x=point["current_density"],
            y=point["error_percent"],
            text=text,
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1.3,
            arrowcolor=color,
            ax=ax_offset,
            ay=ay_offset,
            bgcolor="rgba(255,255,255,0.94)",
            bordercolor=color,
            borderwidth=1,
            borderpad=4,
            font=dict(size=10, color="#222222"),
            align="left",
            row=1,
            col=1,
        )


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
            "",
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

    _add_temperature_error_extrema_annotations_plotly(fig, data, reference_data)

    for row, col in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        fig.update_xaxes(
            title_text="Densidade de corrente (A/cm²)",
            range=[0, 1.0] if (row, col) == (1, 1) else [0, 1.2],
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
            "",
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
                name=f"{PROPOSED_MODEL_LABEL} — {label}",
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
                name=f"{ARTICLE_SHORT_REFERENCE} — {label}",
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
            range=[0, 1.0] if (row, col) == (1, 1) else [0, 1.2],
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


def _annotate_temperature_error_extrema_matplotlib(
    ax,
    data: dict,
    reference_data: dict,
):
    minimum, maximum = _temperature_voltage_error_extrema(data, reference_data)
    annotations = [
        ("Máx.", maximum, (78, -28), "#8B1A1A", 3, "top"),
        ("Mín.", minimum, (38, 52), "#176B3A", 4, "bottom"),
    ]

    for label, point, offset, color, digits, vertical_alignment in annotations:
        ax.scatter(
            [point["current_density"]],
            [point["error_percent"]],
            s=48,
            facecolor="white",
            edgecolor=color,
            linewidth=1.5,
            zorder=6,
        )
        annotation_text = (
            f"{label}: {_decimal_comma(point['error_percent'], digits)}%\n"
            f"em {_decimal_comma(point['current_density'], 3)} A/cm²\n"
            f"{point['temperature']}"
        )
        ax.annotate(
            annotation_text,
            xy=(point["current_density"], point["error_percent"]),
            xytext=offset,
            textcoords="offset points",
            ha="left",
            va=vertical_alignment,
            fontsize=7.5,
            color="#222222",
            bbox=dict(
                boxstyle="round,pad=0.32",
                facecolor="white",
                edgecolor=color,
                alpha=0.95,
            ),
            arrowprops=dict(
                arrowstyle="->",
                color=color,
                linewidth=1.2,
                shrinkA=2,
                shrinkB=3,
            ),
            zorder=7,
        )



def _matplotlib_figure(data: dict, reference_data: dict | None = None):
    fig, axes = plt.subplots(2, 2, figsize=(13.34, 8.0), constrained_layout=True)
    ax1, ax2, ax3, ax4 = axes.flat

    for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
        df = data[key]
        ax1.plot(
            df.current_density_A_cm2,
            df.V_cell_V,
            color=color,
            linewidth=2.2,
            label=f"{PROPOSED_MODEL_LABEL} — {label}",
        )
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
                label=f"{ARTICLE_SHORT_REFERENCE} — {label}",
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
        (ax1, "Tensão da célula (V)", (0.5, 1.1), 1.0),
        (ax2, "Potência (W)", (0, 6000), 1.2),
        (ax3, "Eficiência (%)", (25, 60), 1.2),
        (ax4, "Tensão da célula (V)", (0.5, 1.1), 1.2),
    ]
    for ax, ylabel, ylim, x_max in settings:
        ax.set_xlim(0, x_max)
        ax.set_ylim(*ylim)
        ax.set_xlabel("Densidade de corrente (A/cm²)")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.55)
        ax.legend(loc="best", fontsize=8)

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

    _annotate_temperature_error_extrema_matplotlib(ax1, data, reference_data)

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
        ax.set_xlabel("Densidade de corrente (A/cm²)")
        ax.set_ylabel("Erro percentual absoluto (%)")
        ax.grid(True, alpha=0.55)
        ax.legend(loc="best", fontsize=8)

    ax1.set_xlim(0, 1.0)
    ax2.set_xlim(0, 1.2)
    ax2.set_title("Erro na tensão — efeito da pressão")
    return fig


def _single_panel_matplotlib_figure(
    data: dict,
    panel: str,
    reference_data: dict | None = None,
):
    # O painel de tensão × temperatura é inserido no artigo com o título na
    # legenda do LaTeX. Por isso, sua exportação é 25% mais baixa que o padrão.
    figure_height = 3.6 if panel == "voltage_temperature" else 4.8
    x_max = 1.0 if panel == "voltage_temperature" else 1.2
    fig, ax = plt.subplots(1, 1, figsize=(6.6, figure_height), constrained_layout=True)

    if panel == "voltage_temperature":
        for key, color, label in [("T_298", BLUE, "T = 298,15 K"), ("T_373", RED, "T = 373,15 K")]:
            df = data[key]
            ax.plot(
                df.current_density_A_cm2,
                df.V_cell_V,
                color=color,
                linewidth=2.2,
                label=f"{PROPOSED_MODEL_LABEL} — {label}",
            )
        if reference_data is not None:
            for key, color, label in [("T_298", ARTICLE_BLUE_COMPLEMENT, "T = 298,15 K"), ("T_373", ARTICLE_RED_COMPLEMENT, "T = 373,15 K")]:
                _plot_article_matplotlib(
                    ax,
                    reference_data["voltage"][key],
                    color=color,
                    label=f"{ARTICLE_SHORT_REFERENCE} — {label}",
                )
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

    ax.set_xlim(0, x_max)
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
        _annotate_temperature_error_extrema_matplotlib(ax, data, reference_data)
        x_max = 1.0

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
        x_max = 1.2

    else:
        raise ValueError(f"Painel de erro desconhecido: {panel}")

    ax.set_xlim(0, x_max)
    ax.set_xlabel("Densidade de corrente (A/cm²)")
    ax.set_ylabel("Erro percentual absoluto (%)")
    ax.grid(True, alpha=0.55)
    ax.legend(loc="best", fontsize=8)
    return fig


def _temperature_error_zoom_matplotlib_figure(data: dict, reference_data: dict):
    """Cria o erro de tensão com um detalhe ampliado ao redor do máximo."""
    fig, ax = plt.subplots(1, 1, figsize=(6.6, 4.8), constrained_layout=True)

    curves = []
    for key, color, label in [
        ("T_298", BLUE, "T = 298,15 K"),
        ("T_373", RED, "T = 373,15 K"),
    ]:
        x, error_percent, _, _ = _percentage_error_series(
            data[key], reference_data["voltage"][key], "V_cell_V"
        )
        curves.append((x, error_percent, color, label))
        ax.plot(
            x,
            error_percent,
            color=color,
            linewidth=2.0,
            marker="o",
            markersize=2.8,
            label=label,
        )

    minimum, maximum = _temperature_voltage_error_extrema(data, reference_data)

    # O recorte acompanha automaticamente o máximo, mas permanece dentro do
    # domínio físico exibido no gráfico principal.
    zoom_half_width = 0.055
    zoom_x_min = max(0.0, maximum["current_density"] - zoom_half_width)
    zoom_x_max = min(1.0, maximum["current_density"] + zoom_half_width)
    local_values = np.concatenate(
        [
            error[(x >= zoom_x_min) & (x <= zoom_x_max)]
            for x, error, _, _ in curves
        ]
    )
    local_y_min = max(0.0, float(np.min(local_values)) - 0.08)
    local_y_max = float(np.max(local_values)) + 0.13

    inset = inset_axes(
        ax,
        width="44%",
        height="43%",
        loc="upper right",
        borderpad=1.05,
    )
    for x, error_percent, color, _ in curves:
        inset.plot(
            x,
            error_percent,
            color=color,
            linewidth=1.55,
            marker="o",
            markersize=2.2,
        )
    inset.set_xlim(zoom_x_min, zoom_x_max)
    inset.set_ylim(local_y_min, local_y_max)
    inset.grid(True, alpha=0.38, linewidth=0.55)
    inset.tick_params(labelsize=6.3, pad=1.5)
    inset.scatter(
        [maximum["current_density"]],
        [maximum["error_percent"]],
        s=31,
        facecolor="white",
        edgecolor="#8B1A1A",
        linewidth=1.2,
        zorder=6,
    )
    inset.annotate(
        f"Máx.: {_decimal_comma(maximum['error_percent'], 3)}%",
        xy=(maximum["current_density"], maximum["error_percent"]),
        xytext=(21, -22),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=6.6,
        color="#8B1A1A",
        arrowprops=dict(arrowstyle="->", color="#8B1A1A", linewidth=0.9),
    )
    mark_inset(
        ax,
        inset,
        loc1=2,
        loc2=4,
        fc="none",
        ec="#555555",
        linestyle="--",
        linewidth=0.9,
    )

    # Mantém a informação do mínimo global no painel principal; o máximo é
    # identificado dentro do detalhe ampliado para evitar textos duplicados.
    ax.scatter(
        [minimum["current_density"]],
        [minimum["error_percent"]],
        s=42,
        facecolor="white",
        edgecolor="#176B3A",
        linewidth=1.3,
        zorder=6,
    )
    ax.annotate(
        f"Mín.: {_decimal_comma(minimum['error_percent'], 4)}%\n"
        f"em {_decimal_comma(minimum['current_density'], 3)} A/cm²",
        xy=(minimum["current_density"], minimum["error_percent"]),
        xytext=(18, 34),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=7.2,
        color="#222222",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="white", edgecolor="#176B3A", alpha=0.95),
        arrowprops=dict(arrowstyle="->", color="#176B3A", linewidth=1.0),
        zorder=7,
    )

    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.06, maximum["error_percent"] * 1.12)
    ax.set_xlabel("Densidade de corrente (A/cm²)")
    ax.set_ylabel("Erro percentual absoluto (%)")
    ax.grid(True, alpha=0.55)
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        fontsize=8,
        ncol=2,
        borderaxespad=0.0,
    )
    return fig


def _temperature_voltage_zoom_matplotlib_figure(data: dict, reference_data: dict):
    """Cria tensão × temperatura com detalhes das diferenças extrema."""
    fig, ax = plt.subplots(1, 1, figsize=(6.6, 3.9), constrained_layout=True)
    model_colors = {"T_298": BLUE, "T_373": RED}
    article_colors = {
        "T_298": ARTICLE_BLUE_COMPLEMENT,
        "T_373": ARTICLE_RED_COMPLEMENT,
    }
    temperature_labels = {"T_298": "T = 298,15 K", "T_373": "T = 373,15 K"}

    for key in ("T_298", "T_373"):
        label = temperature_labels[key]
        df = data[key]
        ax.plot(
            df.current_density_A_cm2,
            df.V_cell_V,
            color=model_colors[key],
            linewidth=2.2,
            label=f"{PROPOSED_MODEL_LABEL} — {label}",
        )
        _plot_article_matplotlib(
            ax,
            reference_data["voltage"][key],
            color=article_colors[key],
            label=f"{ARTICLE_SHORT_REFERENCE} — {label}",
        )

    minimum, maximum = _temperature_voltage_difference_extrema(data, reference_data)

    def add_difference_inset(point, *, bounds, title, edge_color):
        # ``bounds`` usa coordenadas relativas ao painel principal. Assim os
        # detalhes ficam menores e, sobretudo, afastados dos rótulos do eixo x.
        inset = ax.inset_axes(bounds)
        key = point["key"]
        model_df = data[key]
        article_df = reference_data["voltage"][key]
        center = point["current_density"]
        half_width = 0.045 if center < 0.1 else 0.065
        x_min = max(0.0, center - half_width)
        x_max = min(1.0, center + half_width)

        inset.plot(
            model_df.current_density_A_cm2,
            model_df.V_cell_V,
            color=model_colors[key],
            linewidth=1.6,
        )
        inset.plot(
            article_df.current_density_A_cm2,
            article_df.value,
            color=article_colors[key],
            linewidth=1.45,
            linestyle="--",
            marker="o",
            markersize=2.0,
            markerfacecolor="none",
        )

        mask_model = (
            (model_df.current_density_A_cm2.to_numpy() >= x_min)
            & (model_df.current_density_A_cm2.to_numpy() <= x_max)
        )
        mask_article = (
            (article_df.current_density_A_cm2.to_numpy() >= x_min)
            & (article_df.current_density_A_cm2.to_numpy() <= x_max)
        )
        local_y = np.concatenate(
            [
                model_df.V_cell_V.to_numpy()[mask_model],
                article_df.value.to_numpy()[mask_article],
            ]
        )
        padding = max(0.0015, 0.14 * float(np.ptp(local_y)))
        inset.set_xlim(x_min, x_max)
        inset.set_ylim(float(np.min(local_y)) - padding, float(np.max(local_y)) + padding)
        inset.grid(True, alpha=0.38, linewidth=0.5)
        inset.tick_params(labelsize=5.8, pad=1.2)
        inset.text(
            0.5,
            0.96,
            f"{title}: {_decimal_comma(point['difference_V'] * 1000.0, 3)} mV\n"
            f"{point['temperature']}",
            transform=inset.transAxes,
            ha="center",
            va="top",
            fontsize=6.1,
            color=edge_color,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.86, pad=1.0),
            zorder=8,
        )
        inset.scatter(
            [center, center],
            [point["model_V"], point["article_V"]],
            s=22,
            facecolor="white",
            edgecolor=edge_color,
            linewidth=1.0,
            zorder=6,
        )
        mark_inset(
            ax,
            inset,
            loc1=2,
            loc2=4,
            fc="none",
            ec=edge_color,
            linestyle="--",
            linewidth=0.85,
        )

    add_difference_inset(
        maximum,
        bounds=[0.34, 0.64, 0.27, 0.28],
        title="MAIOR DIFERENÇA",
        edge_color="#8B1A1A",
    )
    add_difference_inset(
        minimum,
        bounds=[0.04, 0.17, 0.27, 0.27],
        title="MENOR DIFERENÇA",
        edge_color="#176B3A",
    )

    ax.set_xlim(0, 1.0)
    ax.set_ylim(0.5, 1.1)
    ax.set_xlabel("Densidade de corrente (A/cm²)")
    ax.set_ylabel("Tensão da célula (V)")
    ax.grid(True, alpha=0.55)
    ax.legend(
        loc="upper right",
        fontsize=5.5,
        ncol=1,
        borderaxespad=0.45,
    )
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


def figure3_temperature_error_zoom_svg_bytes(data: dict, reference_data: dict) -> bytes:
    """Exporta o erro de tensão por temperatura com detalhe ampliado em SVG."""
    fig = _temperature_error_zoom_matplotlib_figure(data, reference_data)
    buffer = BytesIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()


def figure3_temperature_voltage_zoom_svg_bytes(data: dict, reference_data: dict) -> bytes:
    """Exporta tensão × temperatura com zoom nas diferenças mínima e máxima."""
    fig = _temperature_voltage_zoom_matplotlib_figure(data, reference_data)
    buffer = BytesIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight")
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
