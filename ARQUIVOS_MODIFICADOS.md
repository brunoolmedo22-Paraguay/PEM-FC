# Alterações em relação ao ZIP recebido

## Removido da execução

- aba `Comparação`;
- funções `_vcell`, `XI1_REPRO`, `RMEM_REPRO` e `N_CELLS_REPRO` em `app.py`;
- classes/modos `literal`, `reprodução` e `revisado`;
- modelo paralelo em `calibration/flexible_model.py`;
- parâmetros padrão com `N_cells = 1`;
- cálculos de física dentro da interface;
- dependência da aplicação nos CSVs digitalizados.

## Reescrito

- `app.py`;
- `pemfc_config/parameters.py`;
- `models/pemfc_model.py`;
- `simulation/solver.py`;
- `visualization/plots.py`;
- testes e documentação.

## Adicionado

- quatro gráficos 2×2 gerados pelo modelo;
- exportação PNG, SVG e CSV;
- classificação de origem de cada parâmetro;
- validação interna independente da interface;
- testes contra regressão para impedir o retorno ao resultado de ~140 W.
