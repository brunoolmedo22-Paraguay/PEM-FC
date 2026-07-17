# Relatório — Engenharia Reversa da Figura 3 (OTEKON 2024)

**Segunda etapa de fidelidade.** Complementa `RELATORIO_FIDELIDADE_OTEKON.md`.
Objetivo: reconstruir o caso de simulação usado na Figura 3 do artigo,
digitalizando as curvas publicadas e ajustando o modelo contra elas.

---

## 1. Digitalização da Figura 3

**Fonte:** `image10.png` extraída do `.docx` original (1334×800 px),
única figura com múltiplos painéis do artigo.

**Método:** calibração pixel→dado obtida das posições OCR dos rótulos
numéricos de cada eixo (não de estimativa visual), rastreamento de
curvas por cor de pixel (azul e vermelho), filtro de outliers (Hampel +
exclusão de zona de artefato conhecida), remostragem uniforme a 28
pontos por curva.

**Layout identificado (2×2 painéis):**

| Posição | Título impresso | Eixo Y | Confirmado por |
|---|---|---|---|
| Superior-esquerdo | **"Activation Loss (Volts)"** | 0,5–1,1 V | OCR (3 modos de PSM concordantes) |
| Superior-direito | "Power (Watt)" | 0–6000 W | OCR |
| Inferior-esquerdo | "Efficiency (%)" | 25–60 % | OCR |
| Inferior-direito | **"Activation Loss (Volts)"** | 0,5–1,1 V | OCR (3 modos de PSM concordantes) |

**Temperaturas confirmadas por OCR da legenda:** T₁ = 298,15 K (azul),
T₂ = 373,15 K (vermelho) — exatamente os valores que você indicou.
298,15 K coincide exatamente com T_ref da Eq. 3, o que anula o termo de
correção térmica nessa curva especificamente.

**Achado no painel inferior-direito:** legenda com **P_H2 = 1 atm** e
**P_hava = 5 atm** ("hava" = "ar" em turco — os autores deixaram uma
variável do Simulink original sem traduzir). Isto resolve, com evidência
direta da própria figura (não mais placeholder), o maior GAP do
relatório anterior.

CSVs em `data/otekon_figure3/`, um por painel/temperatura, com coluna de
incerteza aproximada e sinalização de trechos interpolados.

---

## 2. Achado central: os dois painéis "Activation Loss" são, na prática, curvas de tensão

Evidência:

1. **Comportamento monotonicamente decrescente** com a corrente, faixa
   0,5–1,1 V — exatamente a forma clássica de uma curva de polarização
   (V×I), não de uma perda de ativação isolada (que deveria **crescer**
   em magnitude com I, segundo a Eq. 4).
2. **Numericamente quase idênticos entre si** (painel superior-esquerdo
   e inferior-direito): diferença média de ~0,03 V a 298 K, quase nula a
   373 K — consistente com duas tensões de célula sob condições de
   pressão ligeiramente diferentes, não duas grandezas físicas distintas.
3. **A legenda de pressões (P_H2, P_ar) só faz sentido físico para uma
   grandeza dependente de Nernst (Eq. 3).** A Eq. 4 (ativação) não
   depende de p_H2 nem diretamente de p_O2 — só de T, I e C_O2.

**Conclusão mais provável:** erro de rotulagem no artigo original (título
do eixo Y copiado de um painel para outro sem atualização) — um erro de
copy-paste comum em figuras geradas por template. Reportado como tal,
não corrigido silenciosamente: os CSVs preservam o título impresso
original com uma nota anexada.

**Consequência prática:** o artigo, apesar do que a Etapa 2.A do plano
original presumia, **não contém uma curva isolada de perda de ativação**
para calibrar esse bloco independentemente. A calibração teve que ser
feita diretamente contra a tensão total (Nernst + ativação + ôhmica),
sem separação prévia — um desvio do plano original, declarado aqui
explicitamente, não escondido.

---

## 3. Testes de convenção realizados

| Hipótese testada | Resultado |
|---|---|
| I em mA/cm² vs A/cm² na Eq. 4 | Ambas ajustáveis via xi1 (redundante com o intercepto); não discrimináveis pela forma da curva sozinha |
| ln vs log10 na Eq. 4 | log10 dá RMSE ligeiramente menor (0,145 vs 0,153 V) isoladamente, mas a diferença é absorvida pelo mesmo grau de liberdade (xi1); não é um discriminador forte com os dados disponíveis |
| Pressões: legenda da Fig.3 vs Tabela 1 (P=1,2 atm) | Diferença pequena no E de Nernst (1,2279 vs 1,2267 V); não é o fator dominante do erro |
| **R_mem literal (Eq. 12, C_H+=1) vs R_mem livre** | **Decisivo.** Literal: perda ôhmica desprezível (~mV), curva do modelo quase plana → RMSE ~0,15 V. R_mem livre (~0,20 Ω·cm², ignorando Eq. 11/12): RMSE cai para ~0,05–0,07 V |

**Achado mais importante desta etapa:** a inclinação quase linear da
curva de tensão digitalizada (queda de ~0,3 V ao longo de 0–0,8 A/cm²)
é a assinatura clássica de uma perda **ôhmica dominante**, não de uma
perda de ativação (que satura/achata em escala logarítmica). Isso é
incompatível com a leitura literal da Eq. 11/12 (que dá R_mem
desprezível, ver relatório anterior) — mas **é** compatível com um
modelo em que a resistência de membrana tem um valor comum de projeto
(~0,15–0,25 Ω·cm², faixa citada em literatura geral de Nafion
hidratado), sugerindo que os autores do OTEKON, na prática, **não usaram
a cadeia dinâmica de hidratação (Eq. 11/12) para gerar a Figura 3** —
usaram, mais provavelmente, um R_mem efetivo fixo.

---

## 4. Configuração final do "Modo 2 — Reprodução da Figura 3"

| Parâmetro | Valor | Como foi obtido |
|---|---|---|
| xi1 | −0,637 (literal: −0,9514) | Ajustado contra tensão (298 K + 373 K conjuntamente) |
| xi2, xi3, xi4 | mantidos literais | Não foi necessário alterar |
| R_mem | 0,203 Ω·cm² (constante, substitui Eq. 11/12) | Ajustado contra tensão |
| p_H2 | 1,0 atm | **Legenda da própria Figura 3** |
| P (catodo) | 5,0 atm | **Legenda da própria Figura 3** ("P_hava") |
| p_O2 | 1,05 atm (0,21×5,0) | Derivado, fração molar padrão do ar |
| p_H2O | 0,5 atm | GAP — não restringido pelos dados disponíveis |
| A_active | 232 cm² | Mesma inferência do relatório anterior (Tabela 1) |
| N_cells | ≈ 41 (ajustado: 40,85) | Ajustado contra a curva de potência |
| V_conc | **não incluída** | Não foi necessária para explicar as curvas no intervalo digitalizado (0–1,15 A/cm²); consistente com o próprio artigo, cujo a(T) só teria efeito visível em correntes mais altas |
| Eficiência | η ≈ 55,3% × V_cell | Ajuste empírico; não reproduz exatamente V_cell/E, /1,229, /1,254 nem /1,481 isoladamente (ver Seção 5) |

### Métricas de erro (contra dados digitalizados completos, incluindo pontos de menor confiança)

| Grandeza | T (K) | RMSE | MAE | Erro máx. | R² |
|---|---|---|---|---|---|
| Tensão | 298,15 | 0,096 V | 0,049 V | 0,344 V | 0,54 |
| Tensão | 373,15 | 0,070 V | 0,041 V | 0,241 V | 0,72 |
| Potência | 298,15 | 425 W | 279 W | 1168 W | 0,94 |
| Potência | 373,15 | 351 W | 284 W | 911 W | 0,95 |
| Eficiência | 298,15 | 3,08 pp | 1,81 pp | 12,5 pp | 0,84 |
| Eficiência | 373,15 | 2,14 pp | 1,73 pp | 6,9 pp | 0,92 |

Os erros máximos de tensão coincidem com a faixa x≈0,85–0,96 A/cm²,
onde um artefato de imagem (provável marca d'água) contamina a
digitalização nos dois painéis de tensão e no de potência — excluindo
essa faixa, o RMSE de tensão cai para ~0,05 V (298 K) e ~0,04 V (373 K).

### Sensibilidade e identificabilidade

- **xi1 e R_mem são parcialmente correlacionados** (xi1 desloca a curva
  verticalmente de forma quase uniforme; R_mem inclina). Com apenas duas
  curvas de temperatura, não há garantia de solução única — outras
  combinações de (xi1, R_mem) próximas produzem erros semelhantes.
- **N_cells é bem identificado** pela curva de potência (R²>0,93), pois
  a escala de potência é sensível quase exclusivamente a esse produto.
- **O fator de eficiência (0,553) não tem interpretação física limpa**
  isolada — é um ajuste de forma, não uma grandeza rastreável a uma
  definição termodinâmica padrão testada.

---

## 5. Sobre a inconsistência em T = 373,15 K

Com os parâmetros literais, `a(T) = 1,1×10⁻⁴ − 1,2×10⁻⁶(373,15−273) =
−9,98×10⁻⁶` — já negativo mesmo a 373,15 K (o limiar é ≈364,7 K). No
modelo de reprodução, **V_conc não é usada** (Seção 4), então essa
inconsistência não se propaga para a curva ajustada — ela permanece,
porém, como um problema **do modo Literal**, documentado e visível no
código (`aT_mode="literal"` como default, com alternativas `abs`,
`zero_floor`, `sign_flip` implementadas em
`calibration/flexible_model.py` para quem quiser explorar cada hipótese
isoladamente).

Não foi possível determinar qual dessas hipóteses os autores adotaram,
porque a Figura 3 não exige V_conc para ser reproduzida no intervalo
disponível (0–1,15 A/cm²) — a inconsistência pode nunca ter sido
"resolvida" pelos autores simplesmente porque não afetou visualmente os
resultados que eles publicaram.

---

## 6. Busca da formulação original (Etapa 6)

**Não foi possível acessar os textos de Spiegel (2008), Barbir (2005),
Chanpeng & Khunatorn (2009) ou Maher & Sadiq (2005) nesta sessão** — não
há acesso a bases de conteúdo de livros/artigos pagos a partir deste
ambiente. Declarado explicitamente, conforme solicitado: **não
verificado**. Qualquer afirmação sobre a origem exata das Eq. 4, 7, 8,
10–13 nessas referências (feita no relatório anterior) permanece como
inferência de conhecimento geral de literatura eletroquímica, não como
citação conferida.

---

## 7. O que precisa entrar no artigo com a devida cautela

- **Nunca chamar este ajuste de "validação"** — é engenharia reversa
  contra uma figura publicada, sem acesso aos dados brutos dos autores.
- A frase recomendada: *"interpretação mais provável compatível com os
  resultados publicados"*.
- O achado de rotulagem duplicada ("Activation Loss" em dois painéis
  distintos) deve ser citado como observação sobre o artigo-fonte, com
  a evidência (OCR + comportamento da curva + inconsistência com a
  legenda de pressão) apresentada em conjunto — nenhuma evidência
  isolada seria suficiente sozinha.
- O R_mem ajustado (0,203 Ω·cm²) **contradiz** a leitura literal da
  Eq. 11/12 do relatório anterior — isso deve ser apresentado como
  evidência de que **a Figura 3 provavelmente não foi gerada pela cadeia
  dinâmica de hidratação como impressa**, e não como uma "correção" do
  nosso modelo.

---

## 8. Respostas diretas

1. **Foi possível reproduzir a Figura 3?** Parcialmente. Potência e
   eficiência: bem reproduzidas (R² 0,84–0,95). Tensão: moderadamente
   (R² 0,54–0,72), limitada por digitalização e por xi1/R_mem não serem
   totalmente identificáveis com apenas 2 curvas de T.
2. **Configuração final:** ver tabela da Seção 4.
3. **Parâmetros que precisaram ser inferidos:** xi1 (recalibrado),
   R_mem (substituindo Eq. 11/12), N_cells (~41), p_H2O (permanece GAP).
4. **Equações com inconsistências aparentes:** Eq. 11/12 (dão R_mem
   desprezível, incompatível com a inclinação observada); Eq. 13 em
   T>364,7K (a<0); possível erro de rotulagem nos títulos dos painéis
   de tensão.
5. **Erro final:** RMSE de tensão 0,05–0,10 V; potência 350–425 W (num
   fundo de escala de ~5400 W); eficiência 2–3 pontos percentuais.
6. **Conjunto mínimo de alterações:** (a) substituir a cadeia Eq. 11/12
   por um R_mem efetivo constante (~0,2 Ω·cm²); (b) usar as pressões da
   legenda da Fig. 3 em vez das da Tabela 1; (c) escalar por N≈41
   células; (d) não aplicar V_conc no intervalo 0–1,2 A/cm².

---

## 9. Limitações

- Digitalização a partir de uma imagem de 1334×800 px — resolução
  intrínseca ≈0,001 A/cm²/pixel no eixo X; erro de leitura de cor
  estimado em ±0,01–0,03 V (colunas de incerteza nos CSVs).
- Artefato de imagem não identificado (possível marca d'água) contamina
  parte da faixa 0,85–0,98 A/cm² em três dos quatro painéis.
- Apenas 2 curvas de temperatura por grandeza — insuficiente para
  identificar unicamente todos os parâmetros simultaneamente (ver
  Seção 4, sensibilidade).
- Não houve tempo/orçamento computacional para a varredura combinatória
  exaustiva de todas as hipóteses listadas no plano original (Etapa 3);
  o caminho seguido foi guiado por evidência física incremental
  (Etapas 2–4 do plano), não por força bruta.
