# Modelo PEMFC - OTEKON 2024

Implementação em Python do modelo eletroquímico de Altıntaş e Ertan,
com reconstrução das condições não explicitadas necessárias para gerar os
quatro resultados da Figura 3.

## Princípio arquitetural

```text
parâmetros centralizados
        ↓
    PEMFCModel
        ↓
simulação / resultados / sensibilidade / exportação
```

Existe apenas uma implementação matemática: `models/pemfc_model.py`.
A interface não possui aba de comparação, modelo literal, modelo revisado
nem funções eletroquímicas paralelas.

## Execução

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Testes

```bash
pytest -q
python calibration/validate_figure3.py
python calibration/export_outputs.py
```

## Parâmetros-chave

- `N_cells = 41` - **INFERIDO** pela consistência entre tensão, área e potência.
- `A_active = 232 cm²` - **INFERIDO** do produto `0,035 × 232 F` da Tabela 1.
- Coeficientes efetivos de ativação, resistência de membrana e concentração -
  **INFERIDOS** por identificação conjunta das quatro curvas.
- Eficiência - expressão ausente no artigo; fator de utilização inferido da
  proporcionalidade entre eficiência e tensão.

Os dados digitalizados permanecem apenas em `data/` para auditoria e testes.
A aplicação funciona sem essa pasta e nunca interpola pontos da figura para
produzir seus resultados.
