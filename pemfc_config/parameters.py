"""Parâmetros centralizados do modelo PEMFC reconstruído a partir do OTEKON 2024.

A aplicação possui um único conjunto de equações e uma única classe de modelo.
Cada parâmetro é classificado como ARTIGO, DERIVADO, INFERIDO,
CONSTANTE FÍSICA ou HIPÓTESE.
"""
from __future__ import annotations

from dataclasses import dataclass, replace, asdict
from typing import Any


@dataclass(frozen=True)
class PEMFCParameters:
    # Constantes e valores explicitamente publicados
    E0: float = 1.229                    # V
    R: float = 8.314                     # J/(mol.K)
    F: float = 96485.0                   # C/mol
    T_ref: float = 298.15                # K
    t_m: float = 0.005                   # cm
    D_H: float = 0.85e-6                 # cm²/s
    tau_H: float = 12.78                 # s
    C_dl_specific: float = 0.035         # F/cm²

    # Condições reconstruídas da Figura 3
    p_h2: float = 1.0                    # atm
    p_h2o: float = 0.50                  # atm
    oxygen_fraction_air: float = 0.21    # -
    pressure_temperature_K: float = 373.15

    # Geometria e stack
    A_active_cm2: float = 232.0
    N_cells: int = 41

    # Coeficientes efetivos de ativação.
    # A estrutura é a Eq. (4), mas os três primeiros coeficientes foram
    # identificados conjuntamente porque os valores impressos não reproduzem
    # a Figura 3 sob uma convenção dimensional coerente.
    xi1: float = -0.674591776167
    xi2: float = 0.00177858729827
    xi3: float = -7.38573038384e-05
    xi4: float = 1.19623548544e-05

    # Cadeia ôhmica Eq. (10)-(12), parametrizada pelo R_mem de referência.
    R_mem_ref_ohm_cm2: float = 0.225432192680
    R_mem_temperature_exponent: float = -0.776511316144

    # Eq. (13) reconstruída. A forma exponencial foi mantida; os coeficientes
    # efetivos foram inferidos porque a expressão impressa torna a(T) negativa
    # em 373,15 K e não reproduz a curvatura publicada.
    concentration_a_ref_V: float = 0.00658205964880
    concentration_a_temperature_V_K: float = 1.50924914732e-05
    concentration_b_cm2_A: float = 2.92419192535

    # A Figura 3 não informa a expressão da eficiência. Este fator equivale
    # a eta = 100 * U_f * V_cell / E0 e foi inferido das curvas publicadas.
    fuel_utilization: float = 0.696146096313

    # Regularização da correlação logarítmica no ponto I=0.
    current_density_floor_A_cm2: float = 0.010

    def copy_with(self, **kwargs: Any) -> "PEMFCParameters":
        return replace(self, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def C_dl_total_F(self) -> float:
        return self.C_dl_specific * self.A_active_cm2

    @property
    def sigma_ref_S_cm(self) -> float:
        return self.t_m / self.R_mem_ref_ohm_cm2

    @property
    def proton_concentration_ref_mol_cm3(self) -> float:
        """Concentração efetiva derivada de Eq. (10)-(12) em T_ref."""
        return (
            self.sigma_ref_S_cm * self.R * self.T_ref
            / (self.F**2 * self.D_H)
        )


DEFAULT_PARAMS = PEMFCParameters()

# Metadados para rastreabilidade e para a página de documentação.
PARAMETER_METADATA: dict[str, dict[str, str]] = {
    "E0": {"symbol": "E0", "unit": "V", "origin": "ARTIGO", "justification": "Tabela 1."},
    "R": {"symbol": "R", "unit": "J mol⁻¹ K⁻¹", "origin": "CONSTANTE FÍSICA", "justification": "Tabela 1 e constante universal."},
    "F": {"symbol": "F", "unit": "C mol⁻¹", "origin": "CONSTANTE FÍSICA", "justification": "Tabela 1 e constante de Faraday."},
    "t_m": {"symbol": "t_m", "unit": "cm", "origin": "ARTIGO", "justification": "Tabela 1."},
    "D_H": {"symbol": "D_H+", "unit": "cm² s⁻¹", "origin": "ARTIGO", "justification": "Tabela 1; unidade cm²/s é exigida dimensionalmente pela Eq. (12)."},
    "tau_H": {"symbol": "τ_H+", "unit": "s", "origin": "ARTIGO", "justification": "Tabela 1."},
    "C_dl_specific": {"symbol": "C_dl/A", "unit": "F cm⁻²", "origin": "DERIVADO", "justification": "Decomposição de 0,035 × 232 F da Tabela 1."},
    "p_h2": {"symbol": "p_H2", "unit": "atm", "origin": "INFERIDO", "justification": "Legenda do painel de pressão e hipótese de H2 puro."},
    "p_h2o": {"symbol": "p_H2O", "unit": "atm", "origin": "HIPÓTESE", "justification": "Não informado; valor de referência preservado porque seu efeito é correlacionado ao intercepto de ativação."},
    "oxygen_fraction_air": {"symbol": "y_O2", "unit": "-", "origin": "CONSTANTE FÍSICA", "justification": "Fração molar aproximada do oxigênio no ar seco."},
    "pressure_temperature_K": {"symbol": "T_p", "unit": "K", "origin": "INFERIDO", "justification": "O painel de 5 atm coincide com a curva de 373,15 K da Figura 3."},
    "A_active_cm2": {"symbol": "A", "unit": "cm²", "origin": "INFERIDO", "justification": "O fator 232 aparece no produto da capacitância de dupla camada."},
    "N_cells": {"symbol": "N", "unit": "células", "origin": "INFERIDO", "justification": "Consistência entre V_cell, A e potência do stack na Figura 3; valor inteiro mais provável: 41."},
    "xi1": {"symbol": "ξ1,ef", "unit": "V", "origin": "INFERIDO", "justification": "Identificação conjunta contra as duas curvas de temperatura e as duas de pressão."},
    "xi2": {"symbol": "ξ2,ef", "unit": "V K⁻¹", "origin": "INFERIDO", "justification": "Coeficiente efetivo; o valor impresso não fecha simultaneamente as curvas publicadas."},
    "xi3": {"symbol": "ξ3,ef", "unit": "V K⁻¹", "origin": "INFERIDO", "justification": "Coeficiente efetivo da dependência logarítmica da corrente."},
    "xi4": {"symbol": "ξ4,ef", "unit": "V K⁻¹", "origin": "INFERIDO", "justification": "O valor efetivo é exigido pela pequena separação entre as curvas de 1 e 5 atm; o coeficiente impresso gera diferença cerca de seis vezes maior."},
    "R_mem_ref_ohm_cm2": {"symbol": "R_mem,ref", "unit": "Ω cm²", "origin": "INFERIDO", "justification": "Inclinação ôhmica identificada na Figura 3 e usada dentro da cadeia Eq. (10)-(12)."},
    "R_mem_temperature_exponent": {"symbol": "n_R", "unit": "-", "origin": "INFERIDO", "justification": "Dependência térmica efetiva da hidratação/condutividade não explicitada no artigo."},
    "concentration_a_ref_V": {"symbol": "a_ref", "unit": "V", "origin": "INFERIDO", "justification": "Coeficiente efetivo da Eq. (13)."},
    "concentration_a_temperature_V_K": {"symbol": "a_T", "unit": "V K⁻¹", "origin": "INFERIDO", "justification": "Dependência térmica efetiva; evita o valor negativo gerado pela expressão impressa em 373,15 K."},
    "concentration_b_cm2_A": {"symbol": "b_eff", "unit": "cm² A⁻¹", "origin": "INFERIDO", "justification": "Interpretação de unidade compatível com a curvatura publicada."},
    "fuel_utilization": {"symbol": "U_f", "unit": "-", "origin": "INFERIDO", "justification": "A expressão de eficiência não é fornecida; inferido pela proporcionalidade η/V da Figura 3."},
}
