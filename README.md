# Modelo PEMFC — OTEKON 2024

Implementação em Python do modelo eletroquímico de Altıntaş e Ertan, com
engenharia reversa e identificação paramétrica das informações necessárias
para reconstruir os quatro resultados da Figura 3.

## Princípio arquitetural

```text
artigo + Figura 3
        ↓
digitalização e engenharia reversa
        ↓
identificação paramétrica reprodutível
        ↓
parâmetros centralizados
        ↓
    PEMFCModel
        ↓
resultados / sensibilidade / exportação
```

Existe apenas uma implementação matemática: `models/pemfc_model.py`. A
interface não possui modelo paralelo ou função especial para gerar os gráficos.

## Execução

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Reprodução da identificação paramétrica

```bash
python calibration/identify_parameters.py --starts 16
```

O script executa o procedimento completo com semente fixa, limites físicos e
múltiplos inícios. São gerados:

- `outputs/identified_parameters.csv`;
- `outputs/optimization_runs.csv`;
- `outputs/optimization_residuals.csv`;
- `outputs/parameter_correlation.csv`;
- `outputs/optimization_summary.json`;
- `outputs/optimization_report.md`.

A nova aba **Identificação paramétrica** da aplicação registra o motivo da
otimização, a função objetivo, os parâmetros, os limites, o fluxograma, os
resultados e os diagnósticos de identificabilidade.

## Validação e exportação

```bash
pytest -q
python calibration/validate_figure3.py
python calibration/export_outputs.py
```

## Decisões principais

- `N_cells = 41` — **INFERIDO** pela escala de potência, com valor contínuo
  equivalente de aproximadamente 41,70 células para `A = 232 cm²`;
- `A_active = 232 cm²` — **INFERIDO** do termo `0,035 × 232 F`;
- coeficientes efetivos de ativação, membrana e concentração — **INFERIDOS**
  pelas quatro curvas de tensão;
- `U_f = 0,696146` — **INFERIDO** posteriormente pelas curvas de eficiência;
- potência e eficiência não são usadas na otimização eletroquímica primária,
  evitando dupla contagem da informação contida na tensão.

Os dados digitalizados permanecem apenas em `data/` para identificação,
auditoria e validação. A aplicação gera suas curvas exclusivamente pelas
equações do `PEMFCModel`.

## Sobreposição com as curvas do artigo

Na aba **Resultados**, o controle **Sobrepor curvas digitalizadas do artigo**
adiciona aos quatro painéis as curvas extraídas da Figura 3 do OTEKON. As
linhas contínuas azul e vermelha representam o `PEMFCModel`; as linhas
tracejadas laranja e ciano representam os dados digitalizados. A sobreposição
é opcional e os CSVs não participam da geração das curvas do modelo.
