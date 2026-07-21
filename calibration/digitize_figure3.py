"""Digitalização reprodutível das curvas da imagem original da Figura 3.

Este script é apenas uma ferramenta de auditoria. A aplicação não o importa.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "data" / "otekon_figure3" / "figure3_source.png"
OUT = IMAGE.parent

BOUNDS = {
    "TL": dict(x0=101, x1=559, y0=66, y1=349, xmin=0.0, xmax=1.2, ymin=0.5, ymax=1.1),
    "TR": dict(x0=725, x1=1194, y0=61, y1=359, xmin=0.0, xmax=1.2, ymin=0.0, ymax=6000.0),
    "BL": dict(x0=108, x1=558, y0=440, y1=708, xmin=0.0, xmax=1.2, ymin=25.0, ymax=60.0),
    "BR": dict(x0=736, x1=1202, y0=436, y1=715, xmin=0.0, xmax=1.2, ymin=0.5, ymax=1.1),
}


def color_masks(image: np.ndarray):
    r, g, b = [image[:, :, k].astype(int) for k in range(3)]
    red = (r > 150) & (r > g + 70) & (r > b + 70)
    blue = (b > 120) & (b > r + 70) & (b > g + 20) & (g > 40)
    return {"red": red, "blue": blue}


def pixel_to_data(x, y, bounds):
    x_data = bounds["xmin"] + (x - bounds["x0"]) / (bounds["x1"] - bounds["x0"]) * (bounds["xmax"] - bounds["xmin"])
    y_data = bounds["ymax"] - (y - bounds["y0"]) / (bounds["y1"] - bounds["y0"]) * (bounds["ymax"] - bounds["ymin"])
    return x_data, y_data


def curve_component(mask, panel):
    b = BOUNDS[panel]
    x_end = round(b["x0"] + (1.02 / 1.2) * (b["x1"] - b["x0"]))
    sub = mask[b["y0"]:b["y1"] + 1, b["x0"]:x_end + 1]
    labels, count = ndimage.label(sub, structure=np.ones((3, 3)))
    components = []
    for idx in range(1, count + 1):
        yy, xx = np.where(labels == idx)
        if len(xx) < 20:
            continue
        if np.ptp(xx) > 100 and np.ptp(yy) > 20:
            components.append((len(xx), idx))
    _, selected = max(components)
    yy, xx = np.where(labels == selected)
    return xx + b["x0"], yy + b["y0"]


def extract(mask, panel, sample_points=101):
    x, y = curve_component(mask, panel)
    unique_x = np.unique(x)
    center_y = np.array([np.median(y[x == value]) for value in unique_x])
    x_data, y_data = pixel_to_data(unique_x, center_y, BOUNDS[panel])
    valid = (x_data >= 0.0) & (x_data <= 1.01)
    observed_x = x_data[valid]
    observed_y = y_data[valid]
    start = max(0.01, float(np.min(observed_x)))
    grid = np.linspace(start, 1.0, sample_points)
    values = np.interp(grid, observed_x, observed_y)
    return pd.DataFrame({"current_density_A_cm2": grid, "value": values})


def main():
    image = np.asarray(Image.open(IMAGE).convert("RGB"))
    masks = color_masks(image)
    mapping = {
        "voltage_298K.csv": ("TL", "blue"),
        "voltage_373K.csv": ("TL", "red"),
        "power_298K.csv": ("TR", "blue"),
        "power_373K.csv": ("TR", "red"),
        "efficiency_298K.csv": ("BL", "blue"),
        "efficiency_373K.csv": ("BL", "red"),
        "pressure_1atm.csv": ("BR", "blue"),
        "pressure_5atm.csv": ("BR", "red"),
    }
    for filename, (panel, color) in mapping.items():
        frame = extract(masks[color], panel)
        frame.to_csv(OUT / filename, index=False)
        print(filename, len(frame))


if __name__ == "__main__":
    main()
