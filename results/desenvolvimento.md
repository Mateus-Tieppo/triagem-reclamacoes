## Escolha no desenvolvimento (467 mensagens rotuladas pelo Claude)

Forma A: só os rótulos do Claude. Forma B: mais os rótulos das regras no resto do pool, com o peso indicado.

| Modelo | Forma de treino | F1 macro no desenvolvimento | Hiperparâmetros |
| --- | --- | --- | --- |
| logistica | A | 75,7% | {'clf__C': 10} |
| nb | B0.1 | 72,5% | {'clf__alpha': 0.1} |
| nb | B0.3 | 70,1% | {'clf__alpha': 0.1} |
| svm | B0.1 | 68,6% | {'clf__estimator__C': 1} |
| logistica | B0.1 | 68,2% | {'clf__C': 30} |
| logistica | B0.3 | 67,9% | {'clf__C': 30} |
| svm | B0.3 | 66,7% | {'clf__estimator__C': 1} |
| svm | A | 66,1% | {'clf__estimator__C': 0.1} |
| nb | A | 60,0% | {'clf__alpha': 0.1} |

Escolhido: logistica, forma A. Limiar de certeza: 0.8.
