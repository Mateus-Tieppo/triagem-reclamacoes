## Resultados no conjunto ouro

300 mensagens no conjunto ouro (53 rotuladas pelo Mateus, o resto pelo Claude); 42 marcadas como dúvida. F1 macro com intervalo de 95% por bootstrap (1.000 reamostragens).

| Abordagem | Acurácia | F1 macro | F1 sem dúvida | F1 nas 53 humanas | Inválidas | Latência mediana |
| --- | --- | --- | --- | --- | --- | --- |
| ollama/qwen2.5-7b (zero) | 82,7% | 74,9% (67,8% a 80,7%) | 79,1% | 60,5% | 0,0% | 1041 ms |
| ollama/qwen2.5-7b (few) | 82,7% | 74,1% (67,4% a 80,0%) | 79,1% | 53,1% | 0,0% | 1076 ms |
| ollama/llama3.2-3b (zero) | 68,3% | 61,5% (55,1% a 67,3%) | 66,0% | 51,9% | 0,0% | 359 ms |
| classico/tfidf-svm (treino-prata) | 73,3% | 61,4% (54,1% a 68,0%) | 64,1% | 45,2% | 0,0% | < 1 ms |
| ollama/llama3.2-3b (few) | 57,0% | 52,7% (47,0% a 58,6%) | 54,8% | 43,4% | 0,0% | 394 ms |

### F1 por categoria

|  | classico/tfidf-svm (treino-prata) | ollama/llama3.2-3b (few) | ollama/llama3.2-3b (zero) | ollama/qwen2.5-7b (few) | ollama/qwen2.5-7b (zero) |
| --- | --- | --- | --- | --- | --- |
| nao_recebido_atraso | 82,9% | 57,7% | 78,3% | 88,4% | 90,2% |
| item_faltando | 86,4% | 79,5% | 80,5% | 89,1% | 89,1% |
| produto_errado | 65,1% | 67,4% | 65,3% | 78,6% | 74,7% |
| defeito_qualidade | 76,8% | 68,1% | 69,0% | 89,3% | 84,9% |
| atendimento_loja | 33,3% | 25,0% | 29,3% | 43,5% | 54,5% |
| cobranca_cancelamento | 56,4% | 44,4% | 51,1% | 65,0% | 71,8% |
| outro | 28,6% | 26,8% | 57,1% | 64,7% | 58,8% |
