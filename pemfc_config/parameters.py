"""
pemfc_config/parameters.py
====================
Centralização de TODOS os parâmetros do modelo PEMFC.

Fonte única: Altıntaş, N.; Ertan, R. "Modeling of a PEM Fuel Cell System
in MATLAB", OTEKON 2024 (Bursa Uludağ University).

------------------------------------------------------------------
REGRA DE RASTREABILIDADE (obrigatória neste projeto)
------------------------------------------------------------------
Cada campo abaixo está marcado com uma tag de origem:

  [ARTIGO-EQ]   valor numérico ou coeficiente citado explicitamente no
                texto do artigo, junto à equação correspondente.
  [ARTIGO-TAB]  valor citado explicitamente na Tabela 1 do artigo.
  [GAP]         o artigo MENCIONA a grandeza mas NÃO fornece um valor
                numérico (ex: p_H2, p_O2, p_H2O, N). É necessário um
                valor para a simulação rodar; o valor abaixo é um
                PLACEHOLDER editável, não um dado do artigo.
  [PONTE]       grandeza que não existe como parâmetro livre no artigo,
                mas que é necessária para reconciliar duas equações do
                próprio artigo que usam convenções de unidade diferentes
                (ver nota "PONTE DE UNIDADES" abaixo). Documentado em
                detalhe em models/dynamics.py.

------------------------------------------------------------------
CONVENÇÃO DE UNIDADES CONFIRMADA NO TEXTO DO ARTIGO
------------------------------------------------------------------
O artigo declara explicitamente:
  - "Here I is the current density" (texto após Eq. 4-5).
  - Eq. 8 (R_act = V_act/I): unidade impressa = kΩ.cm²
  - Eq. 10 (R_mem = t_m/σ):  unidade impressa = kΩ.cm²
  - Eq. 13, coeficiente b:   unidade impressa = cm².mA⁻¹

Um R em kΩ.cm² só surge de V[volts]/I[mA/cm²] (Ohm's law): V/(mA/cm²) =
1000 Ω.cm² = 1 kΩ.cm². Da mesma forma, b em cm²/mA só faz sentido se I
em V_conc=a·exp(b·I) estiver em mA/cm². Logo: TODA densidade de corrente
I nas Eq. 4, 6, 8, 9, 10, 11 e 13 está em mA/cm² -- não em A/cm².

Esta é uma correção em relação a uma versão anterior deste projeto, que
usava A/cm² nos blocos ôhmico e de hidratação por engano (ver auditoria
técnica anterior a esta versão).

PONTE DE UNIDADES (Eq. 7, dinâmica de dupla camada):
  A Tabela 1 dá C_dl = "0.035 x 232 F", ou seja, um valor TOTAL (8.12 F,
  não F/cm²) para a célula específica do artigo (232 cm²). Mas o texto
  diz que I é densidade de corrente. dV/dt = I/C_dl só é dimensionalmente
  V/s se I e C_dl estiverem ambos "totais" (A e F) ou ambos "específicos"
  (A/cm² e F/cm²) -- misturar densidade com capacitância total não fecha
  dimensionalmente. O artigo NÃO explicita essa conversão. Implementamos
  a ponte mínima necessária (densidade x área = corrente total; R_act
  específico / área = R_act total) em models/dynamics.py, documentada
  linha por linha. Isso é uma INTERPRETAÇÃO, não um dado do artigo.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from typing import Dict, Any


# ==================================================================
# 1. CONSTANTES FÍSICAS UNIVERSAIS  [ARTIGO-TAB]
# ==================================================================
@dataclass(frozen=True)
class PhysicalConstants:
    """Constantes universais. Tabela 1 do artigo (E0, R, F) + padrão físico."""

    R: float = 8.314        # [ARTIGO-TAB] Constante universal dos gases [J/(mol.K)]
    F: float = 96485.0      # [ARTIGO-TAB] Constante de Faraday          [C/mol]
    T_ref: float = 298.15   # [ARTIGO-EQ]  Referência da Eq. 3 (298.15 K)
    n_electrons: int = 2    # Padrão eletroquímico (H2 -> 2H+ + 2e-), não é
                             # um parâmetro explicitamente tabelado no artigo,
                             # mas decorre diretamente da Eq. 1 (2H2+O2->2H2O)


CONSTANTS = PhysicalConstants()


# ==================================================================
# 2. PARÂMETROS DO MODELO — Eq. 1 a 14 do artigo
# ==================================================================
@dataclass
class PEMFCParameters:
    """
    Parâmetros do modelo PEMFC. Os defaults reproduzem literalmente a
    Tabela 1 e os coeficientes citados no texto das Eq. 4 e 13 do artigo.
    Campos marcados [GAP] não têm valor no artigo e precisam ser
    fornecidos pelo usuário -- eles vêm com um placeholder, nunca com um
    valor apresentado como "do artigo".
    """

    name: str = "OTEKON 2024 — Reprodução do artigo"

    # --- Eq. 3 (Nernst) ---------------------------------------------------
    E0: float = 1.229          # [ARTIGO-TAB] Tabela 1                    [V]
    T: float = 353.0           # [ARTIGO-TAB] Tabela 1 ("Bulk temperature") [K]
    P: float = 1.2             # [ARTIGO-TAB] Tabela 1 ("Cell pressure")  [atm]

    # [GAP] O texto diz "Related parameters are given in Table 1", mas a
    # Tabela 1 NÃO lista p_H2, p_O2 nem p_H2O -- apenas a pressão total P.
    # Isto é uma lacuna do próprio artigo, não desta implementação.
    # Placeholders fisicamente plausíveis (ar atmosférico, H2 puro,
    # umidificação parcial), editáveis, claramente sinalizados na UI:
    p_h2: float = 1.0          # [GAP] presión parcial de H2 no ânodo    [atm]
    p_o2: float = 0.21         # [GAP] presión parcial de O2 no cátodo  [atm]
    p_h2o: float = 0.50        # [GAP] presión de vapor de água         [atm]

    # --- Eq. 5 (concentração de O2, lei de Henry) --------------------------
    # Coeficientes citados explicitamente na Eq. 5 do artigo.
    k_henry: float = 5.08e6    # [ARTIGO-EQ] prefator                [atm.cm^3/mol]
    e_henry: float = 498.0     # [ARTIGO-EQ] energia característica          [K]

    # --- Eq. 4 (ativação, Tafel semi-empírico) -----------------------------
    # Coeficientes citados EXATAMENTE no texto, junto à Eq. 4.
    # I em mA/cm² (ver nota de unidades no cabeçalho do módulo).
    xi1: float = -0.9514       # [ARTIGO-EQ]                              [V]
    xi2: float = 0.00312       # [ARTIGO-EQ]                            [V/K]
    xi3: float = -0.000187     # [ARTIGO-EQ] multiplica T*ln(I_mA)  [V/(K.ln)]
    xi4: float = 7.4e-5        # [ARTIGO-EQ] multiplica T*ln(C_O2)  [V/(K.ln)]

    # --- Eq. 10 / Tabela 1 (membrana) ---------------------------------------
    t_m: float = 0.005         # [ARTIGO-TAB]                             [cm]
    D_H: float = 0.85e-6       # [ARTIGO-TAB]                          [cm^2/s]
    tau_H: float = 12.78       # [ARTIGO-TAB]                              [s]

    # --- Eq. 11 (hidratação protônica) --------------------------------------
    # dCH+/dt + CH+/tauH+ = (1 + alphaH+ * I_mA^3) / tauH+
    # O "1" é LITERAL no artigo -- não há um "C_H_ref" nomeado no texto.
    # Dimensionalmente, porém, a Eq. 12 (sigma = F^2 D C /(RT)) só resulta
    # em S/cm se C for uma concentração molar -- então esse "1" só faz
    # sentido físico como "1 mol/cm^3" (ver nota completa em models/ohmic.py).
    # Mantido como constante FIXA (não editável), pois é literal no artigo.
    CH_BASE: float = 1.0       # [ARTIGO-EQ, literal] termo "1" da Eq. 11

    # [GAP] alpha_H+ NÃO aparece em lugar nenhum do artigo (nem no texto,
    # nem na Tabela 1). É a única incógnita realmente livre do bloco de
    # hidratação. Placeholder pequeno o suficiente para não dominar o
    # termo "1" em correntes moderadas (ver docstring de models/ohmic.py
    # para a escala correta agora que I está em mA/cm^2).
    alpha_H: float = 1.5e-12   # [GAP]                          [(cm^2/mA)^3]

    # --- Eq. 13 (concentração) ----------------------------------------------
    # Coeficientes citados EXATAMENTE no texto, após a Eq. 13.
    a_1: float = 1.1e-4        # [ARTIGO-EQ]                               [V]
    a_2: float = 1.2e-6        # [ARTIGO-EQ]                             [V/K]
    T_conc_ref: float = 273.0  # [ARTIGO-EQ] "(T - 273)"                     [K]
    b_conc: float = 8.0e-3     # [ARTIGO-EQ]                     [cm^2/mA]

    # --- Eq. 7 / Tabela 1 (dupla camada) -------------------------------------
    # Tabela 1: "Cdl = 0.035 x 232 F" -- um valor TOTAL para a célula
    # específica do artigo (232 cm^2). Guardamos aqui a forma específica
    # (0.035 F/cm^2) e a área (232 cm^2) separadamente, reconstruindo o
    # total via C_dl_total = C_dl_specific * A_active (bate exatamente com
    # 8.12 F quando A_active=232, e generaliza corretamente se o usuário
    # mudar a área).
    C_dl_specific: float = 0.035   # [ARTIGO-TAB] (extraído do produto)  [F/cm^2]

    # --- Eq. 14 (stack) + área ativa -----------------------------------------
    # 232 cm^2 aparece no artigo APENAS dentro do produto "0.035 x 232" da
    # Tabela 1 (capacitância). O artigo nunca rotula esse número
    # explicitamente como "área ativa" -- essa é uma INFERÊNCIA (ainda que
    # bem apoiada: é o único jeito de o produto "0.035 x 232 F" fazer
    # sentido dimensional, já que 0.035 F/cm^2 é uma capacitância de dupla
    # camada específica plausível).
    A_active: float = 232.0    # [INFERIDO da Tabela 1]                 [cm^2]

    # [GAP] O artigo dá Eq. 14 (V_stack = V_cell x N) de forma genérica,
    # sem especificar N para o caso estudado. N=1 é o default neutro
    # (V_stack = V_cell), não uma afirmação sobre o artigo.
    N_cells: int = 1           # [GAP]                                     [-]

    # --- Numérico -------------------------------------------------------------
    # NÃO é um parâmetro do artigo. Piso de corrente para evitar ln(0) na
    # Eq. 4/13 quando I->0. Ver nota de regularização em models/activation.py.
    i_min_mA: float = 1.0e-3   # [REGULARIZAÇÃO NUMÉRICA]              [mA/cm^2]

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def copy_with(self, **kwargs) -> "PEMFCParameters":
        return replace(self, **kwargs)

    @property
    def C_dl_total(self) -> float:
        """C_dl total [F] = C_dl_specific [F/cm^2] * A_active [cm^2].
        Em A_active=232 cm^2 (default), isto reproduz EXATAMENTE o
        "0.035 x 232 = 8.12 F" da Tabela 1."""
        return self.C_dl_specific * self.A_active

    def current_to_density_mA(self, current_A: float) -> float:
        """Corrente total [A] -> densidade de corrente [mA/cm^2]."""
        return 1000.0 * current_A / self.A_active

    def density_mA_to_current(self, i_mA: float) -> float:
        """Densidade de corrente [mA/cm^2] -> corrente total [A]."""
        return i_mA / 1000.0 * self.A_active


# Instância default = reprodução literal do artigo (com GAPs sinalizados)
DEFAULT_PARAMS = PEMFCParameters()


# ==================================================================
# 3. QUAIS CAMPOS SÃO "GAP" (não vêm do artigo) — usado pela UI
#    para exibir o selo "não especificado pelo artigo" automaticamente,
#    sem depender de manter duas listas sincronizadas manualmente.
# ==================================================================
GAP_FIELDS = {
    "p_h2": "O artigo cita p_H2 na Eq. 3 e diz 'Related parameters are given "
            "in Table 1', mas a Tabela 1 não lista p_H2. Valor abaixo é um "
            "placeholder (H2 puro no ânodo), não um dado do artigo.",
    "p_o2": "Mesma lacuna: a Tabela 1 não lista p_O2. Placeholder = fração "
            "molar de O2 no ar atmosférico seco (0.21 atm a 1 atm total).",
    "p_h2o": "Mesma lacuna: a Tabela 1 não lista p_H2O. Placeholder "
             "arbitrário (0.50 atm), sem base no artigo.",
    "alpha_H": "Não aparece em nenhum lugar do artigo (nem texto, nem "
               "Tabela 1). É a única incógnita livre da Eq. 11. Placeholder "
               "pequeno para não dominar o termo '1' em corrente moderada.",
    "N_cells": "A Eq. 14 (V_stack = V_cell x N) é genérica; o artigo não "
               "informa N para o caso estudado. Default = 1 (V_stack=V_cell).",
    "A_active": "232 cm² aparece apenas dentro do produto '0.035 x 232 F' da "
                "Tabela 1 (capacitância). O artigo nunca o rotula "
                "explicitamente como área ativa -- é uma inferência.",
}


# ==================================================================
# 4. BIBLIOTECA DE PARÂMETROS
# ==================================================================
# Um único preset fiel ao artigo. Presets anteriores rotulados "OTEKON —
# O2 puro" / "OTEKON — Stack 50 células" / "Membrana calibrada" foram
# REMOVIDOS nesta versão: eram exemplos didáticos inventados e rotulados
# de forma enganosa como se fossem variações do artigo. Ver auditoria.
PARAMETER_LIBRARY: Dict[str, PEMFCParameters] = {
    "OTEKON 2024 — Reprodução do artigo": DEFAULT_PARAMS,
}
