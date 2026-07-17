# Texto para a seção de Metodologia (rascunho)

Sugestão de parágrafos, prontos para adaptar ao estilo do artigo.

---

**Digitalização da Figura 3.** As curvas publicadas na Figura 3 de
[OTEKON 2024] foram digitalizadas por rastreamento de pixels sobre a
imagem original extraída do documento fonte, com calibração dos eixos
obtida a partir das posições dos rótulos numéricos (reconhecimento
óptico de caracteres). Foram extraídos 28 pontos por curva, para as
quatro grandezas apresentadas (tensão, potência, eficiência e um painel
identificado no impresso como "Activation Loss") em ambas as
temperaturas indicadas (298,15 K e 373,15 K). A incerteza de
digitalização foi estimada em ±0,01–0,03 V (curvas de tensão) e
propagada para as métricas de ajuste subsequentes.

**Observação sobre a rotulagem da figura.** Dois dos quatro painéis
trazem o título impresso "Activation Loss (Volts)". A análise do
comportamento das curvas (monotonicamente decrescentes, faixa 0,5–1,1 V,
compatível com a magnitude de tensão de célula e incompatível com a
Eq. 4 do artigo, que prevê perda de ativação crescente em módulo com a
corrente) e da legenda de pressões parciais presente em um dos painéis
(que não é argumento da equação de ativação, mas é argumento direto da
equação de Nernst) indica que ambos os painéis correspondem, na prática,
a curvas de tensão de célula — sugerindo um erro de rotulagem no eixo Y
no artigo original, provavelmente por reaproveitamento de template entre
subplots.

**Reprodução por engenharia reversa.** Como o artigo não disponibiliza
uma curva isolada de perda de ativação nem os dados brutos da
simulação, a reprodução foi conduzida ajustando o modelo diretamente
contra a curva de tensão, hierarquicamente seguida pela curva de
potência (para o produto N_células × área ativa) e pela curva de
eficiência (para a definição empírica de rendimento). O ajuste do termo
de ativação (coeficiente ξ₁) e da resistência ôhmica de membrana
(tratada como parâmetro livre, substituindo a cadeia de hidratação
dinâmica das Eq. 11–12) contra as curvas de tensão em ambas as
temperaturas resultou em erro quadrático médio de 0,05–0,10 V (faixa de
eixo 0,5–1,1 V), com R² de 0,54–0,72. A curva de potência foi
reproduzida com R² de 0,94–0,95 (N_células ≈ 41, para área ativa de
232 cm² inferida da Tabela 1), e a de eficiência com R² de 0,84–0,92,
via um fator de escala empírico sobre a tensão de célula que não
corresponde exatamente a nenhuma das definições termodinâmicas de
eficiência usualmente empregadas na literatura.

**Achado relevante para a formulação ôhmica.** A resistência de membrana
necessária para reproduzir a inclinação da curva de tensão (~0,20 Ω·cm²)
é 4 a 5 ordens de grandeza maior que a obtida pela leitura literal das
Eq. 11–12 do artigo com os valores da Tabela 1 (que resulta em
resistência praticamente desprezível). Isso sugere que a Figura 3 do
artigo original não foi gerada pela cadeia dinâmica de hidratação
protônica como impressa, ou que há um parâmetro não documentado
(possivelmente a concentração protônica de referência da Eq. 11) que
compensa essa diferença.

**Ressalva metodológica.** Os parâmetros obtidos por este procedimento
constituem a interpretação mais provável compatível com os resultados
publicados, não uma validação experimental nem uma confirmação dos
valores internos usados pelos autores originais, aos quais não se teve
acesso.

---

## Frases de transição sugeridas (para reforçar honestidade epistêmica)

- "A interpretação mais provável compatível com os resultados
  publicados sugere que..."
- "O ajuste não permite distinguir de forma única entre as hipóteses
  A e B, dado o número limitado de curvas disponíveis..."
- "Esta digitalização está sujeita à resolução da imagem-fonte
  (1334×800 pixels) e deve ser interpretada como uma reconstrução
  aproximada, não como dado experimental."
