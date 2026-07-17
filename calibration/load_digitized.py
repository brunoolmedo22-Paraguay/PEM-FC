"""Carrega os CSVs digitalizados da Figura 3 em arrays numpy."""
import csv
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "otekon_figure3")

FILES = {
    ("panel1", 298.15): "panel1_labeled_activationloss_298K.csv",
    ("panel1", 373.15): "panel1_labeled_activationloss_373K.csv",
    ("panel2_power", 298.15): "panel2_power_298K.csv",
    ("panel2_power", 373.15): "panel2_power_373K.csv",
    ("panel3_efficiency", 298.15): "panel3_efficiency_298K.csv",
    ("panel3_efficiency", 373.15): "panel3_efficiency_373K.csv",
    ("panel4", 298.15): "panel4_labeled_activationloss_298K.csv",
    ("panel4", 373.15): "panel4_labeled_activationloss_373K.csv",
}


def load(key):
    path = os.path.join(DATA_DIR, FILES[key])
    xs, ys = [], []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            xs.append(float(row["current_density_A_cm2"]))
            ys.append(float(row["value"]))
    return np.array(xs), np.array(ys)


def load_all():
    return {k: load(k) for k in FILES}
