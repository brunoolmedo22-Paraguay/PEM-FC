# Relatório técnico - reconstrução do modelo PEMFC do OTEKON 2024

## 1. Resultado arquitetural

O projeto foi reconstruído ao redor de uma única classe `PEMFCModel`.
A antiga separação entre implementação principal e função especial de
comparação foi eliminada. A interface, os quatro gráficos, a sensibilidade,
as exportações e os testes chamam exatamente a mesma classe.

## 2. Equações implementadas

A tensão é calculada por

`V_cell = E - V_act - V_ohm - V_conc`.

O potencial reversível segue a Eq. (3), a ativação mantém a estrutura da
Eq. (4), o bloco ôhmico é fechado pelas Eq. (10)-(12) e a perda de
concentração mantém a forma exponencial da Eq. (13). Potência e tensão do
stack seguem `V_stack = N V_cell` e `P_stack = V_stack j A`.

## 3. Inferências necessárias

### Número de células

O artigo não fornece `N`. A Figura 3 mostra aproximadamente 5,3 kW para
`j ≈ 1 A/cm²`, `V_cell ≈ 0,55-0,57 V` e área próxima de 232 cm². A relação
`N = P/(V_cell j A)` resulta em aproximadamente 40-41 células. Foi adotado
`N = 41`, valor inteiro mais provável, classificado como **INFERIDO**.

### Área ativa

O número 232 aparece na Tabela 1 apenas em `C_dl = 0,035 × 232 F`. A leitura
dimensional mais consistente é 0,035 F/cm² multiplicado por uma área de
232 cm². A área foi classificada como **INFERIDA**, não como explicitamente
informada.

### Coeficientes eletroquímicos efetivos

A substituição direta dos coeficientes impressos não reproduz as curvas.
Em especial:

- a cadeia de hidratação, com o termo `1` da Eq. (11) interpretado como
  concentração dimensional, gera resistência ôhmica várias ordens abaixo da
  necessária;
- a expressão impressa de `a(T)` na Eq. (13) fica negativa em 373,15 K;
- a convenção de corrente indicada pela unidade de `b` produz uma queda de
  concentração excessiva em alta corrente;
- os coeficientes de ativação impressos não fecham simultaneamente nível,
  inclinação e diferença térmica da Figura 3.

Por isso, foram identificados coeficientes efetivos, preservando a estrutura
física das equações. Eles representam a **interpretação mais provável
compatível com os resultados publicados** e estão explicitamente marcados
como **INFERIDOS**.

### Eficiência

O artigo não fornece a equação usada no painel de eficiência. A digitalização
mostra uma relação praticamente constante `eta[%]/V_cell ≈ 56,6`. A
implementação utiliza `eta = 100 U_f V_cell/E0`, com `U_f = 0,69048` inferido.

### Temperatura do painel de pressão

O painel não informa a temperatura. A curva de 5 atm coincide com a curva de
373,15 K do painel superior, portanto foi adotado `T = 373,15 K`, classificado
como **INFERIDO**.

## 4. Inconsistência interna da Figura 3

As curvas de potência não são perfeitamente consistentes, ponto a ponto, com
as curvas de tensão para um único produto `N × A`. A diferença é pequena na
escala do gráfico, mas impede coincidência matemática absoluta de tensão e
potência simultaneamente. A implementação preserva a relação física
`P = N V_cell j A`, usa `N = 41` e `A = 232 cm²`, e mantém a discrepância
residual documentada em vez de aplicar um fator de potência oculto.

## 5. Uso dos dados digitalizados

Os CSVs são usados somente por `calibration/validate_figure3.py`. A aplicação
não importa a pasta `data/`, não usa spline, regressão polinomial, tabela de
consulta ou interpolação dos pontos publicados. Todas as curvas apresentadas
nascem das equações da classe `PEMFCModel`.

## 6. Limitações

A reconstrução é uma reprodução computacional de resultados gráficos, não
uma validação experimental. A solução paramétrica não é estritamente única,
pois intercepto de ativação, pressões parciais e resistência efetiva apresentam
correlação. O conjunto adotado prioriza um único modelo, baixo erro visual,
plausibilidade física e rastreabilidade das inferências.

## 7. Métricas da reconstrução

A validação foi realizada contra uma nova digitalização da imagem original,
com o eixo de corrente limitado corretamente a 1,0 A/cm². Os resultados
estão em `outputs/validation_metrics.csv`.

| Curva | RMSE | Erro máximo | Erro relativo médio |
|---|---:|---:|---:|
| Tensão, 298,15 K | 0,0020 V | 0,0119 V | 0,155% |
| Tensão, 373,15 K | 0,0013 V | 0,0062 V | 0,100% |
| Potência, 298,15 K | 135,3 W | 201,0 W | 3,250% |
| Potência, 373,15 K | 34,4 W | 59,5 W | 1,930% |
| Eficiência, 298,15 K | 0,081 p.p. | 0,372 p.p. | 0,141% |
| Eficiência, 373,15 K | 0,059 p.p. | 0,296 p.p. | 0,098% |
| Pressão, 1 atm | 0,0011 V | 0,0069 V | 0,082% |
| Pressão, 5 atm | 0,0011 V | 0,0067 V | 0,086% |

Todas as curvas de tensão, eficiência e pressão permanecem integralmente
dentro de 5% dos pontos digitalizados. A potência de 298,15 K mantém erro
médio inferior a 5%; a pequena discrepância remanescente decorre da
inconsistência interna entre os painéis de tensão e potência, discutida na
Seção 4.

## 8. Resultados padrão da plataforma

- `V_cell(1 A/cm², 298,15 K) = 0,5345 V`;
- `V_cell(1 A/cm², 373,15 K) = 0,5668 V`;
- potência máxima a 298,15 K: aproximadamente `5,10 kW`;
- potência máxima a 373,15 K: aproximadamente `5,40 kW`;
- eficiência a 1 A/cm²: `30,28%` e `32,10%`;
- diferença entre 5 atm e 1 atm em 0,6 A/cm²: aproximadamente `7,2 mV`.
