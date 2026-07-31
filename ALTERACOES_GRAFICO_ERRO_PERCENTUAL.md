# Gráfico de erro percentual ponto a ponto

Foi incluído na aba **Resultados**, abaixo da comparação principal, um novo gráfico com quatro painéis:

- tensão em função da temperatura;
- potência do stack;
- eficiência elétrica;
- tensão em função da pressão.

O gráfico aparece quando a opção **Sobrepor curvas digitalizadas do artigo** está ativada.

Para cada ponto digitalizado do eixo x, o modelo é interpolado na mesma densidade de corrente e o erro é calculado por:

`erro (%) = |modelo - artigo| / |artigo| × 100`

O cursor mostra a densidade de corrente, o valor calculado pelo modelo, o valor digitalizado do artigo e o erro percentual absoluto.
# Novas exportações com zoom (v6)

- Novo botão **Erro de tensão × temperatura — COM ZOOM (SVG)**: destaca a
  região do maior erro percentual em um detalhe ampliado e mantém o mínimo
  global identificado no painel principal.
- Novo botão **Tensão × temperatura — ZOOM NAS DIFERENÇAS MÁXIMA E MÍNIMA
  (SVG)**: preserva a formatação destinada ao artigo e acrescenta dois
  detalhes ampliados, calculados automaticamente nos pontos de maior e menor
  diferença absoluta entre o modelo e os dados digitalizados.
- As novas figuras permanecem sem título interno e com o eixo de densidade de
  corrente limitado a 1,0 A/cm².
