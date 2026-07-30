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
