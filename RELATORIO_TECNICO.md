# Relatório técnico — reconstrução do modelo PEMFC do OTEKON 2024

## 1. Resultado arquitetural

O projeto foi estruturado ao redor de uma única classe `PEMFCModel`. A
interface, os quatro gráficos, a análise de sensibilidade, as exportações, a
validação e a identificação paramétrica utilizam essa mesma implementação.
Não existe cálculo eletroquímico paralelo dentro de `app.py`.

## 2. Por que foi necessária uma otimização

A substituição direta dos coeficientes impressos no artigo não reproduz os
níveis, a inclinação e a curvatura da Figura 3. Foram encontradas ainda as
seguintes lacunas ou ambiguidades:

- número de células não informado;
- área ativa não identificada explicitamente;
- expressão de eficiência ausente;
- temperatura do painel de pressão não indicada;
- cadeia de hidratação dimensionalmente incompleta;
- coeficiente `a(T)` da perda de concentração negativo a 373,15 K;
- convenção de corrente da Eq. (13) incompatível com a curvatura publicada;
- coeficientes de ativação incapazes de fechar simultaneamente as quatro
  curvas de tensão.

A otimização não substitui o modelo por uma função arbitrária. A estrutura

`V_cell = E - V_act - V_ohm - V_conc`

foi preservada, e apenas os parâmetros não identificáveis diretamente foram
tratados como coeficientes efetivos inferidos.

## 3. Procedimento de engenharia reversa

### 3.1 Digitalização

As curvas da Figura 3 foram extraídas da imagem original por segmentação das
linhas vermelha e azul, calibração dos eixos e conversão pixel–grandeza. Os
CSVs resultantes permanecem em `data/otekon_figure3/` e não são utilizados
pela aplicação durante a simulação.

### 3.2 Dados do ajuste primário

A identificação eletroquímica usa somente:

- tensão a 298,15 K e 5 atm;
- tensão a 373,15 K e 5 atm;
- tensão a 373,15 K e 1 atm;
- tensão a 373,15 K e 5 atm.

Potência e eficiência não entram nessa função objetivo, porque são derivadas
da tensão e sua inclusão criaria dupla contagem da mesma informação.

### 3.3 Vetor identificado

Foram ajustados simultaneamente:

`θ = [ξ1, ξ2, ξ3, ξ4, R_mem,ref, n_R, a_ref, a_T, b]`.

Os valores iniciais de ativação e concentração foram construídos a partir das
equações publicadas. A resistência inicial foi estimada pela inclinação da
região aproximadamente ôhmica.

### 3.4 Função objetivo e algoritmo

Foi minimizada a soma dos resíduos de tensão normalizados por uma incerteza de
digitalização de `σV = 0,003 V`. O algoritmo é mínimos quadrados não lineares
limitados, método Trust Region Reflective (`scipy.optimize.least_squares`).
Foram usados 16 inícios determinísticos com semente `20260720`, escolhendo-se
o conjunto com menor RMSE conjunto.

O procedimento completo está em:

```bash
python calibration/identify_parameters.py --starts 16
```

O RMSE conjunto obtido para as quatro curvas de tensão foi de aproximadamente
`1,411 mV`.

### 3.5 Identificabilidade

O número de condição do Jacobiano escalado foi aproximadamente `2185,9`. As
principais correlações locais foram:

- `R_mem_ref × a_ref = -0,960`;
- `R_mem_ref × b = 0,932`;
- `n_R × a_T = -0,948`;
- `a_ref × b = -0,995`.

Essas correlações não impedem a reprodução das curvas, mas demonstram que
alguns coeficientes efetivos não devem ser interpretados isoladamente como
propriedades físicas únicas sem dados experimentais adicionais.

## 4. Inferências escalares posteriores

### Número de células

Com `A = 232 cm²`, o ajuste contínuo das curvas de potência fornece
`N_eq = 41,70`. Como o número de células deve ser inteiro, foi adotado
`N = 41`, preservando a escala publicada e evitando fatores ocultos. A
incompatibilidade residual entre os dois painéis de potência é mantida como
limitação explícita.

### Eficiência

A expressão utilizada é

`η = 100 U_f V_cell / E0`.

O fator foi inferido por mínimos quadrados escalares nas curvas de eficiência,
resultando em `U_f = 0,6961460963`.

## 5. Parâmetros eletroquímicos identificados

| Parâmetro | Valor |
|---|---:|
| `ξ1` | -0,674591776167 |
| `ξ2` | 0,00177858729827 |
| `ξ3` | -7,38573038384×10⁻⁵ |
| `ξ4` | 1,19623548544×10⁻⁵ |
| `R_mem,ref` | 0,225432192680 Ω·cm² |
| `n_R` | -0,776511316144 |
| `a_ref` | 0,00658205964880 V |
| `a_T` | 1,50924914732×10⁻⁵ V/K |
| `b` | 2,92419192535 cm²/A |

Esses valores são classificados como **INFERIDOS** e representam a
interpretação mais provável compatível com os resultados publicados.

## 6. Métricas da reconstrução

| Curva | RMSE | Erro relativo médio | Pontos dentro de 5% |
|---|---:|---:|---:|
| Tensão, 298,15 K | 0,001996 V | 0,154% | 100% |
| Tensão, 373,15 K | 0,001258 V | 0,101% | 100% |
| Potência, 298,15 K | 135,26 W | 3,250% | 100% |
| Potência, 373,15 K | 34,39 W | 1,930% | 92,1% |
| Eficiência, 298,15 K | 0,080 p.p. | 0,140% | 100% |
| Eficiência, 373,15 K | 0,060 p.p. | 0,098% | 100% |
| Pressão, 1 atm | 0,001086 V | 0,083% | 100% |
| Pressão, 5 atm | 0,001106 V | 0,086% | 100% |

## 7. Registro na plataforma

A aplicação contém a aba **Identificação paramétrica**, que apresenta:

- justificativa para a otimização;
- fluxograma do procedimento;
- dados utilizados;
- função objetivo;
- valores iniciais e limites;
- algoritmo e semente;
- parâmetros finais;
- robustez em relação aos inícios;
- correlações e número de condição;
- arquivos para reprodução e download.

O fluxograma está disponível em `outputs/optimization_flowchart.png` e
`outputs/optimization_flowchart.svg`.

## 8. Limitação corretamente interpretada

A solução reproduz os resultados gráficos do artigo com elevada precisão e
possui rastreabilidade integral. Isso não constitui validação experimental do
stack da embarcação nem prova que cada coeficiente efetivo seja idêntico ao
valor interno utilizado pelos autores. A contribuição está justamente em
identificar, documentar e resolver as lacunas necessárias para obter uma
implementação computacional coerente e reproduzível.
