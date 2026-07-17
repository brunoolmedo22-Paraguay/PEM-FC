# Relatório Técnico de Fidelidade — PEMFC Simulator vs. OTEKON 2024

**Documento de suporte metodológico para uso em artigo científico.**
Descreve, com rastreabilidade completa, a revisão do simulador PEMFC
frente ao texto original do artigo-fonte, após acesso ao documento
`.docx` original (anteriormente o modelo havia sido construído a partir
de uma transcrição de equações, sem o documento em mãos).

**Referência do artigo-fonte:**
Altıntaş, N.; Ertan, R. *"Modeling of a PEM Fuel Cell System in
MATLAB"*. 11th International Automotive Technologies Congress, OTEKON
2024. Bursa Uludağ University, Department of Polymer Materials /
Department of Automotive Engineering.

**Data desta revisão:** conduzida na mesma sessão de trabalho em que o
`.docx` do artigo foi disponibilizado.

---

## 1. Objetivo deste relatório

Este documento tem três funções:

1. **Registrar exatamente o que mudou** entre a versão anterior do
   simulador (construída sem acesso ao artigo original) e a versão
   atual (construída após leitura completa do `.docx`, incluindo OCR de
   alta resolução das fórmulas embutidas como imagens).
2. **Justificar cada decisão de interpretação** com evidência textual
   direta do artigo, prova dimensional, ou declaração explícita de que
   se trata de uma lacuna do próprio artigo.
3. **Antecipar as críticas metodológicas mais prováveis** que um
   revisor (humano ou não) faria a esta replicação, e responder a cada
   uma com a evidência disponível — ou reconhecer abertamente onde a
   evidência não é suficiente.

Nada neste relatório afirma mais do que pode ser sustentado pelo texto
do artigo. Onde a leitura exigiu uma escolha própria, isso está
identificado como tal, não disfarçado de dado original.

---

## 2. Metodologia de extração do artigo-fonte

O arquivo fornecido (`Modeling__of_a_pem_fuel_cell_system_in_matlab...docx`)
foi processado em duas camadas, porque as fórmulas do artigo **não estão
em texto** — estão embutidas como objetos de equação do Word (formato
WMF, imagens vetoriais), o que significa que uma extração de texto puro
(ex. `pandoc -t markdown`) reproduz o texto corrido normalmente, mas
mostra apenas placeholders de imagem onde deveriam estar as Equações 3,
7, 8, 10, 11 e 12.

Etapas realizadas:

1. `pandoc -t markdown` sobre o `.docx` → texto corrido completo,
   incluindo a Tabela 1, todos os coeficientes numéricos citados em
   prosa (Eq. 4, Eq. 13) e as referências bibliográficas.
2. Conversão do `.docx` para PDF via LibreOffice headless e
   rasterização de página (`pdftoppm`), para inspeção visual do layout
   completo, incluindo as Figuras 1 e 2.
3. Extração individual de cada objeto WMF (`word/media/imageN.wmf`) do
   pacote ZIP do `.docx`, conversão para PNG via LibreOffice, recorte
   automático da região com conteúdo (bounding box) e ampliação 6-10x.
4. **Dupla verificação** de cada fórmula: leitura visual direta da
   imagem ampliada **e** OCR (Tesseract) sobre a mesma imagem
   binarizada, comparando os dois resultados antes de aceitar uma
   leitura como confiável.

Este processo permitiu recuperar literalmente as Equações 3, 7, 8, 10,
11 e 12, que na versão anterior deste projeto haviam sido reconstruídas
a partir de uma transcrição de texto (fornecida em conversa, não o
documento original) — e que, como se verá na Seção 6, continha um erro
de convenção de unidades não detectável sem o documento fonte.

---

## 3. Resumo executivo das mudanças

| # | Item | Versão anterior | Versão atual | Motivo |
|---|---|---|---|---|
| 1 | Unidade de corrente no bloco ôhmico e de hidratação | A/cm² | **mA/cm²** | Confirmado por 3 evidências textuais independentes (Seção 6) |
| 2 | Resistências R_act, R_mem | Ω·cm² | **kΩ·cm²** | Unidade literalmente impressa no artigo nas Eq. 8 e 10 |
| 3 | Corrente de cruzamento (`i_leak`) | Presente (invenção própria) | **Removida** | Não existe no artigo |
| 4 | Concentração protônica de referência | Parâmetro livre `C_H_ref`, com preset "calibrado" | **Constante fixa `CH_BASE=1.0`**, não editável | É o "1" literal da Eq. 11; não é um grau de liberdade do artigo |
| 5 | Preset "Membrana calibrada" | Presente | **Removido** | Recalibrava um parâmetro que não existe como tal no artigo |
| 6 | Presets "OTEKON — O2 puro" / "Stack 50 células" | Presentes, rotulados como OTEKON | **Removidos** | Invenções didáticas rotuladas de forma enganosa |
| 7 | Dinâmica da dupla camada (Eq. 7) | Usava corrente e capacitância específicas (A/cm², F/cm²) sem citar a Tabela 1 | **Ponte de unidades explícita** (corrente total, capacitância total, resistência total) documentada linha por linha | A Tabela 1 dá C_dl como valor total (8.12 F), não específico |
| 8 | Rotulagem de parâmetros na interface | Nenhuma | **Selo ARTIGO / GAP em cada campo** | Rastreabilidade exigida para uso científico |
| 9 | Aba dedicada de auditoria | Inexistente | **Aba "Fidelidade & Gaps"** | Auditoria embutida na própria aplicação |

**O que NÃO mudou:** as Equações 3 (Nernst), 4/6 (ativação), 5 (Henry) e
13 (concentração), incluindo todos os coeficientes numéricos, já
estavam corretas na versão anterior — a transcrição original fornecida
em conversa continha essas equações certas. O erro estava
especificamente no bloco ôhmico/hidratação (Eq. 7, 9, 10, 11, 12) e em
extensões que eu havia adicionado sem base no artigo.

---

## 4. Equações — correspondência exata com o artigo

Tabela completa, com o texto/OCR de origem citado para cada uma.

| Eq. artigo | Fórmula (como impressa) | Evidência de origem | Status na implementação |
|---|---|---|---|
| 1 | `2H2 + O2 → 2H2O + Heat` | Texto corrido | Não numérica; conceitual |
| 2 | `Vcell = E − Vact − Vohm − Vconc` | Texto corrido | Literal (`models/pemfc_model.py::cell_voltage`) |
| 3 | `E = E0 − 0.85×10⁻³(T−298.15) + (RT/2F)·ln[(pH2·pO2^0.5)/(pH2O·P^0.5)]` | OCR de alta resolução da imagem da fórmula (`image3.wmf`) | Literal (`models/nernst.py::nernst_voltage`) |
| 4 | `Eact = −0.9514 + 0.00312T − 0.000187·T·ln(I) + 7.4×10⁻⁵·T·ln(CO2)` | Texto corrido (coeficientes citados em prosa) | Literal (`models/activation.py::activation_overpotential`) |
| 5 | `CO2 = pO2 / (5.08×10⁶·exp(−498/T))` | OCR da imagem (`image4.wmf`) | Literal (`models/nernst.py::oxygen_concentration`) |
| 6 | `Vact = −Eact` | Texto corrido | Literal |
| 7 | `dVact/dt = I/Cdl − Vact/(Ract·Cdl)` | OCR da imagem (`image5.wmf`) | Literal + **ponte de unidades** (Seção 7) |
| 8 | `Ract = Vact/I` **[kΩ·cm²]** | OCR da imagem (`image6.wmf`) + unidade impressa no texto | Literal, com unidade confirmada |
| 9 | `Vohm = I·Rmem` | Texto corrido | Literal |
| 10 | `Rmem = tm/σ` **[kΩ·cm²]** | OCR da imagem (`image7.wmf`) + unidade impressa no texto | Literal, com unidade confirmada |
| 11 | `dCH+/dt + CH+/τH+ = (1 + αH+·I³)/τH+` | OCR da imagem (`image8.wmf`) | Literal (Seção 8 discute o "1") |
| 12 | `σ = (F²/RT)·DH+·CH+` | OCR da imagem (`image9.wmf`) | Literal |
| 13 | `Vconc = a·exp(b·I)`, `a=1.1×10⁻⁴−1.2×10⁻⁶(T−273)`, `b=8×10⁻³` **[b: cm².mA⁻¹]** | Texto corrido, coeficientes e unidade de `b` citados em prosa | Literal |
| 14 | `Vstack = N·Vcell` | Texto corrido | Literal |

Todas as fórmulas em imagem foram lidas por **dois métodos
independentes** (inspeção visual direta em alta resolução + OCR) antes
de serem aceitas. Nenhuma foi reconstruída de memória.

---

## 5. Tabela 1 do artigo — reprodução literal

| Parâmetro | Símbolo | Valor | Unidade |
|---|---|---|---|
| Reference voltage | E₀ | 1.229 | V |
| Universal gas constant | R | 8.314 | J·mol⁻¹·K⁻¹ |
| Faraday constant | F | 96485 | C·mol⁻¹ |
| Bulk temperature | T | 353 | K |
| Cell pressure | P | 1.2 | atm |
| Membrane thickness | t_m | 0.005 | cm |
| Double layer capacitance | C_dl | 0.035 × 232 | F |
| Time constant | τ_H+ | 12.78 | s |
| Diffusion coefficient | D_H+ | 0.85×10⁻⁶ | cm².s⁻¹ (*) |

(*) O artigo imprime a unidade de D_H+ como "cm s⁻¹" na tabela, o que é
dimensionalmente incorreto para um coeficiente de difusão (deveria ser
cm²·s⁻¹). Interpretamos isso como um erro tipográfico do artigo — não
uma instrução para usar cm·s⁻¹ — porque (a) a Eq. 12 exige D em cm²/s
para σ sair em S/cm, e (b) 0.85×10⁻⁶ cm²/s é um valor de ordem de
grandeza absolutamente padrão para difusividade de próton em Nafion,
enquanto 0.85×10⁻⁶ cm/s não tem significado físico usual nesse
contexto. **Isso é uma correção de erratum evidente, não uma
reinterpretação livre.**

**Ponto crítico:** a Tabela 1 é citada no texto do artigo, logo após a
Eq. 3, com a frase *"Related parameters are given in Table 1"* — mas a
tabela **não lista p_H2, p_O2 nem p_H2O**, as três grandezas citadas
imediatamente antes dessa frase. Essa é uma lacuna do próprio artigo,
não um erro de leitura nossa (ver Seção 9).

---

## 6. A questão central: unidade de corrente (mA/cm² vs. A/cm²)

### 6.1 O que estava errado antes

A versão anterior deste simulador usava **mA/cm²** nos blocos de
ativação e concentração (Eq. 4, 13), mas **A/cm²** nos blocos ôhmico e
de hidratação (Eq. 7, 9, 10, 11). Essa mistura foi uma decisão de
engenharia numérica tomada **sem o artigo em mãos**, para evitar que o
termo `α_H+·I³` da Eq. 11 explodisse numericamente se I estivesse em
mA/cm² (na faixa de centenas a milhares).

### 6.2 Evidência de que essa mistura estava errada

Três evidências textuais **independentes**, extraídas do artigo, apontam
todas para a mesma conclusão — I é mA/cm² em **todas** as equações, sem
exceção:

**Evidência 1 — declaração direta.** Imediatamente após a Eq. 4/5, o
texto diz:

> *"Here I is the current density, CO2 is the oxygen concentration."*

Isso por si só já diz "densidade", mas não especifica a escala (mA ou
A). As evidências 2 e 3 resolvem isso.

**Evidência 2 — unidade impressa em R_act e R_mem.** As Eq. 8 e 10 vêm,
no documento original, com a unidade impressa explicitamente ao lado:

> Eq. 8: `Ract = Vact/I` ... **kΩ.cm²**
> Eq. 10: `Rmem = tm/σ` ... **kΩ.cm²**

Prova dimensional: pela Lei de Ohm, R = V/I. Se V está em volts e o
resultado sai em **quilo-ohm** (10³ Ω), então I precisa estar em
**miliampère** (10⁻³ A):

```
R [Ω·cm²] = V [V] / I [A/cm²]
R [kΩ·cm²] = R [Ω·cm²] / 1000 = V [V] / (I [A/cm²] × 1000)
           = V [V] / I [mA/cm²]        ✓ (mA = A/1000)
```

Ou seja: **V/(mA/cm²) dá exatamente kΩ·cm²**, sem nenhuma conversão
adicional. Se I estivesse em A/cm² (como a versão anterior assumia para
o bloco ôhmico), R sairia em Ω·cm², não kΩ·cm² — contradizendo a unidade
impressa no próprio artigo.

**Evidência 3 — unidade impressa no coeficiente `b` da Eq. 13.**
Imediatamente após a Eq. 13, o texto diz:

> *"Here the coefficients a (V) and b (cm².mA⁻¹) vary with temperature."*

`b` multiplica `I` dentro de uma exponencial (`Vconc = a·exp(b·I)`). Para
o produto `b·I` ser adimensional (exigência de qualquer expoente), e
`b` está em cm²/mA, então **I precisa estar em mA/cm²** nessa mesma
equação — confirmando, num terceiro ponto totalmente independente dos
dois primeiros, a mesma convenção.

### 6.3 Verificação numérica de consistência

Rodando o modelo corrigido com os valores literais da Tabela 1
(D_H+=0.85×10⁻⁶ cm²/s, CH_BASE=1, T=353K):

```
σ = (F²/RT)·DH+·CH+ = 2.696 S/cm
Rmem = tm/σ = 0.005/2.696 = 1.854×10⁻³ Ω·cm² = 1.854×10⁻⁶ kΩ·cm²
Vohm @ 1000 mA/cm² = 1000 × 1.854×10⁻⁶ = 1.854×10⁻³ V ≈ 1.85 mV
```

Isso é **dimensionalmente consistente** (mA/cm² × kΩ·cm² = V) e produz
um valor numérico plausível de ordem de grandeza para uma queda ôhmica
(miliVolts), o que não seria o caso se a unidade estivesse errada por um
fator de 1000 em qualquer direção. Esta é uma checagem de sanidade, não
uma prova adicional — a prova está nas Evidências 1-3.

---

## 7. A ponte de unidades da Equação 7 — a única interpretação própria do modelo

Esta é a parte do modelo em que uma decisão interpretativa foi
realmente necessária, e por isso recebe a análise mais detalhada.

### 7.1 O problema

A Tabela 1 dá `Cdl = 0.035 × 232 F`. Isso não é "0.035 F/cm²" como um
parâmetro específico isolado — é o produto já calculado, **8.12 F**,
rotulado com unidade simples "F" (não "F/cm²"). Ou seja: a Tabela 1
fornece uma capacitância **total**, específica da célula de 232 cm² do
artigo.

Mas a Eq. 7 usa o mesmo símbolo `I` que, pelas evidências da Seção 6, é
uma **densidade** de corrente (mA/cm²). Substituir uma densidade de
corrente diretamente dividida por uma capacitância total não fecha
dimensionalmente:

```
dV/dt deveria estar em [V/s]
I [mA/cm²] / Cdl [F]  =  [mA/(cm²·F)]  ≠  [V/s]
```

O artigo **não** explicita essa conversão em nenhum lugar do texto — a
Eq. 7 e a Tabela 1 são, tomadas ao pé da letra, mutuamente inconsistentes
em unidades.

### 7.2 A ponte implementada

Optamos pela única reconciliação que preserva os dois números que o
artigo efetivamente fornece (a densidade de corrente em mA/cm² das
demais equações, e a capacitância total de 8.12 F da Tabela 1),
convertendo tudo para uma base "total" consistente:

```
I_total [A]       = I [mA/cm²] / 1000 × A_active [cm²]
Ract_total [Ω]    = Ract [kΩ·cm²] × 1000 / A_active [cm²]
Cdl_total [F]     = 0.035 [F/cm²] × A_active [cm²]     (= 8.12 F em 232 cm², batendo com a Tabela 1)

dVact/dt = I_total/Cdl_total − Vact/(Ract_total · Cdl_total)
```

Implementado em `models/dynamics.py::state_derivatives`, com a mesma
justificativa comentada linha por linha no código-fonte.

### 7.3 Por que essa ponte, e não outra

Existiam pelo menos duas alternativas que consideramos e descartamos:

- **Tratar Cdl como se fosse "0.035 F/cm²" específico**, ignorando a
  área embutida no produto da Tabela 1. Descartada porque contradiz a
  leitura literal da tabela (o valor impresso é o produto, não o fator
  isolado).
- **Tratar I como corrente total nesta equação apenas**, mudando de
  convenção só aqui. Descartada porque não há nenhuma indicação textual
  de que o símbolo `I` mude de significado entre equações do mesmo
  artigo — seria uma suposição ainda mais arbitrária do que a ponte
  escolhida.

A ponte escolhida é a que usa **exclusivamente** números que o artigo
já fornece (a Tabela 1, e a convenção mA/cm² comprovada na Seção 6), sem
introduzir nenhum parâmetro novo.

### 7.4 Verificação de plausibilidade (não é validação)

Com essa ponte, para `I=500 mA/cm²`, `Vact≈0.5V`, `A_active=232 cm²`:

```
I_total = 0.5 A/cm² × 232 cm² = 116 A
Ract_kOhm.cm² = 0.5/500 = 0.001 kΩ·cm²
Ract_total = 0.001 × 1000 / 232 = 4.31×10⁻³ Ω
τ_dl = Ract_total × Cdl_total = 4.31×10⁻³ × 8.12 ≈ 0.035 s = 35 ms
```

Uma constante de tempo de dupla camada de dezenas de milissegundos é
consistente com a ordem de grandeza normalmente relatada na literatura
eletroquímica geral (não uma citação do OTEKON) para esse fenômeno. Isso
é um indício de que a ponte é razoável — **não** uma confirmação de que
é exatamente o que os autores do artigo fizeram internamente no
Simulink (o artigo descreve apenas as equações, não o diagrama de
blocos do modelo).

### 7.5 Como isso está sinalizado no produto entregue

- Comentário extenso no início de `models/dynamics.py`.
- Aviso em destaque (`st.warning`) na aba **Simulation**, junto à
  Eq. 7, visível sempre que o usuário abre essa seção.
- Linha dedicada na tabela de equações da aba **Fidelidade & Gaps**:
  *"Literal + ponte de unidades"*.

---

## 8. O "1" da Equação 11 — prova dimensional da interpretação

### 8.1 O texto literal

A Eq. 11, lida diretamente da imagem original:

```
dCH+/dt + CH+/τH+ = (1 + αH+·I³) / τH+
```

Não há, em nenhum lugar do artigo, um símbolo nomeado para esse "1" —
nenhuma variável tipo "C_ref" é definida no texto corrido nem na
Tabela 1.

### 8.2 Por que não pode ser lido como um "1" puramente adimensional

Isoladamente, a Eq. 11 é compatível com CH+ sendo uma variável de
estado normalizada/adimensional. Mas a Eq. 12, imediatamente em
seguida, é a relação de Nernst-Einstein:

```
σ = (F²/RT)·DH+·CH+
```

Essa é uma relação eletroquímica padrão em que, para σ sair em [S/cm]
(unidade de condutividade, exigida para a Eq. 10 funcionar), **CH+
precisa ser uma concentração molar [mol/cm³]**. Prova dimensional:

```
[F²/(RT)] = (C/mol)² / (J/mol) = C²/(mol·J) = C²/(mol·C·V) = C/(mol·V)
[F²/(RT)] × [DH+ em cm²/s] × [CH+]  deve dar [S/cm] = [C/(V·s)]/cm

C/(mol·V) × cm²/s × [CH+] = C·cm²/(mol·V·s)

Para isso = C/(V·s·cm), precisamos [CH+] = mol/cm³
```

Ou seja: **a Eq. 12, por si só, exige que CH+ tenha unidade de
concentração molar** — não é uma escolha nossa, é uma consequência
matemática obrigatória da fórmula que o próprio artigo escreve na
sequência imediata.

### 8.3 A reconciliação

As Eq. 11 e 12, tomadas isoladamente, sugerem convenções diferentes
para CH+ (adimensional vs. molar). A única forma de as duas fazerem
sentido em conjunto é ler o "1" da Eq. 11 como **"1 mol/cm³" implícito**
— ou seja, a equação foi escrita em forma "normalizada", omitindo a
unidade do termo constante por concisão, prática relativamente comum em
artigos que compactam a notação de uma implementação Simulink.

Implementado como `CH_BASE = 1.0` [mol/cm³] em
`config/parameters.py`, marcado como constante **fixa**, não exposta
como parâmetro de calibração livre na interface (diferente da versão
anterior, que expunha `C_H_ref` como editável e chegava a ter um preset
"calibrado" que o alterava para 0.0371 — um grau de liberdade que a
leitura literal do artigo não sustenta).

### 8.4 Consequência numérica, reportada sem maquiagem

Usando CH_BASE=1, DH+=0.85×10⁻⁶ cm²/s (Tabela 1) e T=353K:

```
σ = 2.696 S/cm
```

Isso está **1-2 ordens de grandeza acima** da faixa tipicamente citada
na literatura eletroquímica geral para condutividade de Nafion
hidratado (~0.02-0.20 S/cm — valor de conhecimento geral, não do
OTEKON). Consequência: a perda ôhmica sai desprezível
(0.24% do total no ponto de máxima potência, ver Seção 12) quando os
números do artigo são usados literalmente.

**Esta é uma consequência direta e honesta dos próprios números do
artigo — não um defeito desta implementação.** A versão anterior deste
projeto "corrigia" isso com um preset de calibração inventado; a versão
atual reporta a condição (aviso automático na barra lateral sempre que
σ sai da faixa típica) e não mascara o resultado.

---

## 9. Lacunas do próprio artigo (parâmetros GAP)

Seis parâmetros são necessários para a simulação rodar, mas **não têm
valor numérico fornecido pelo artigo**. Cada um está marcado com selo
vermelho "GAP" na interface, com o placeholder usado e a justificativa:

| Parâmetro | Placeholder usado | Evidência da lacuna |
|---|---|---|
| `p_H2` | 1.0 atm | Citado na Eq. 3, texto promete "Related parameters are given in Table 1" — a tabela não lista |
| `p_O2` | 0.21 atm | Idem. Placeholder = fração molar de O2 no ar atmosférico seco |
| `p_H2O` | 0.50 atm | Idem. Placeholder arbitrário, sem base no artigo |
| `alpha_H+` | 1.5×10⁻¹² (cm²/mA)³ | Não aparece em nenhum lugar do texto nem da Tabela 1 |
| `N` (N_cells) | 1 | Eq. 14 é genérica; nenhum N é dado para o caso estudado |
| `A_active` | 232 cm² | Só aparece embutido no produto "0.035×232" da Tabela 1; nunca rotulado explicitamente como "área ativa" |

Sobre `A_active`: esta é uma **inferência**, não um GAP arbitrário — é a
única forma de o produto "0.035 × 232 F" fazer sentido dimensional
(0.035 F/cm² é uma capacitância de dupla camada específica plausível; 232
cm² como área a multiplicar). Mas o artigo nunca escreve a frase "active
area = 232 cm²" — por isso mantém o selo de atenção, não de "confirmado".

Sobre `alpha_H+`: o placeholder é deliberadamente pequeno (10⁻¹²) porque,
sob a convenção mA/cm² confirmada na Seção 6, `I³` atinge ordens de
10⁹ em correntes de 1000 mA/cm² — um `alpha_H+` do tamanho usado na
versão anterior (1.5×10⁻³, calibrado sob a convenção A/cm² incorreta)
faria o termo `αH+·I³` dominar completamente sobre o "1" e produzir
concentrações protônicas absurdas. O valor atual foi escolhido apenas
para manter o termo de correção pequeno frente ao termo base — **não é
uma calibração contra nenhum dado**, é a menor intervenção possível para
o modelo não divergir numericamente.

---

## 10. O que foi removido, e por quê

| Item removido | Por que existia | Por que foi removido |
|---|---|---|
| `i_leak` (corrente de cruzamento) | Adicionado para evitar que o OCV saísse maior que E (Nernst) num contexto anterior de calibração contra um datasheet comercial | Não existe no artigo. Nenhuma menção a corrente de cruzamento/crossover em nenhum lugar do texto |
| Preset "Membrana calibrada (σ≈0.1 S/cm)" | Tentativa anterior de "consertar" a σ irreal recalibrando C_H_ref | A Eq. 11, lida literalmente, não expõe C_H_ref como parâmetro livre — é a constante "1" (Seção 8). Calibrá-la é alterar a equação, não ajustar um parâmetro do artigo |
| Presets "OTEKON — O2 puro" e "OTEKON — Stack 50 células" | Exemplos didáticos de sensibilidade a parâmetros | Rotulados como se fossem variações do artigo ("OTEKON —"), quando eram inteiramente inventados (N=50, por exemplo, não tem nenhuma base textual) |
| Módulo de calibração para equipamento comercial (Horizon VLII50) | Resposta a uma solicitação anterior, não relacionada a esta correção | Dependia da convenção de unidades incorreta (A/cm² no bloco ôhmico); removido nesta rodada para não misturar "reprodução fiel do OTEKON" com "calibração de equipamento comercial" no mesmo pacote. Pode ser refeito à parte, sob a convenção corrigida, se for necessário depois |

---

## 11. Extensões desta implementação — explicitamente não atribuídas ao artigo

| Extensão | Onde vive | Base |
|---|---|---|
| Eficiência (η_HHV, η_LHV) | `simulation/calculations.py` | Relação termodinâmica padrão (V_cell / potencial termoneutro), literatura geral de células a combustível, não citada no OTEKON |
| Consumo de H2 | `simulation/calculations.py` | Lei de Faraday padrão, consumo estequiométrico ideal, sem excesso nem purga |
| Piso de corrente (`i_min_mA`) | `models/activation.py` | Regularização numérica para evitar `ln(0)` quando I→0; não é uma equação do artigo |
| Saturação `V_act ≥ 0` | `models/activation.py` | A Eq. 4, extrapolada para I muito próximo de zero, pode produzir `E_act > 0` (logo `V_act < 0`), o que violaria a Eq. 2 (que pressupõe todas as quedas ≥ 0). Sem essa saturação, o circuito aberto simulado ficaria acima do potencial de Nernst — fisicamente inválido |

Nenhuma dessas extensões altera o valor de nenhuma das Equações 2 a 14
dentro da faixa de corrente em que a correlação empírica do artigo é
bem-comportada; elas atuam apenas nas bordas numéricas (I→0) ou fora do
núcleo físico (pós-processamento).

---

## 12. Resultados da verificação numérica

Saída de `python tests_smoke.py`, execução atual, incluída aqui na
íntegra para rastreabilidade:

```
DIAGNOSTICO DO MODELO (parametros do artigo OTEKON 2024)
==================================================================
  E_nernst [V]                     : 1.1797
  C_O2 [mol/cm3]                   : 1.6945e-07
  Tafel slope [V/dec]              : 0.1520
  sigma @ I=0 [S/cm]               : 2.6962
  R_mem @ I=0 [kOhm.cm2]           : 1.8545e-06
  C_dl_total [F]                   : 8.12
  a_conc(T) [V]                    : 1.4000e-05
  conc_model_valid                 : True
  sigma_fora_da_faixa_tipica       : True

CURVA DE POLARIZACAO
==================================================================
  OCV (i->0)            : 0.9779 V
  Monotonia decrescente : True
  MPP                    : 98.1 W @ 232.0 A (1000 mA/cm2)
  Densidade de potencia : 0.4228 W/cm2
  Reparto no MPP        : ativacao 94.2% | ohmica 0.24% | concentracao 5.5%

TRANSITORIO -- degrau 20 -> 500 mA/cm2 em t=5s
==================================================================
  Integracao              : sucesso
  V_cell antes (t=4.9s)   : 0.7246 V
  V_cell em t=5.1s        : 0.5370 V
  V_cell em t=60s         : 0.5104 V
  V_cell estacionario     : 0.5104 V
  Erro vs. estacionario   : 2.6e-09 V
```

**Leitura desses números:**

- OCV simulado (0.978 V) é consistente com a frase do próprio artigo na
  Introdução: *"A single fuel cell produces a theoretical potential of
  1.23 Volts, in reality around 1 Volt"* — o modelo, sem nenhum ajuste
  fino, reproduz essa ordem de grandeza.
- A curva é monotonicamente decrescente em toda a faixa simulada, sem
  descontinuidades — consistente com o formato qualitativo da Figura 2
  do artigo (curva de polarização típica, com as três regiões:
  ativação, ôhmica, transporte de massa).
- O transitório converge ao valor estacionário correspondente com erro
  de 2.6×10⁻⁹ V — confirma que a integração numérica (`solve_ivp`,
  método BDF) está correta e que o par (Eq. 7, Eq. 11) tem solução
  bem-comportada sob a ponte de unidades da Seção 7.
- A repartição de perdas no ponto de máxima potência (ativação 94.2%,
  ôhmica 0.24%, concentração 5.5%) é a consequência numérica direta e
  honesta dos parâmetros literais do artigo (Seção 8.4) — não foi
  ajustada para parecer "razoável".

---

## 13. Validação vs. verificação — distinção que deve constar no artigo

É importante que o artigo não confunda estas duas coisas:

- **Verificação** (o que este projeto tem): confirmação de que o código
  implementa corretamente as equações do artigo e se comporta de forma
  numericamente estável e fisicamente coerente internamente (curva
  monotônica, convergência do transitório, ordem de grandeza do OCV
  batendo com o texto).
- **Validação** (o que este projeto **não** tem): comparação
  quantitativa contra dados experimentais medidos.

O artigo original afirma, na seção de Conclusões:

> *"The model has been validated to an experiment of 1.2 kW PEM."*

Mas **não publica** os dados dessa validação — nem a curva V-I medida,
nem as condições de ensaio, nem qualquer tabela numérica associada. A
Figura 3 do artigo (mencionada como "Output graphs of the model") está
embutida como imagem raster no `.docx`, sem dados numéricos
extraíveis, o que impede uma comparação ponto a ponto mesmo que
quiséssemos tentar reconstruir os eixos.

**Recomendação para o artigo:** afirmar explicitamente que esta é uma
reprodução verificada da formulação matemática do OTEKON 2024, e não
uma validação experimental — nem deste trabalho, nem (de forma
extraível) do artigo original.

---

## 14. Perguntas que um revisor cético deve fazer — e as respostas

Esta seção antecipa objeções prováveis, no formato pergunta/resposta,
para uso direto na defesa da metodologia.

**P1. "Como vocês sabem que I é mA/cm² e não A/cm²? Isso não está
escrito explicitamente em nenhuma equação."**
R: Não está escrito como "[I] = mA/cm²" em nenhum lugar, correto. Mas
são três evidências indiretas convergentes e independentes (Seção 6):
a frase "current density", a unidade impressa kΩ·cm² em duas equações
diferentes (Eq. 8 e 10), e a unidade impressa cm²/mA no coeficiente b da
Eq. 13. Três evidências textuais apontando para a mesma conclusão, por
vias diferentes, é o padrão de evidência disponível — não é uma
suposição isolada.

**P2. "A ponte de unidades da Eq. 7 não é, na prática, uma invenção de
vocês, já que o artigo não pede isso?"**
R: É uma interpretação, e está rotulada como tal em três lugares
diferentes do produto (código, interface, este relatório). Não é uma
invenção arbitrária: usa exclusivamente números que o próprio artigo
fornece (a Tabela 1 e a convenção mA/cm² comprovada), sem introduzir
nenhum parâmetro novo. A alternativa seria simplesmente não conseguir
executar a Eq. 7 com os números do artigo — o que consideramos pior do
que documentar a ponte necessária.

**P3. "Por que confiar que a unidade de D_H+ na Tabela 1 é um erro de
digitação (cm²/s em vez de cm/s), em vez de aceitar o que está
escrito?"**
R: Porque a Eq. 12 exige dimensionalmente D em cm²/s para σ sair em
S/cm (mostrado na Seção 8.2 para C; o mesmo raciocínio aplica-se a D).
Aceitar "cm/s" tornaria a Eq. 12 dimensionalmente inconsistente por
completo, não apenas numericamente estranha. É mais defensável assumir
um erro tipográfico comum (falta de expoente) do que assumir que a
equação central do bloco de condutividade está errada.

**P4. "O CH_BASE=1 é uma suposição tão arbitrária quanto qualquer
outro valor que vocês pudessem ter escolhido — por que essa em
particular?"**
R: Não é uma escolha entre várias opções igualmente válidas. É a
leitura literal do número "1" que está impresso na Eq. 11, promovido à
unidade que a Eq. 12 exige matematicamente (mol/cm³) para ser
dimensionalmente consistente. A alternativa seria inventar um valor
diferente de 1 sem nenhum apoio textual — o que faríamos se
estivéssemos calibrando; não é o que fizemos aqui.

**P5. "Vocês reportam que σ sai 1-2 ordens de grandeza alta. Isso não
indica que a interpretação do CH_BASE está errada?"**
R: Pode indicar isso, honestamente não podemos descartar. Mas indica de
forma igualmente plausível que os PRÓPRIOS valores do artigo (D_H+ da
Tabela 1, especificamente) produzem esse resultado quando usados como
escritos — o que não é incomum em artigos de conferência que compilam
parâmetros de fontes diferentes (o artigo cita Spiegel 2008 e Barbir
2005 como fontes dos blocos de equações) sem necessariamente verificar
a consistência cruzada entre eles. Reportamos a condição em vez de
escolher silenciosamente um valor de CH_BASE diferente que "resolvesse"
o problema — isso seria calibração disfarçada de reprodução.

**P6. "Por que não usar directamente os dados do artigo para validar
numericamente, já que ele menciona um experimento de 1.2 kW?"**
R: Porque o artigo não publica esses dados (Seção 13). Não há tabela,
não há eixos numéricos extraíveis da Figura 3 (imagem raster), não há
anexo. Isso é uma limitação do artigo-fonte, não desta implementação —
e deve ser dito explicitamente no artigo que está sendo escrito, em vez
de omitido.

**P7. "As pressões parciais (p_H2, p_O2, p_H2O) são um ponto fraco
óbvio — qualquer resultado depende deles e vocês os inventaram."**
R: Concordamos que é o ponto mais frágil do modelo, e por isso é
sinalizado com o selo mais visível da interface (vermelho, "GAP", com
justificativa). Não os inventamos no sentido de "escolhemos para dar
certo" — são valores fisicamente plausíveis de composição atmosférica
padrão e operação típica de PEMFC, mas o artigo genuinamente não
especifica esses três números, apesar de prometer fazê-lo. Qualquer uso
científico deste simulador deve tratar esses três parâmetros como
entradas do usuário, não como resultado do artigo.

**P8. "Área ativa = 232 cm² parece conveniente demais."**
R: É o único número que aparece no artigo relacionado a área (dentro do
produto "0.035×232" da Tabela 1). Não foi escolhido para dar certo —
é o único candidato textual disponível. Mas é honesto reconhecer que o
artigo nunca escreve "active area = 232 cm²" como frase; é uma
inferência de que esse é o significado do segundo fator do produto, não
uma citação direta.

---

## 15. O que pode e o que não pode ser afirmado no artigo científico

### Pode ser afirmado, com confiança:

- As Equações 2 a 14 foram implementadas em correspondência exata com
  a formulação do artigo, incluindo os coeficientes numéricos citados
  (Tabela 1 e texto), verificado por leitura direta e OCR do documento
  original.
- A convenção de unidade de corrente (mA/cm²) foi determinada por
  evidência textual direta e cruzada, não por suposição.
- O simulador é internamente consistente (verificação numérica:
  monotonicidade, convergência do transitório, ordem de grandeza do OCV
  compatível com o texto do artigo).

### Não pode ser afirmado:

- Que o simulador foi "validado" contra dados experimentais — não foi,
  porque o artigo não disponibiliza esses dados.
- Que as pressões parciais, α_H+, N (número de células) ou a área ativa
  são "os valores do artigo" — são placeholders necessários, GAP,
  claramente sinalizados.
- Que a ponte de unidades da Eq. 7 é "o que o artigo faz" — é uma
  interpretação necessária para tornar a equação executável, justificada
  mas não confirmada pelo texto.

### Formulação sugerida para a seção de Métodos do artigo:

> *"O modelo foi implementado com correspondência literal às Equações
> 2-14 de [OTEKON 2024], incluindo os coeficientes da Tabela 1 e os
> citados no texto (Eq. 4 e 13). A convenção de densidade de corrente
> (mA/cm²) foi determinada por evidência textual cruzada (unidade
> kΩ·cm² impressa nas Eq. 8 e 10; unidade cm²/mA do coeficiente b na
> Eq. 13). Onde o artigo não fornece valores numéricos necessários à
> simulação (pressões parciais dos reagentes, coeficiente α_H+, número
> de células do stack), foram usados valores de placeholder,
> explicitamente identificados como tal na implementação. A dinâmica da
> dupla camada (Eq. 7) exigiu uma reconciliação de unidades entre a
> capacitância total tabelada e a densidade de corrente do restante do
> modelo, documentada em detalhe no material suplementar."*

---

## 16. Reprodutibilidade

```bash
git clone <repo>
cd PEMFC_Simulator
pip install -r requirements.txt
python tests_smoke.py        # verificação numérica (saída na Seção 12)
streamlit run app.py         # interface completa, com abas
                              # "Fidelidade & Gaps" e "Simulation"
                              # trazendo esta mesma rastreabilidade
                              # embutida na aplicação
```

Todos os números citados neste relatório foram gerados na mesma sessão
em que este documento foi escrito, a partir do código entregue — não
são valores de memória nem de execuções anteriores.

---

*Documento gerado como material de suporte metodológico. Recomenda-se
anexá-lo (ou uma versão resumida) como material suplementar do artigo,
dado o nível de escrutínio que decisões de unidade e interpretação como
as descritas aqui tipicamente recebem em revisão por pares de trabalhos
de modelagem de células a combustível.*
