"""Identificação paramétrica reprodutível do modelo PEMFC.

Este script reconstrói os parâmetros eletroquímicos ausentes ou incompatíveis
com a Figura 3 de Altıntaş e Ertan (OTEKON 2024). A identificação primária usa
somente as quatro curvas de tensão, evitando contar potência e eficiência como
observações independentes da mesma tensão.

Execução recomendada:
    python calibration/identify_parameters.py --starts 16

Saídas:
    outputs/identified_parameters.csv
    outputs/optimization_runs.csv
    outputs/optimization_residuals.csv
    outputs/parameter_correlation.csv
    outputs/optimization_summary.json
    outputs/optimization_report.md
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
import sys
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models.pemfc_model import PEMFCModel
from pemfc_config import DEFAULT_PARAMS, PEMFCParameters

DATA_DIR = ROOT / "data" / "otekon_figure3"
OUTPUT_DIR = ROOT / "outputs"
SIGMA_DIGITIZATION_V = 0.003
RANDOM_SEED = 20260720


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    symbol: str
    initial: float
    lower: float
    upper: float
    scale: float
    rationale: str


# O vetor inicial combina os coeficientes publicados com inferências obtidas
# pela leitura física das três regiões da curva de polarização.
PARAMETER_SPECS: tuple[ParameterSpec, ...] = (
    ParameterSpec("xi1", "ξ1", -0.9514, -1.5, -0.2, 0.5, "Valor inicial publicado na Eq. (4)."),
    ParameterSpec("xi2", "ξ2", 0.00312, 0.0, 0.005, 0.002, "Valor inicial publicado na Eq. (4)."),
    ParameterSpec("xi3", "ξ3", -0.000187, -3e-4, 0.0, 1e-4, "Valor inicial publicado na Eq. (4)."),
    ParameterSpec("xi4", "ξ4", 7.4e-5, 0.0, 1e-4, 5e-5, "Valor inicial publicado na Eq. (4)."),
    ParameterSpec("R_mem_ref_ohm_cm2", "Rmem,ref", 0.20, 0.05, 0.50, 0.20, "Estimativa da inclinação da região aproximadamente ôhmica."),
    ParameterSpec("R_mem_temperature_exponent", "nR", 0.0, -2.0, 2.0, 1.0, "Dependência térmica não explicitada da condutividade da membrana."),
    ParameterSpec("concentration_a_ref_V", "aref", 7.982e-5, 0.0, 0.03, 0.01, "Eq. (13) avaliada em 298,15 K como ponto de partida."),
    ParameterSpec("concentration_a_temperature_V_K", "aT", -1.2e-6, -5e-5, 5e-5, 2e-5, "Coeficiente térmico publicado para a Eq. (13)."),
    ParameterSpec("concentration_b_cm2_A", "b", 8.0, 0.1, 8.0, 3.0, "Conversão de 8×10⁻³ cm²/mA para cm²/A."),
)

VOLTAGE_CASES: tuple[tuple[str, str, float, float], ...] = (
    ("tensao_298K", "voltage_298K.csv", 298.15, 5.0),
    ("tensao_373K", "voltage_373K.csv", 373.15, 5.0),
    ("pressao_1atm", "pressure_1atm.csv", 373.15, 1.0),
    ("pressao_5atm", "pressure_5atm.csv", 373.15, 5.0),
)


@dataclass(frozen=True)
class VoltageCase:
    label: str
    current_density_A_cm2: np.ndarray
    target_voltage_V: np.ndarray
    temperature_K: float
    air_pressure_atm: float


def parameter_specification_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Parâmetro": spec.name,
                "Símbolo": spec.symbol,
                "Valor inicial": spec.initial,
                "Limite inferior": spec.lower,
                "Limite superior": spec.upper,
                "Motivo do valor inicial": spec.rationale,
            }
            for spec in PARAMETER_SPECS
        ]
    )


def load_voltage_cases(data_dir: Path = DATA_DIR) -> list[VoltageCase]:
    cases: list[VoltageCase] = []
    for label, filename, temperature, pressure in VOLTAGE_CASES:
        frame = pd.read_csv(data_dir / filename)
        cases.append(
            VoltageCase(
                label=label,
                current_density_A_cm2=frame["current_density_A_cm2"].to_numpy(dtype=float),
                target_voltage_V=frame["value"].to_numpy(dtype=float),
                temperature_K=temperature,
                air_pressure_atm=pressure,
            )
        )
    return cases


def vector_to_params(vector: np.ndarray, base: PEMFCParameters = DEFAULT_PARAMS) -> PEMFCParameters:
    values = {spec.name: float(value) for spec, value in zip(PARAMETER_SPECS, vector)}
    return replace(base, **values)


def voltage_residuals(
    vector: np.ndarray,
    cases: Iterable[VoltageCase],
    sigma_V: float = SIGMA_DIGITIZATION_V,
) -> np.ndarray:
    model = PEMFCModel(vector_to_params(vector))
    residual_parts: list[np.ndarray] = []
    for case in cases:
        estimate = model.cell_voltage(
            case.current_density_A_cm2,
            case.temperature_K,
            case.air_pressure_atm,
        )
        residual_parts.append((estimate - case.target_voltage_V) / sigma_V)
    return np.concatenate(residual_parts)


def build_start_vectors(number_of_starts: int, seed: int = RANDOM_SEED) -> list[np.ndarray]:
    """Gera um início publicado e inícios perturbados deterministicamente.

    O primeiro vetor sempre preserva os valores publicados/engenheirados.
    Os demais exploram os limites para reduzir dependência do chute inicial.
    """
    if number_of_starts < 1:
        raise ValueError("number_of_starts deve ser pelo menos 1")

    initial = np.array([spec.initial for spec in PARAMETER_SPECS], dtype=float)
    lower = np.array([spec.lower for spec in PARAMETER_SPECS], dtype=float)
    upper = np.array([spec.upper for spec in PARAMETER_SPECS], dtype=float)
    starts = [initial]
    rng = np.random.default_rng(seed)
    for _ in range(number_of_starts - 1):
        # Mistura um ponto global dentro dos limites com o vetor baseado no artigo.
        global_sample = rng.uniform(lower, upper)
        weight = rng.uniform(0.25, 0.75)
        candidate = weight * initial + (1.0 - weight) * global_sample
        starts.append(np.clip(candidate, lower + 1e-12, upper - 1e-12))
    return starts


def fit_voltage_parameters(
    number_of_starts: int = 16,
    seed: int = RANDOM_SEED,
    max_nfev: int = 10000,
) -> tuple[np.ndarray, pd.DataFrame, object, list[VoltageCase]]:
    """Executa mínimos quadrados não lineares com múltiplos inícios."""
    cases = load_voltage_cases()
    lower = np.array([spec.lower for spec in PARAMETER_SPECS], dtype=float)
    upper = np.array([spec.upper for spec in PARAMETER_SPECS], dtype=float)
    scales = np.array([spec.scale for spec in PARAMETER_SPECS], dtype=float)

    runs: list[dict[str, float | int | bool]] = []
    fitted_results = []
    for start_id, start in enumerate(build_start_vectors(number_of_starts, seed)):
        result = least_squares(
            voltage_residuals,
            start,
            args=(cases, SIGMA_DIGITIZATION_V),
            bounds=(lower, upper),
            method="trf",
            jac="3-point",
            x_scale=scales,
            loss="linear",
            max_nfev=max_nfev,
            ftol=1e-12,
            xtol=1e-12,
            gtol=1e-12,
        )
        residual_V = voltage_residuals(result.x, cases, 1.0)
        rmse_V = float(np.sqrt(np.mean(residual_V**2)))
        runs.append(
            {
                "start_id": start_id,
                "success": bool(result.success),
                "cost": float(result.cost),
                "rmse_voltage_V": rmse_V,
                "nfev": int(result.nfev),
                "optimality": float(result.optimality),
            }
        )
        fitted_results.append(result)

    best_index = int(np.argmin([row["rmse_voltage_V"] for row in runs]))
    return fitted_results[best_index].x, pd.DataFrame(runs), fitted_results[best_index], cases


def infer_fuel_utilization(params: PEMFCParameters) -> float:
    """Infere U_f por mínimos quadrados escalares nas duas curvas de eficiência."""
    model = PEMFCModel(params)
    numerator = 0.0
    denominator = 0.0
    for filename, temperature in (("efficiency_298K.csv", 298.15), ("efficiency_373K.csv", 373.15)):
        frame = pd.read_csv(DATA_DIR / filename)
        voltage = model.cell_voltage(frame.current_density_A_cm2.to_numpy(), temperature, 5.0)
        predictor = 100.0 * voltage / params.E0
        target = frame.value.to_numpy(dtype=float)
        numerator += float(np.dot(predictor, target))
        denominator += float(np.dot(predictor, predictor))
    return numerator / denominator


def infer_stack_product(params: PEMFCParameters) -> dict[str, float]:
    """Infere o produto contínuo N×A a partir das curvas de potência.

    A escolha final de N mantém a restrição inteira e A=232 cm². O produto
    contínuo é informado para expor a pequena inconsistência interna da figura.
    """
    model = PEMFCModel(params)
    numerator = 0.0
    denominator = 0.0
    for filename, temperature in (("power_298K.csv", 298.15), ("power_373K.csv", 373.15)):
        frame = pd.read_csv(DATA_DIR / filename)
        j = frame.current_density_A_cm2.to_numpy(dtype=float)
        voltage = model.cell_voltage(j, temperature, 5.0)
        predictor = j * voltage
        target = frame.value.to_numpy(dtype=float)
        numerator += float(np.dot(predictor, target))
        denominator += float(np.dot(predictor, predictor))
    effective_NA = numerator / denominator
    effective_cells = effective_NA / params.A_active_cm2
    return {
        "effective_N_times_A_cm2": effective_NA,
        "effective_number_of_cells": effective_cells,
        "adopted_integer_cells": float(params.N_cells),
        "adopted_area_cm2": params.A_active_cm2,
    }


def identifiability(result, scales: np.ndarray) -> tuple[float, pd.DataFrame]:
    """Calcula número de condição e correlação local dos parâmetros."""
    scaled_jacobian = result.jac @ np.diag(scales)
    singular_values = np.linalg.svd(scaled_jacobian, compute_uv=False)
    condition_number = float(singular_values[0] / singular_values[-1])
    covariance = np.linalg.pinv(scaled_jacobian.T @ scaled_jacobian)
    std = np.sqrt(np.maximum(np.diag(covariance), 1e-30))
    correlation = covariance / np.outer(std, std)
    labels = [spec.name for spec in PARAMETER_SPECS]
    return condition_number, pd.DataFrame(correlation, index=labels, columns=labels)


def residual_table(params: PEMFCParameters, cases: list[VoltageCase]) -> pd.DataFrame:
    model = PEMFCModel(params)
    rows: list[dict[str, float | str]] = []
    for case in cases:
        estimate = model.cell_voltage(
            case.current_density_A_cm2,
            case.temperature_K,
            case.air_pressure_atm,
        )
        for j, target, calculated in zip(
            case.current_density_A_cm2,
            case.target_voltage_V,
            estimate,
        ):
            rows.append(
                {
                    "case": case.label,
                    "current_density_A_cm2": float(j),
                    "target_voltage_V": float(target),
                    "model_voltage_V": float(calculated),
                    "residual_V": float(calculated - target),
                }
            )
    return pd.DataFrame(rows)


def write_report(
    params: PEMFCParameters,
    runs: pd.DataFrame,
    condition_number: float,
    stack_inference: dict[str, float],
    output_path: Path,
) -> None:
    best_rmse = float(runs.rmse_voltage_V.min())
    converged = int((runs.rmse_voltage_V <= best_rmse * 1.01).sum())
    report = f"""# Identificação paramétrica do modelo PEMFC

## Motivo

A aplicação direta dos coeficientes impressos no artigo não reproduz os níveis,
a inclinação e a curvatura da Figura 3. Além disso, número de células, área ativa,
expressão de eficiência e algumas convenções dimensionais não são informados de
forma inequívoca. Por isso, foi realizada identificação paramétrica mantendo a
estrutura eletroquímica publicada.

## Dados utilizados no ajuste primário

Foram usadas somente quatro curvas de tensão: 298,15 K, 373,15 K, 1 atm e 5 atm.
Potência e eficiência não entraram na função objetivo primária, pois ambas são
derivadas da tensão e causariam dupla contagem da mesma informação.

## Função objetivo

A função minimizada é a soma dos resíduos de tensão normalizados pela incerteza
de digitalização de {SIGMA_DIGITIZATION_V:.3f} V. O algoritmo utilizado é o
`scipy.optimize.least_squares`, método Trust Region Reflective, com limites físicos
e {len(runs)} inícios determinísticos (`seed={RANDOM_SEED}`).

## Resultado

- RMSE conjunto das quatro curvas de tensão: **{best_rmse:.8f} V**;
- inícios que convergiram a até 1% do melhor RMSE: **{converged}/{len(runs)}**;
- número de condição local do Jacobiano escalado: **{condition_number:.1f}**;
- produto contínuo inferido N×A: **{stack_inference['effective_N_times_A_cm2']:.2f} cm²**;
- número contínuo equivalente para A=232 cm²: **{stack_inference['effective_number_of_cells']:.2f}**;
- número inteiro adotado: **{params.N_cells} células**;
- fator de utilização inferido: **{params.fuel_utilization:.9f}**.

## Parâmetros finais

| Parâmetro | Valor |
|---|---:|
"""
    for spec in PARAMETER_SPECS:
        report += f"| {spec.name} | {getattr(params, spec.name):.12g} |\n"
    report += """

## Interpretação

Os coeficientes finais não são apresentados como valores explicitamente fornecidos
pelos autores. Eles constituem a interpretação mais provável compatível com os
resultados publicados, obtida por um processo reprodutível de engenharia reversa
e otimização limitada.
"""
    output_path.write_text(report, encoding="utf-8")


def run_identification(number_of_starts: int = 16, seed: int = RANDOM_SEED) -> PEMFCParameters:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    vector, runs, result, cases = fit_voltage_parameters(number_of_starts, seed)
    voltage_params = vector_to_params(vector)
    fuel_utilization = infer_fuel_utilization(voltage_params)
    final_params = replace(voltage_params, fuel_utilization=fuel_utilization)
    stack_inference = infer_stack_product(final_params)

    scales = np.array([spec.scale for spec in PARAMETER_SPECS], dtype=float)
    condition_number, correlation = identifiability(result, scales)
    residuals = residual_table(final_params, cases)

    parameter_rows = []
    for spec, value in zip(PARAMETER_SPECS, vector):
        parameter_rows.append(
            {
                "parameter": spec.name,
                "symbol": spec.symbol,
                "initial_value": spec.initial,
                "identified_value": float(value),
                "lower_bound": spec.lower,
                "upper_bound": spec.upper,
                "initial_rationale": spec.rationale,
            }
        )
    parameter_rows.extend(
        [
            {
                "parameter": "fuel_utilization",
                "symbol": "U_f",
                "initial_value": np.nan,
                "identified_value": fuel_utilization,
                "lower_bound": 0.0,
                "upper_bound": 1.0,
                "initial_rationale": "Inferência escalar posterior a partir das curvas de eficiência.",
            },
            {
                "parameter": "N_cells",
                "symbol": "N",
                "initial_value": np.nan,
                "identified_value": final_params.N_cells,
                "lower_bound": 1,
                "upper_bound": 500,
                "initial_rationale": "Restrição inteira aplicada à escala de potência com A=232 cm².",
            },
        ]
    )

    pd.DataFrame(parameter_rows).to_csv(OUTPUT_DIR / "identified_parameters.csv", index=False)
    runs.to_csv(OUTPUT_DIR / "optimization_runs.csv", index=False)
    residuals.to_csv(OUTPUT_DIR / "optimization_residuals.csv", index=False)
    correlation.to_csv(OUTPUT_DIR / "parameter_correlation.csv")

    best_rmse = float(runs.rmse_voltage_V.min())
    summary = {
        "algorithm": "bounded multistart nonlinear least squares (TRF)",
        "number_of_starts": number_of_starts,
        "random_seed": seed,
        "digitization_sigma_V": SIGMA_DIGITIZATION_V,
        "voltage_rmse_V": best_rmse,
        "jacobian_condition_number_scaled": condition_number,
        "fuel_utilization": fuel_utilization,
        **stack_inference,
    }
    (OUTPUT_DIR / "optimization_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_report(
        final_params,
        runs,
        condition_number,
        stack_inference,
        OUTPUT_DIR / "optimization_report.md",
    )
    return final_params


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts", type=int, default=16, help="Número de inícios da otimização.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Semente determinística.")
    args = parser.parse_args()

    params = run_identification(args.starts, args.seed)
    print("Identificação concluída.")
    print(f"N_cells = {params.N_cells}")
    print(f"fuel_utilization = {params.fuel_utilization:.10f}")
    for spec in PARAMETER_SPECS:
        print(f"{spec.name} = {getattr(params, spec.name):.12g}")


if __name__ == "__main__":
    main()
