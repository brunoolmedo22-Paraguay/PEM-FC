# PEMFC Simulator -- OTEKON 2024

Simulador de uma celula de combustivel PEM (PEMFC) que reproduz o modelo
matematico de:

> Altintas, N.; Ertan, R. **"Modeling of a PEM Fuel Cell System in
> MATLAB"**. OTEKON 2024 (11th International Automotive Technologies
> Congress). Bursa Uludag University.

Este README documenta explicitamente, equacao por equacao e parametro
por parametro, o que vem literalmente do artigo e o que nao vem. Essa
rastreabilidade e um requisito deste projeto, nao um detalhe opcional.

---

## 1. Instalacao e execucao local

```bash
git clone <repo>
cd PEMFC_Simulator

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Validacao numerica sem interface:

```bash
python tests_smoke.py
```

---

## 2. Arquitetura

```
PEMFC_Simulator/
├── app.py                    # Interface Streamlit (5 abas). Sem fisica.
├── models/                   # FISICA PURA
│   ├── pemfc_model.py        # BasePEMFCModel + PEMFCModel (Eq. 2, 14)
│   ├── nernst.py             # Eq. 3 (Nernst) + Eq. 5 (Henry)
│   ├── activation.py         # Eq. 4, 6, 8 (ativacao)
│   ├── ohmic.py              # Eq. 9, 10, 11, 12 (ohmica + hidratacao)
│   ├── concentration.py      # Eq. 13 (concentracao)
│   └── dynamics.py           # Eq. 7 + 11 (EDOs, solve_ivp)
├── config/
│   └── parameters.py         # TODOS os parametros, com selo ARTIGO/GAP
├── simulation/
│   ├── solver.py             # Varreduras estacionarias e transitorias
│   └── calculations.py       # Potencia, eficiencia, MPP, H2 (extensoes)
├── visualization/
│   └── plots.py              # Figuras Plotly
├── tests_smoke.py            # Validacao numerica
├── requirements.txt
└── README.md
```

---

## 3. Equacoes implementadas (numeracao identica a do artigo)

| Eq. | Descricao | Formula |
|---|---|---|
| 2 | Tensao de celula | `Vcell = E - Vact - Vohm - Vconc` |
| 3 | Nernst | `E = E0 - 0.85e-3(T-298.15) + (RT/2F).ln[(pH2.pO2^0.5)/(pH2O.P^0.5)]` |
| 4 | Ativacao (Tafel) | `Eact = -0.9514 + 0.00312T - 1.87e-4.T.ln(I) + 7.4e-5.T.ln(CO2)` |
| 5 | O2 (Henry) | `CO2 = pO2/(5.08e6.exp(-498/T))` [mol/cm3] |
| 6 | | `Vact = -Eact` |
| 7 | Dupla camada | `dVact/dt = I/Cdl - Vact/(Ract.Cdl)` |
| 8 | | `Ract = Vact/I` [kOhm.cm2] |
| 9 | Ohmica | `Vohm = I.Rmem` |
| 10 | | `Rmem = tm/sigma` [kOhm.cm2] |
| 11 | Hidratacao | `dCH+/dt + CH+/tauH+ = (1 + alphaH+.I^3)/tauH+` |
| 12 | Condutividade | `sigma = (F^2/RT).DH+.CH+` |
| 13 | Concentracao | `Vconc = a.exp(b.I)`, `a=1.1e-4-1.2e-6(T-273)`, `b=8e-3` |
| 14 | Stack | `Vstack = N.Vcell` |

Todas confirmadas por leitura do `.docx` original do artigo (texto +
OCR de alta resolucao das formulas embutidas como imagens WMF).

---

## 4. Convencao de unidades -- ponto critico

**A densidade de corrente I esta em mA/cm2 em TODAS as equacoes acima,
nao em A/cm2.** Isso nao e uma escolha desta implementacao: e o que o
proprio artigo declara, por tres vias independentes:

1. Texto: *"Here I is the current density"* (logo apos a Eq. 4-5).
2. A Eq. 8 (`Ract=Vact/I`) e rotulada com unidade **kOhm.cm2**. Isso so
   surge de V dividido por mA/cm2 (V/(mA/cm2) = 1000 Ohm.cm2 = 1 kOhm.cm2).
   A mesma logica vale para a Eq. 10 (Rmem).
3. O coeficiente `b` da Eq. 13 e rotulado **cm2.mA-1** no texto do
   artigo -- confirmacao direta e textual, nao inferida.

Uma versao anterior deste projeto usava A/cm2 nos blocos ohmico e de
hidratacao. Isso estava **errado** e foi corrigido nesta versao apos
leitura do artigo original (antes, o modelo era reconstruido a partir
de uma transcricao de equacoes sem o documento fonte).

### Ponte de unidades necessaria na Eq. 7

A Tabela 1 da `Cdl = 0.035 x 232 F`, ou seja, um valor **total** (8.12 F)
para a celula especifica do artigo -- nao uma capacitancia especifica
por area. Mas a Eq. 7 usa o mesmo simbolo `I` que o resto do artigo
declara ser densidade de corrente. `dVact/dt = I/Cdl` so fecha em V/s se
`I` e `Cdl` estiverem na mesma base (ambos totais ou ambos especificos).

O artigo nao explicita essa conversao. Implementamos a ponte minima
necessaria em `models/dynamics.py`:

```
I_total [A]     = i[mA/cm2] / 1000 * A_active[cm2]
Ract_total [Ohm]= Ract[kOhm.cm2] * 1000 / A_active[cm2]
Cdl_total [F]   = 0.035[F/cm2] * A_active[cm2]     (= 8.12 F em 232 cm2)

dVact/dt = I_total/Cdl_total - Vact/(Ract_total . Cdl_total)
```

Verificacao de plausibilidade (nao e validacao contra o artigo): essa
ponte produz `tau_dl = Ract_total . Cdl_total` na faixa de dezenas de
milissegundos para correntes moderadas, compativel com constantes de
tempo de dupla camada tipicas na literatura eletroquimica geral. Isso e
um indicio de que a interpretacao e razoavel, nao uma confirmacao do
artigo. **Esta e a UNICA parte do modelo em que uma interpretacao
propria foi necessaria** para tornar a equacao executavel; esta isolada
em `models/dynamics.py` e sinalizada em destaque na aba Simulation do
app.

---

## 5. O "1" da Equacao 11

O artigo escreve literalmente `dCH+/dt + CH+/tauH+ = (1 + alphaH+.I^3)/tauH+`,
sem nomear uma constante de referencia. Isolada, essa equacao sugere uma
variavel de estado adimensional.

Mas a Eq. 12 (`sigma = F^2.D.C/(RT)`, relacao de Nernst-Einstein padrao)
so resulta em `S/cm` se `C` for uma concentracao molar `[mol/cm3]` --
nao um numero adimensional. As duas equacoes, tomadas juntas, so fecham
dimensionalmente se o "1" da Eq. 11 for lido como "1 mol/cm3" implicito.

Implementado como `CH_BASE = 1.0` [mol/cm3], uma **constante fixa**
(nao um parametro de calibracao livre) -- ver `pemfc_config/parameters.py` e
`models/ohmic.py` para a discussao completa.

**Consequencia numerica, reportada e nao "corrigida":** com
`CH_BASE=1`, `DH+=0.85e-6 cm2/s` (Tabela 1) e `T=353 K`, a Eq. 12 da
`sigma ~= 2.7 S/cm` -- 1 a 2 ordens de grandeza acima da faixa
experimental tipica de Nafion hidratado citada em literatura geral
(~0.02-0.20 S/cm, fora do OTEKON). Isso faz `Vohm` sair desprezivel
(<0.25% da queda total) quando os numeros do artigo sao usados ao pe da
letra. O simulador reporta essa condicao na barra lateral em vez de
mascara-la com uma recalibracao inventada.

---

## 6. Parametros -- origem, campo a campo

### Confirmados no artigo (Tabela 1)

| Parametro | Valor | Fonte |
|---|---|---|
| E0 | 1.229 V | Tabela 1 |
| R | 8.314 J/mol.K | Tabela 1 |
| F | 96485 C/mol | Tabela 1 |
| T | 353 K | Tabela 1 |
| P | 1.2 atm | Tabela 1 |
| t_m | 0.005 cm | Tabela 1 |
| C_dl (especifica x area) | 0.035 x 232 F | Tabela 1 |
| tau_H+ | 12.78 s | Tabela 1 |
| D_H+ | 0.85e-6 cm2/s | Tabela 1 |

### Confirmados no texto (fora da tabela)

| Parametro | Valor | Fonte |
|---|---|---|
| xi1, xi2, xi3, xi4 | -0.9514, 0.00312, -0.000187, 7.4e-5 | Texto, Eq. 4 |
| a1, a2 | 1.1e-4, 1.2e-6 | Texto, apos Eq. 13 |
| b | 8e-3 | Texto, apos Eq. 13 |
| CH_BASE (o "1" da Eq. 11) | 1.0 (interpretado como 1 mol/cm3) | Eq. 11 + exigencia dimensional da Eq. 12 |

### GAP -- o artigo NAO fornece (placeholders editaveis, sinalizados em vermelho na interface)

| Parametro | Placeholder | Por que e um gap |
|---|---|---|
| p_H2 | 1.0 atm | O texto diz "Related parameters are given in Table 1" apos citar p_H2, p_O2, p_H2O na Eq. 3 -- mas a Tabela 1 nao lista nenhuma das tres. Lacuna do proprio artigo. |
| p_O2 | 0.21 atm | Idem. Placeholder = fracao molar de O2 no ar atmosferico seco. |
| p_H2O | 0.50 atm | Idem. Placeholder arbitrario, sem base no artigo. |
| alpha_H+ | 1.5e-12 (cm2/mA)^3 | Nao aparece em lugar nenhum do artigo (nem texto, nem Tabela 1). |
| N (N_cells) | 1 | A Eq. 14 e generica; o artigo nao informa N para o caso estudado. |
| A_active | 232 cm2 | So aparece embutido no produto "0.035 x 232" da Tabela 1 -- o artigo nunca rotula esse numero como "area ativa" explicitamente. Inferencia razoavel (e a unica forma de o produto ter sentido dimensional), nao uma confirmacao literal. |

---

## 7. Extensoes desta implementacao (nao sao do artigo)

| Extensao | Base |
|---|---|
| Eficiencia (eta_HHV, eta_LHV) | Relacao termodinamica padrao (potencial termoneutro / V_cell), literatura geral de celulas a combustivel |
| Consumo de H2 | Lei de Faraday padrao, consumo estequiometrico ideal (sem excesso nem purga) |
| Regularizacoes numericas | Piso de corrente contra ln(0); saturacao V_act >= 0 (a Eq. 4, extrapolada para I muito baixo, pode dar V_act negativo, o que violaria a Eq. 2) |

Nenhuma dessas extensoes altera as Eq. 2-14; vivem em
`simulation/calculations.py`, separadas de `models/`.

---

## 8. O que foi removido em relacao a uma versao anterior

Uma versao anterior deste projeto (construida antes de o artigo original
estar disponivel, a partir de uma transcricao de equacoes) continha:

- Um parametro de "corrente de cruzamento" (`i_leak`) inventado para
  corrigir um OCV alto -- **removido**. Nao esta no artigo.
- Um preset "Membrana calibrada" que recalibrava a concentracao
  protonica para forcar uma condutividade "realista" -- **removido**.
  A Eq. 11, lida literalmente, nao expoe esse grau de liberdade.
- Presets "OTEKON -- O2 puro" e "OTEKON -- Stack 50 celulas" rotulados
  como variacoes do artigo, mas na verdade exemplos didaticos
  inventados sem base no OTEKON -- **removidos**.
- Um bloco ohmico/de hidratacao que usava A/cm2 em vez de mA/cm2 --
  **corrigido** (ver secao 4).

Essa limpeza segue diretamente de uma auditoria de rastreabilidade
completa realizada antes da leitura do artigo original, e da leitura do
`.docx` do artigo fornecido posteriormente.

---

## 9. Validacao vs. verificacao -- o que este projeto pode afirmar

- **Verificacao numerica** (`tests_smoke.py`): a curva V-I e monotonica
  decrescente, o transitorio converge ao estacionario, OCV ~0.98 V
  (compativel com a frase do artigo "in reality around 1 Volt").
  Isso e consistencia interna do codigo, nao validacao fisica.
- **Nao ha validacao contra dados experimentais.** O artigo menciona
  *"The model has been validated to an experiment of 1.2 kW PEM"*, mas
  nao publica os dados dessa validacao (curva V-I medida, condicoes de
  ensaio) -- portanto esta implementacao nao pode ser validada contra
  eles.
- **Nao ha comparacao com as figuras do artigo** (Figura 3 -- graficos
  de saida do modelo original). O `.docx` fornecido contem a figura como
  imagem; nao ha dados numericos extraiveis dela para comparacao ponto a
  ponto.

---

## 10. Solucao de problemas de deploy (Streamlit Community Cloud)

**Erro `ImportError` em `from config.parameters import ...`:** corrigido
nesta versao. A causa mais provavel e que `config` e o nome de um
pacote real publicado no PyPI (https://pypi.org/project/config/), que
pode sombrear a pasta local `config/` do repositorio em determinados
ambientes de resolucao de `sys.path`. O pacote local foi renomeado para
**`pemfc_config/`** em todo o projeto para eliminar esse risco por
completo. `app.py` tambem passou a inserir explicitamente a raiz do
repositorio em `sys.path` antes dos imports locais, como protecao
adicional contra diferencas de diretorio de trabalho entre ambientes.

Se, mesmo assim, o deploy falhar novamente:

1. No painel do Streamlit Cloud, clique em "Manage app" -> Logs e
   copie a mensagem de erro completa (a pagina publica mostra uma
   versao redigida por padrao; o log completo so aparece ali).
2. Confirme que a raiz do repositorio no GitHub contem `app.py` e as
   pastas `pemfc_config/`, `models/`, `simulation/`, `visualization/`
   diretamente, sem um subdiretorio extra (ex.: nao deve haver
   `PEMFC_Simulator/PEMFC_Simulator/app.py`).
3. Confirme que `runtime.txt` (Python 3.12) e `requirements.txt` foram
   commitados junto com o resto do projeto.
4. Force um "Reboot app" no painel do Streamlit Cloud apos qualquer
   correcao, pois o build costuma ficar em cache.

---

## 11. Extensao futura

`BasePEMFCModel` (`models/pemfc_model.py`) define o contrato minimo para
qualquer modelo PEMFC. Para adicionar outro modelo (Amphlett 1995
completo, um equipamento comercial calibrado por datasheet, etc.) basta
herdar dessa classe e implementar `reversible_voltage()` e `losses()` --
a app, o solver e os graficos nao mudam. Qualquer novo modelo desse tipo
deve manter a mesma disciplina de rotulagem ARTIGO/GAP usada aqui.
