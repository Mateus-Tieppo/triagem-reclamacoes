## Escolha no desenvolvimento (489 mensagens rotuladas pelo Claude)

Forma A: só os rótulos do Claude. Forma B: mais os rótulos das regras no resto do pool, com o peso indicado.

| Modelo | Forma de treino | F1 macro no desenvolvimento | Hiperparâmetros |
| --- | --- | --- | --- |
| logistica | A | 73,8% | {'clf__C': 10} |
| nb | B0.1 | 71,0% | {'clf__alpha': 0.1} |
| nb | B0.3 | 70,0% | {'clf__alpha': 0.1} |
| svm | B0.1 | 68,0% | {'clf__estimator__C': 1} |
| logistica | B0.1 | 67,7% | {'clf__C': 30} |
| logistica | B0.3 | 67,4% | {'clf__C': 30} |
| svm | B0.3 | 66,3% | {'clf__estimator__C': 1} |
| svm | A | 65,8% | {'clf__estimator__C': 0.1} |
| nb | A | 59,9% | {'clf__alpha': 0.1} |

Escolhido: logistica, forma A. Limiar de certeza: 0.8.
