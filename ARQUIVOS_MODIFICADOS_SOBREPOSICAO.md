# Alterações — sobreposição das curvas do artigo

- `app.py`
  - adiciona o controle **Sobrepor curvas digitalizadas do artigo** na aba Resultados;
  - carrega os oito CSVs somente quando a sobreposição é ativada;
  - exporta PNG, SVG e CSV da comparação quando o controle está ativo.
- `visualization/plots.py`
  - aceita dados de referência opcionais;
  - mantém o modelo em linhas contínuas azul/vermelha;
  - apresenta o artigo em linhas tracejadas com marcadores laranja/ciano.
- `tests/test_model.py`
  - adiciona teste de geração da sobreposição e do SVG comparativo.
- `outputs/figure3_comparison.svg` e `.png`
  - exemplos exportados da nova visualização.

Validação executada:

- `12 passed` no pytest;
- aplicação executada por `streamlit.testing.v1.AppTest` sem exceções;
- controle ativado e gráfico comparativo renderizado sem erro.
