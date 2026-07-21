# Arquivos modificados e adicionados

## Modificados

- `app.py`
  - adicionada a aba **Identificação paramétrica**;
  - incluídos função objetivo, fluxograma, limites, resultados, robustez,
    correlações e downloads;
  - corrigida a classificação de `ξ4` para **INFERIDO**.
- `pemfc_config/parameters.py`
  - parâmetros padrão atualizados para os valores reproduzidos pelo script de
    identificação;
  - `U_f` uniformizado em `0,696146096313`.
- `README.md`
  - documentado o comando de reprodução da otimização.
- `RELATORIO_TECNICO.md`
  - incluído o procedimento completo de engenharia reversa e identificação.
- `calibration/__init__.py`
  - atualizada a descrição do pacote.

## Adicionados

- `calibration/identify_parameters.py`
  - identificação multistart por mínimos quadrados não lineares limitados;
  - inferência de `U_f`, produto `N×A` e diagnóstico de identificabilidade.
- `visualization/optimization.py`
  - fluxograma interativo para Streamlit e exportação estática.
- `TEXTO_METODOLOGIA_IDENTIFICACAO.tex`
  - texto acadêmico pronto para incorporação ao artigo.
- `tests/test_identification.py`
  - testes de rastreabilidade dos parâmetros e erro da identificação.
- `outputs/identified_parameters.csv`
- `outputs/optimization_runs.csv`
- `outputs/optimization_residuals.csv`
- `outputs/parameter_correlation.csv`
- `outputs/optimization_summary.json`
- `outputs/optimization_report.md`
- `outputs/optimization_flowchart.png`
- `outputs/optimization_flowchart.svg`
- `outputs/optimization_flowchart_article.png`
- `outputs/optimization_flowchart_article.svg`
