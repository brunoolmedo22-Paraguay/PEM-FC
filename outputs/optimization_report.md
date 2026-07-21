# Identificação paramétrica do modelo PEMFC

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
de digitalização de 0.003 V. O algoritmo utilizado é o
`scipy.optimize.least_squares`, método Trust Region Reflective, com limites físicos
e 16 inícios determinísticos (`seed=20260720`).

## Resultado

- RMSE conjunto das quatro curvas de tensão: **0.00141137 V**;
- inícios que convergiram a até 1% do melhor RMSE: **16/16**;
- número de condição local do Jacobiano escalado: **2185.9**;
- produto contínuo inferido N×A: **9674.60 cm²**;
- número contínuo equivalente para A=232 cm²: **41.70**;
- número inteiro adotado: **41 células**;
- fator de utilização inferido: **0.696146096**.

## Parâmetros finais

| Parâmetro | Valor |
|---|---:|
| xi1 | -0.674591776167 |
| xi2 | 0.00177858729827 |
| xi3 | -7.38573038384e-05 |
| xi4 | 1.19623548544e-05 |
| R_mem_ref_ohm_cm2 | 0.22543219268 |
| R_mem_temperature_exponent | -0.776511316144 |
| concentration_a_ref_V | 0.0065820596488 |
| concentration_a_temperature_V_K | 1.50924914732e-05 |
| concentration_b_cm2_A | 2.92419192535 |


## Interpretação

Os coeficientes finais não são apresentados como valores explicitamente fornecidos
pelos autores. Eles constituem a interpretação mais provável compatível com os
resultados publicados, obtida por um processo reprodutível de engenharia reversa
e otimização limitada.
