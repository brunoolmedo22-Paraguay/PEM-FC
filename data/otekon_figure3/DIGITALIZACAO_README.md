# Digitalizacao da Figura 3 -- OTEKON 2024

Metodo: rastreamento de pixels por cor (azul=298.15K, vermelho=373.15K)
sobre a imagem original extraida do .docx (1334x800 px), com calibracao
pixel->dado a partir das posicoes OCR dos rotulos numericos dos eixos.

Filtro de outliers: Hampel (janela=6, 3.5 MAD) para remover contaminacao
de texto de eixos/legendas confundido com pixels de curva.

Para as curvas de potencia, foi imposta a ancora fisica P(I=0)=0
(consequencia obrigatoria de P=V.I), pois a deteccao de pixels nao
encontrou curva confiavel abaixo de I~0.28-0.35 A/cm2 no traço
298.15K -- provavel oclusao pela curva 373.15K (ambas muito proximas
nessa regiao).

| Arquivo | Pontos brutos | Mantidos apos filtro | Incerteza aprox. (unidade do eixo) |
|---|---|---|---|
| panel1_labeled_activationloss_298K.csv | 383 | 379 | 0.0252 |
| panel1_labeled_activationloss_373K.csv | 383 | 379 | 0.0239 |
| panel2_power_298K.csv | 212 | 203 | 481.7199 |
| panel2_power_373K.csv | 360 | 354 | 670.897 |
| panel3_efficiency_298K.csv | 378 | 378 | 0.1066 |
| panel3_efficiency_373K.csv | 378 | 378 | 0.1004 |
| panel4_labeled_activationloss_298K.csv | 303 | 299 | 0.0535 |
| panel4_labeled_activationloss_373K.csv | 279 | 274 | 0.0347 |
