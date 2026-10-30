## Resultados no conjunto ouro

300 mensagens no conjunto ouro (53 rotuladas pelo Mateus, o resto pelo Claude); 28 marcadas como dúvida. F1 macro com intervalo de 95% por bootstrap (1.000 reamostragens).

| Abordagem | Acurácia | F1 macro | F1 sem dúvida | F1 nas 53 humanas | Inválidas | Revisão | F1 sem revisão | Latência mediana |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ollama/qwen2.5-7b (few) | 83,0% | 73,6% (65,5% a 80,2%) | 78,1% | 55,1% | 0,0% | - | - | 1058 ms |
| ollama/qwen2.5-7b (zero) | 81,3% | 72,9% (65,8% a 79,1%) | 76,6% | 56,0% | 0,0% | - | - | 1123 ms |
| rotulos-claude/logistica (forma-A) | 82,3% | 65,7% (56,6% a 73,4%) | 67,3% | 50,7% | 0,0% | 28,0% | 71,0% | < 1 ms |
| supervisao-fraca/logistica (sozinho) | 72,0% | 56,5% (48,3% a 63,4%) | 60,9% | 49,9% | 0,0% | - | - | < 1 ms |
| supervisao-fraca/hibrido (final) | 71,3% | 55,0% (46,9% a 61,3%) | 59,2% | 52,1% | 0,0% | 32,3% | 73,6% | 1 ms |
| ollama/llama3.2-3b (few) | 64,7% | 54,1% (45,9% a 61,0%) | 55,3% | 37,4% | 0,0% | - | - | 511 ms |
| ollama/llama3.2-3b (zero) | 66,0% | 52,9% (45,3% a 60,1%) | 56,2% | 38,0% | 0,3% | - | - | 517 ms |
| supervisao-fraca/regras (sozinhas) | 62,0% | 52,2% (44,5% a 58,8%) | 53,7% | 45,7% | 0,0% | - | - | < 1 ms |

### F1 por categoria

|  | ollama/llama3.2-3b (few) | ollama/llama3.2-3b (zero) | ollama/qwen2.5-7b (few) | ollama/qwen2.5-7b (zero) | rotulos-claude/logistica (forma-A) | supervisao-fraca/hibrido (final) | supervisao-fraca/logistica (sozinho) | supervisao-fraca/regras (sozinhas) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sem_estoque | 37,5% | 33,3% | 66,7% | 82,4% | 46,2% | 57,1% | 57,1% | 33,3% |
| nao_recebido_atraso | 78,1% | 80,0% | 89,3% | 88,0% | 90,6% | 83,8% | 84,0% | 77,7% |
| item_faltando | 78,9% | 79,5% | 86,4% | 85,7% | 85,4% | 73,3% | 76,4% | 71,2% |
| produto_errado | 64,5% | 65,5% | 78,7% | 80,0% | 79,5% | 64,0% | 65,8% | 49,2% |
| defeito_qualidade | 54,1% | 56,4% | 88,7% | 84,0% | 84,9% | 73,7% | 73,0% | 73,3% |
| atendimento_loja | 40,0% | 22,9% | 52,6% | 48,0% | 22,2% | 23,5% | 33,3% | 18,2% |
| cobranca_cancelamento | 43,8% | 35,7% | 66,7% | 58,3% | 70,0% | 56,0% | 53,8% | 66,7% |
| outro | 35,7% | 50,0% | 60,0% | 57,1% | 46,7% | 8,3% | 8,3% | 27,8% |

Atenção: 247 das 300 mensagens do ouro foram rotuladas pelo Claude, que também rotulou o treino do modelo novo (`rotulos-claude`). A comparação honesta com o Qwen é na coluna das rotuladas pelo Mateus.

F1 macro no desenvolvimento do modelo escolhido (logistica, forma A): 75,7%. Detalhes em `results/desenvolvimento.md`.

### Cobertura das regras no pool de treino

| | Mensagens |
| --- | --- |
| Sem rótulo | 2765 (26,5%) |
| Com conflito | 627 (6,0%) |

### Conferência de atraso com datas reais de entrega

Pulada: falta `data/raw/olist_orders_dataset.csv` (base pública da Olist no Kaggle).
