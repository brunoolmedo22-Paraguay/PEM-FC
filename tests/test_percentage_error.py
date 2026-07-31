from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from models.pemfc_model import PEMFCModel
from pemfc_config import DEFAULT_PARAMS
from simulation.solver import build_figure3_dataset
from visualization.plots import (
    _single_error_panel_matplotlib_figure,
    _temperature_error_zoom_matplotlib_figure,
    _temperature_voltage_zoom_matplotlib_figure,
    figure3_percentage_error_plotly,
    figure3_single_error_panel_bytes,
    figure3_temperature_error_zoom_svg_bytes,
    figure3_temperature_voltage_zoom_svg_bytes,
)


def _reference_data():
    root = Path(__file__).resolve().parents[1] / "data" / "otekon_figure3"
    return {
        "voltage": {
            "T_298": pd.read_csv(root / "voltage_298K.csv"),
            "T_373": pd.read_csv(root / "voltage_373K.csv"),
        },
        "power": {
            "T_298": pd.read_csv(root / "power_298K.csv"),
            "T_373": pd.read_csv(root / "power_373K.csv"),
        },
        "efficiency": {
            "T_298": pd.read_csv(root / "efficiency_298K.csv"),
            "T_373": pd.read_csv(root / "efficiency_373K.csv"),
        },
        "pressure": {
            "P_1": pd.read_csv(root / "pressure_1atm.csv"),
            "P_5": pd.read_csv(root / "pressure_5atm.csv"),
        },
    }


def test_percentage_error_plot_has_all_curves_and_nonnegative_values():
    data = build_figure3_dataset(PEMFCModel(DEFAULT_PARAMS))
    reference = _reference_data()
    figure = figure3_percentage_error_plotly(data, reference)

    assert len(figure.data) == 8
    assert all(len(trace.x) == 101 for trace in figure.data)
    assert all(min(trace.y) >= 0 for trace in figure.data)
    assert tuple(figure.layout.xaxis.range) == (0, 1.0)

    annotation_texts = [annotation.text or "" for annotation in figure.layout.annotations]
    assert "Erro na tensão — efeito da temperatura" not in annotation_texts
    assert any("Máx." in text for text in annotation_texts)
    assert any("Mín." in text for text in annotation_texts)

    matplotlib_figure = _single_error_panel_matplotlib_figure(
        data,
        "error_voltage_temperature",
        reference,
    )
    axis = matplotlib_figure.axes[0]
    assert axis.get_title() == ""
    assert axis.get_xlim() == (0.0, 1.0)
    assert any("Máx." in text.get_text() for text in axis.texts)
    assert any("Mín." in text.get_text() for text in axis.texts)
    plt.close(matplotlib_figure)

    svg = figure3_single_error_panel_bytes(
        data,
        "error_voltage_temperature",
        "svg",
        reference_data=reference,
    ).decode("utf-8")
    assert "Erro na tensão — efeito da temperatura" not in svg
    assert "Máx." in svg
    assert "Mín." in svg

    zoom_figure = _temperature_error_zoom_matplotlib_figure(data, reference)
    assert len(zoom_figure.axes) == 2
    assert zoom_figure.axes[0].get_xlim() == (0.0, 1.0)
    assert zoom_figure.axes[1].get_xlim()[1] < 0.2
    plt.close(zoom_figure)

    zoom_svg = figure3_temperature_error_zoom_svg_bytes(data, reference).decode("utf-8")
    assert "Máx.:" in zoom_svg
    assert "Mín.:" in zoom_svg
    assert "Erro na tensão — efeito da temperatura" not in zoom_svg

    voltage_zoom_figure = _temperature_voltage_zoom_matplotlib_figure(data, reference)
    assert len(voltage_zoom_figure.axes) == 3
    assert voltage_zoom_figure.axes[0].get_xlim() == (0.0, 1.0)
    plt.close(voltage_zoom_figure)

    voltage_zoom_svg = figure3_temperature_voltage_zoom_svg_bytes(data, reference).decode("utf-8")
    assert "MAIOR DIFERENÇA" in voltage_zoom_svg
    assert "MENOR DIFERENÇA" in voltage_zoom_svg
    assert "MODELO PROPOSTO" in voltage_zoom_svg
    assert "N. ALTINTAŞ AND R. ERTAN" in voltage_zoom_svg
    assert "Efeito da temperatura sobre a tensão" not in voltage_zoom_svg
