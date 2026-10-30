## Escolha no desenvolvimento (500 mensagens rotuladas pelo Claude)

Forma A: só os rótulos do Claude. Forma B: mais os rótulos das regras no resto do pool, com o peso indicado.

| Modelo | Forma de treino | F1 macro no desenvolvimento | Hiperparâmetros |
| --- | --- | --- | --- |
| svm | A | 71,0% | {'clf__estimator__C': 0.3} |
| nb | B0.1 | 70,4% | {'clf__alpha': 0.1} |
| nb | A | 68,7% | {'clf__alpha': 0.1} |
| nb | B0.3 | 68,0% | {'clf__alpha': 0.1} |
| logistica | A | 67,8% | {'clf__C': 30} |
| svm | B0.1 | 66,9% | {'clf__estimator__C': 1} |
| logistica | B0.1 | 66,4% | {'clf__C': 30} |
| svm | B0.3 | 66,2% | {'clf__estimator__C': 1} |
| logistica | B0.3 | 65,9% | {'clf__C': 30} |

Escolhido: svm, forma A. Limiar de certeza: 0.8.
