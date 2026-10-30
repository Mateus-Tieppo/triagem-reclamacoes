## Resultados no conjunto ouro

300 mensagens no conjunto ouro (53 rotuladas pelo Mateus, o resto pelo Claude); 42 marcadas como dúvida. F1 macro com intervalo de 95% por bootstrap (1.000 reamostragens).

| Abordagem | Acurácia | F1 macro | F1 sem dúvida | F1 nas 53 humanas | Inválidas | Revisão | F1 sem revisão | Latência mediana |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ollama/qwen2.5-7b (zero) | 82,7% | 74,9% (67,8% a 80,7%) | 79,1% | 60,5% | 0,0% | - | - | 1041 ms |
| ollama/qwen2.5-7b (few) | 82,7% | 74,1% (67,4% a 80,0%) | 79,1% | 53,1% | 0,0% | - | - | 1076 ms |
| rotulos-claude/svm (forma-A) | 78,3% | 63,2% (55,2% a 70,4%) | 62,1% | 45,4% | 0,0% | 50,0% | 51,1% | 1 ms |
| ollama/llama3.2-3b (zero) | 68,3% | 61,5% (55,1% a 67,3%) | 66,0% | 51,9% | 0,0% | - | - | 359 ms |
| classico/tfidf-svm (treino-prata) | 73,3% | 61,4% (54,1% a 68,0%) | 64,1% | 45,2% | 0,0% | - | - | < 1 ms |
| supervisao-fraca/logistica (sozinho) | 72,7% | 57,8% (50,5% a 63,9%) | 60,1% | 42,2% | 0,0% | - | - | < 1 ms |
| supervisao-fraca/hibrido (final) | 70,7% | 54,9% (47,9% a 61,1%) | 56,7% | 44,9% | 0,0% | 33,3% | 68,9% | 1 ms |
| ollama/llama3.2-3b (few) | 57,0% | 52,7% (47,0% a 58,6%) | 54,8% | 43,4% | 0,0% | - | - | 394 ms |
| supervisao-fraca/regras (sozinhas) | 60,0% | 50,8% (44,3% a 56,9%) | 51,0% | 36,3% | 0,0% | - | - | < 1 ms |

### F1 por categoria

|  | classico/tfidf-svm (treino-prata) | ollama/llama3.2-3b (few) | ollama/llama3.2-3b (zero) | ollama/qwen2.5-7b (few) | ollama/qwen2.5-7b (zero) | rotulos-claude/svm (forma-A) | supervisao-fraca/hibrido (final) | supervisao-fraca/logistica (sozinho) | supervisao-fraca/regras (sozinhas) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nao_recebido_atraso | 82,9% | 57,7% | 78,3% | 88,4% | 90,2% | 86,2% | 82,4% | 84,7% | 76,7% |
| item_faltando | 86,4% | 79,5% | 80,5% | 89,1% | 89,1% | 85,4% | 74,7% | 75,6% | 70,3% |
| produto_errado | 65,1% | 67,4% | 65,3% | 78,6% | 74,7% | 74,4% | 61,3% | 63,2% | 45,9% |
| defeito_qualidade | 76,8% | 68,1% | 69,0% | 89,3% | 84,9% | 78,6% | 74,8% | 75,9% | 71,7% |
| atendimento_loja | 33,3% | 25,0% | 29,3% | 43,5% | 54,5% | 20,0% | 30,0% | 40,0% | 15,4% |
| cobranca_cancelamento | 56,4% | 44,4% | 51,1% | 65,0% | 71,8% | 53,3% | 52,6% | 56,4% | 50,0% |
| outro | 28,6% | 26,8% | 57,1% | 64,7% | 58,8% | 44,4% | 8,7% | 8,7% | 25,7% |

Atenção: 247 das 300 mensagens do ouro foram rotuladas pelo Claude, que também rotulou o treino do modelo novo (`rotulos-claude`). A comparação honesta com o Qwen é na coluna das rotuladas pelo Mateus.

F1 macro no desenvolvimento do modelo escolhido (svm, forma A): 70,8%. Detalhes em `results/desenvolvimento.md`.

### Cobertura das regras no pool de treino

| | Mensagens |
| --- | --- |
| Sem rótulo | 2853 (27,3%) |
| Com conflito | 581 (5,6%) |

### Conferência de atraso com datas reais de entrega

Pulada: falta `data/raw/olist_orders_dataset.csv` (base pública da Olist no Kaggle).
