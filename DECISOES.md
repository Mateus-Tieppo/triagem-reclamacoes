# Decisões

O que decidimos, por quê e o que ficou de fora. Os números saem de `make tudo` (sem Ollama) e dos arquivos em `results/`.

## Sumário
1. [A decisão central](#1-a-decisão-central)
2. [Por que não usar LLM para rotular](#2-por-que-não-usar-llm-para-rotular)
3. [Normalização](#3-normalização)
4. [Regras legíveis](#4-regras-legíveis)
5. [Modelo](#5-modelo)
6. [Decisão final e fila de revisão](#6-decisão-final-e-fila-de-revisão)
7. [Resultados](#7-resultados)
8. [Conferência de atraso](#8-conferência-de-atraso)
9. [Limitações](#9-limitações)
10. [O que ficou de fora](#10-o-que-ficou-de-fora)
11. [Quem fez o quê](#11-quem-fez-o-quê)

---

## 1. A decisão central
**Regras legíveis rotulam, o modelo generaliza e o humano decide na dúvida.**

Não existe um rótulo "verdadeiro" para 10 mil reclamações, e rotular tudo à mão não cabe no projeto. Então:
- **Regras legíveis** dão o rótulo de treino. Qualquer pessoa consegue ler uma regra e contestar.
- **Um modelo clássico** aprende com esses rótulos e cobre as mensagens que nenhuma regra pega.
- **Os casos incertos ou contraditórios** vão para uma fila de revisão humana.

Isso se chama supervisão fraca (*weak supervision*). Tudo roda localmente, de graça e sem LLM.

## 2. Por que não usar LLM para rotular
Testamos antes LLMs locais (seção 7). O Qwen 2.5 7B foi o melhor, mas decidimos não usar LLM em nenhuma etapa:
- **Custo e hardware:** cerca de 1 segundo por mensagem num notebook, contra menos de 1 milissegundo do modelo clássico.
- **Opinião que não dá para auditar:** um modelo treinado com rótulos de LLM copia a opinião da LLM. Uma regra pode ser lida e corrigida.
- **Reprodutibilidade:** regras e modelo dão sempre a mesma saída para a mesma entrada.

O código de LLM continua no repositório (`make llm`, fora do `make tudo`) só para a comparação.

## 3. Normalização
`src/triagem/normalizar.py`. Uma função usada igual nas regras, no treino e na predição (ela roda dentro do TF-IDF):
- minúsculas e sem acentos ("NÃO" e "ñ" viram "nao" e "n");
- links e e-mails viram `_link_`; números soltos (datas, pedidos, valores) viram `_num_`;
- letras repetidas três ou mais vezes viram uma ("péssimooooo" vira "pessimo");
- espaços colapsados.

## 4. Regras legíveis
`src/triagem/regras.py`: 43 regras, cada uma com nome, categoria e uma expressão regular. Foram escritas lendo amostras do pool de treino, nunca o conjunto de teste.

**Combinação:** se várias categorias disparam, vale a regra principal da taxonomia, o problema que originou a reclamação. A ordem é `nao_recebido_atraso`, `item_faltando`, `produto_errado`, `defeito_qualidade`, `cobranca_cancelamento`, `atendimento_loja`. `outro` só vale quando nada mais dispara. Quando duas categorias de origem (as quatro primeiras) disparam juntas, a mensagem fica marcada com **conflito**.

**Cobertura no pool de treino (10.453 mensagens):**

| Categoria | Mensagens |
| --- | --- |
| nao_recebido_atraso | 35,6% |
| item_faltando | 11,3% |
| produto_errado | 8,0% |
| defeito_qualidade | 9,9% |
| cobranca_cancelamento | 4,0% |
| atendimento_loja | 2,4% |
| outro | 1,6% |
| Sem rótulo | 27,1% |
| Com conflito | 5,6% |

Os disparos de cada regra estão em `results/regras.md`.

## 5. Modelo
`src/triagem/modelo.py`:

| | |
| --- | --- |
| Entrada | TF-IDF de palavras (1 e 2 palavras) e de caracteres (3 a 5), sobre o texto normalizado |
| Algoritmo | Regressão logística com `class_weight="balanced"`, que dá a probabilidade de cada categoria |
| Treino | As 7.033 mensagens que as regras rotularam sem conflito |
| Validação | Cruzada em 5 partes (`random_state=42`); `C` escolhido entre 0,3, 1, 3 e 10. Ficou `C = 10` |
| F1 macro na validação | 82,8%. **Isso mede concordância com as regras, não acerto real.** O acerto real está na seção 7 |
| Explicação | Para cada mensagem, as três palavras que mais puxaram para a categoria escolhida |

## 6. Decisão final e fila de revisão
`src/triagem/triagem.py`. A regra foi fixada antes de olhar o conjunto de teste:
- **Uma regra disparou sem conflito:** a categoria é a da regra. Vai para revisão se o modelo discordar.
- **Nenhuma regra disparou, ou houve conflito:** o modelo decide. Vai para revisão se houve conflito ou se a certeza ficou abaixo do limiar.

**O limiar de certeza é 0,80.** Ele foi escolhido nas predições fora da amostra da validação cruzada: é o início da faixa de certeza (de 0,1 em 0,1) a partir da qual toda faixa acima concorda pelo menos 85% com as regras. Olhamos faixa por faixa porque a média de tudo que passa do limiar esconde as mensagens incertas: com a média, o limiar daria 0,00 e nenhuma decisão incerta do modelo iria para revisão.

**Resultado no pool de treino** (`results/triagem.csv`): 32,1% das mensagens vão para revisão.

| Motivo | Mensagens |
| --- | --- |
| Certeza baixa | 2.137 |
| Regra e modelo discordam | 635 |
| Conflito entre regras | 312 |
| Conflito entre regras e certeza baixa | 271 |

A fila é grande porque quase 80% das decisões do modelo vão para revisão: a maioria delas é de mensagens que nenhuma regra pegou, onde ele é inseguro. Preferimos mandar para um humano a classificar errado. Quem quiser uma fila menor pode baixar o alvo de 85% em `ALVO_CONCORDANCIA`.

## 7. Resultados
Conjunto de teste: 300 reclamações, 53 rotuladas pelo Mateus e 247 pelo Claude. Ele só foi lido na avaliação final. F1 macro com intervalo de 95% por bootstrap.

| Abordagem | F1 macro | F1 nas 53 do Mateus | Revisão | F1 sem revisão | Latência |
| --- | --- | --- | --- | --- | --- |
| Regras sozinhas (controle) | 50,8% (44,3% a 56,9%) | 36,3% | - | - | < 1 ms |
| Regressão logística sozinha | 57,3% (50,4% a 63,3%) | 42,2% | - | - | < 1 ms |
| Híbrido (decisão final) | 54,8% (47,9% a 61,0%) | 44,9% | 32,3% | 67,7% | 1 ms |
| Referência: TF-IDF + SVM com rótulos do Qwen | 61,4% (54,1% a 68,0%) | 45,2% | - | - | < 1 ms |
| Referência: Qwen 2.5 7B zero-shot | 74,9% (67,8% a 80,7%) | 60,5% | - | - | 1.041 ms |

O que os números dizem:
1. **O modelo aprende além das regras.** Treinado só com os rótulos delas, ele ganha das regras sozinhas em 6,5 pontos de F1 e em 5,9 pontos nas 53 do Mateus. É o papel do controle, como no Fila Viva.
2. **O híbrido ficou abaixo do modelo sozinho no F1 geral** (54,8% contra 57,3%), porque quando uma regra dispara ela tem a palavra final, e as regras erram mais que o modelo. Nas 53 do Mateus, o híbrido fica um pouco acima (44,9% contra 42,2%). Não trocamos a regra de decisão depois de ver isso, porque seria escolher olhando o teste.
3. **Nas mensagens que não vão para revisão, o híbrido chega a 67,7% de F1.** A fila de revisão concentra os casos difíceis.
4. **Sem LLM, perdemos qualidade.** O Qwen fica 20 pontos acima. O SVM treinado com rótulos do Qwen fica 6,6 pontos acima do híbrido. É o preço de não depender de LLM nenhuma.
5. **`outro` é o ponto fraco** (8,7% de F1 no híbrido). Só 1,6% do pool tem regra de `outro`, e o conjunto de teste tem bem mais mensagens assim.

Tabela completa e F1 por categoria em `results/resultados.md`.

## 8. Conferência de atraso
`src/triagem/verdade.py` confere, com as datas reais de entrega da Olist, quantas mensagens classificadas como atraso são de pedidos de fato atrasados ou não entregues. Precisa de `data/raw/olist_orders_dataset.csv`, da mesma base pública no Kaggle. **Ainda não rodou:** o arquivo não está no repositório.

## 9. Limitações
- **Sem conjunto de desenvolvimento rotulado à mão.** A precisão das regras foi julgada lendo amostras, e o acerto real só apareceu na avaliação final.
- **O conjunto de teste tem 247 rótulos feitos pelo Claude.** A coluna "53 do Mateus" é a medida mais honesta, mas é pequena.
- **O modelo aprende os erros das regras.** A validação cruzada (82,8%) mede só concordância com elas.
- **Uma categoria por mensagem.** Reclamações com dois problemas ("não chegou e quero o dinheiro") ficam com a de origem.

## 10. O que ficou de fora
- **Uma ferramenta para usar a triagem** (página ou app). É o próximo passo.
- Multirrótulo.
- Embeddings e modelos pré-treinados grandes.

## 11. Quem fez o quê
- **Mateus:** a escolha da abordagem (supervisão fraca, sem LLM), as categorias e os 53 rótulos do conjunto de teste.
- **Claude (Anthropic), como apoio no código:** escreveu as regras lendo o pool de treino, o pipeline e esta documentação. As regras ficam legíveis em `src/triagem/regras.py` para revisão.
