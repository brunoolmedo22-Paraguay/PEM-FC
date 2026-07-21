from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models.pemfc_model import PEMFCModel
from visualization.plots import figure3_matplotlib_bytes


def main() -> None:
    output = ROOT / "outputs"
    output.mkdir(exist_ok=True)
    model = PEMFCModel()
    data = model.figure3_data(points=241)
    frames = []
    for case, frame in data.items():
        copy = frame.copy()
        copy.insert(0, "case", case)
        frames.append(copy)
    pd.concat(frames, ignore_index=True).to_csv(output / "curves_model.csv", index=False)
    (output / "figure3_model.png").write_bytes(figure3_matplotlib_bytes(data, "png"))
    (output / "figure3_model.svg").write_bytes(figure3_matplotlib_bytes(data, "svg"))
    print("Arquivos exportados em", output)


if __name__ == "__main__":
    main()
