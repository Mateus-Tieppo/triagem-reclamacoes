# Decisões

O que decidimos, por quê e o que ficou de fora. Os números saem de `make tudo` (sem Ollama e sem chamar o Claude) e dos arquivos em `results/`.

A versão atual usa um guia de rotulagem calibrado entre o Mateus e o Claude (8 categorias, com `sem_estoque`) e treina o modelo clássico com rótulos do Claude feitos nesse guia. As versões anteriores ficam abaixo como histórico.

## Versão atual: guia calibrado (v4.1) e treino com rótulos do Claude

### Por que mexer nos rótulos
Na versão anterior, o Mateus e o Claude concordavam em só 64% das mensagens, e em 33% das difíceis. O modelo aprendia o jeito do Claude e era cobrado pelo jeito do Mateus, então nenhuma troca de algoritmo resolvia. O problema era o guia, que deixava margem para decidir de jeitos diferentes.

### Calibração do guia
Três rodadas em mensagens do treino (nunca do teste). Em cada uma, o Mateus e um agente do Claude rotularam as mesmas mensagens às cegas; as divergências viraram regras. Histórico completo em [docs/guia-rotulagem.md](docs/guia-rotulagem.md).

| Rodada | Guia | Mensagens | Concordância na principal | Kappa | Contando a secundária |
| --- | --- | --- | --- | --- | --- |
| Antes | 7 categorias, sem desempate | 12 difíceis | 33% | | |
| 1 | v2: categoria `sem_estoque` e ordem da entrega | 40 | 72,5% | 0,68 | 82,5% |
| 2 | v3: exceções escolhidas em tese | 20 | 50,0% | 0,42 | 80,0% |
| 3 | v4: uma regra só, a da origem | 20 | 75,0% | 0,69 | 90,0% |

A rodada 2 foi a mais útil: as exceções que pareciam boas em tese contradiziam o jeito como o Mateus rotula na prática, e a v4 voltou a uma regra única. Kappa de 0,69 é concordância substancial.

**Guia v4.1, em resumo:** quando há mais de um problema, vale o primeiro na ordem `sem_estoque`, entrega, item faltando, produto errado, defeito; atendimento e cobrança só são o rótulo quando são o único problema; comentário leve nunca vence problema concreto; engano do consumidor sem diferença real é `outro`. Cada mensagem tem uma principal e, quando houver, uma secundária.

### Rotulagem com o guia novo
- **Treino:** os 3.000 do treino foram rotulados de novo pelo Claude (11,7% mudaram; dúvida caiu de 28% para 14%; 18% com secundária). Os antigos ficam em `data/rotulos_claude_v1.csv`.
- **Teste:** o Mateus revisou as 53 dele no guia novo (mudou 15); as outras 247 foram rotuladas de novo pelo Claude. Os rótulos antigos ficam na coluna `rotulo_v1` de `data/ouro.csv`.
- **LLMs:** Qwen e Llama rodaram de novo com o guia v4.1 no prompt, para a comparação continuar justa.

### Resultado
Mesmo pipeline da versão anterior (TF-IDF, regras como variáveis, três modelos comparados no desenvolvimento). Venceu a regressão logística só com os rótulos do Claude: 75,7% de F1 macro no desenvolvimento (antes 70,8%).

| Abordagem | Acurácia nas 300 | F1 macro nas 300 | Acurácia nas 53 do Mateus | F1 macro nas 53 | Latência |
| --- | --- | --- | --- | --- | --- |
| **ML clássico, guia v4.1** | **82,3%** | 65,7% (56,6% a 73,4%) | **75,5%** | 50,7% | < 1 ms |
| Qwen 2.5 7B zero-shot, guia v4.1 | 81,3% | **72,9%** (65,8% a 79,1%) | **75,5%** | **56,0%** | 1.123 ms |
| Qwen 2.5 7B few-shot, guia v4.1 | 83,0% | 73,6% (65,5% a 80,2%) | 75,5% | 55,1% | 1.058 ms |
| Llama 3.2 3B zero-shot, guia v4.1 | 66,0% | 52,9% (45,3% a 60,1%) | 58,5% | 38,0% | 517 ms |

1. **Na acurácia, o modelo clássico empata com o Qwen.** Nas 53 do Mateus, os dois acertam 75,5%; nas 300, o clássico faz 82,3% contra 81,3% do Qwen zero-shot. Roda em menos de 1 ms, contra cerca de 1 segundo.
2. **No F1 macro, o Qwen continua na frente** (56,0% contra 50,7% nas 53). Essa métrica dá o mesmo peso a cada categoria, e o Qwen vai melhor nas pequenas: `sem_estoque`, `atendimento_loja` e `outro`.
3. **A fila de revisão ficou bem menor:** 20,9% do pool (antes 45,7%). No teste, o modelo decide sozinho 72% das mensagens e acerta 90,3% delas; nas que vão para revisão, acerta 61,9%.
4. **Ainda vale o aviso:** 247 das 300 mensagens do teste foram rotuladas pelo Claude, que também rotulou o treino. A comparação honesta é nas 53 do Mateus, que são poucas: lá a diferença de acurácia é zero e a de F1 tem intervalo largo.

---

## Versão 2: treino com rótulos do Claude (guia antigo)

### A decisão
**O Claude rotula o treino uma única vez; a triagem continua só com ML clássico, local e de graça.**

A supervisão fraca parou em 54,9% de F1 macro no ouro, porque o modelo copiava os erros das regras. Para melhorar, trocamos a fonte dos rótulos de treino. O Mateus aceitou com isso deixar de dizer "sem LLM nenhuma": agora a LLM entra só no desenvolvimento, para rotular, e nunca na triagem.

### O que foi rotulado
`src/triagem/selecao.py` escolheu 3.000 mensagens do pool de treino, nenhuma do ouro:
- **500 de desenvolvimento**, sorteadas fora das mensagens lidas para escrever as regras. A revisão final achou 11 delas numa amostra que pode ter sido lida para as regras; essas saíram, e a escolha usa 489. É nelas que escolhemos modelo, forma de treino e limiar.
- **1.000 de treino sorteadas.**
- **1.500 de treino em que o modelo da supervisão fraca tinha menos certeza**, para cobrir os casos difíceis.

Cada lote de 150 foi para um agente do Claude (Opus 5.5, outubro de 2026) que recebeu só os textos e o guia de rotulagem (`taxonomia.GUIA_ROTULAGEM`, o mesmo usado no ouro), sem nenhum rótulo. Os rótulos estão em `data/rotulos_claude.csv`; marcados com dúvida: 28%.

**Consistência:** 200 mensagens do desenvolvimento foram rotuladas de novo, às cegas, por outros agentes. Acordo de 98,0% (kappa 0,97). Isso mede só se o Claude concorda com ele mesmo, não se acerta: nas 53 mensagens do ouro rotuladas pelos dois, o Claude e o Mateus concordaram em 64%.

### Modelo
`src/triagem/modelo.py` e `src/triagem/desenvolvimento.py`. Variáveis: TF-IDF de palavras e de caracteres mais as 43 regras como colunas 0/1 (as regras viraram pistas, não decisão). Comparamos no desenvolvimento três modelos e três formas de treino (A: só os rótulos do Claude; B: mais os rótulos das regras no resto do pool, com peso 0,1 ou 0,3):

| Modelo | Forma | F1 macro no desenvolvimento |
| --- | --- | --- |
| **SVM linear calibrado** | **A** | **70,8%** |
| Naive Bayes complementar | B, peso 0,1 | 70,2% |
| Naive Bayes complementar | A | 68,5% |
| Naive Bayes complementar | B, peso 0,3 | 68,0% |
| Regressão logística | A | 67,6% |
| SVM linear calibrado | B, peso 0,1 | 66,9% |
| Regressão logística | B, peso 0,1 | 66,4% |
| SVM linear calibrado | B, peso 0,3 | 66,2% |
| Regressão logística | B, peso 0,3 | 65,9% |

Venceu o SVM com só os rótulos do Claude. Somar os rótulos das regras piorou quase sempre. O modelo final treina só com as 2.500 de treino; o desenvolvimento não entra.

### Decisão e fila de revisão
O modelo decide sempre. A mensagem vai para revisão quando a certeza fica abaixo de 0,80 (mesmo critério por faixas da versão anterior, agora calculado no desenvolvimento) ou quando o texto não tem letras. No pool, 45,7% vão para revisão, todas por certeza baixa. Esse número está um pouco subestimado: nas 2.500 mensagens de treino a predição é do próprio modelo que as viu, e a certeza fica mais alta.

### Resultados no ouro
Avaliado uma única vez, no fim.

| Abordagem | F1 macro | F1 nas 53 do Mateus | Acerto nas 53 | Revisão | Latência |
| --- | --- | --- | --- | --- | --- |
| **Rótulos do Claude + SVM** | **63,2%** (55,2% a 70,4%) | 45,4% | 60,4% | 50,0% | 1 ms |
| Supervisão fraca (versão anterior) | 54,9% (47,9% a 61,1%) | 44,9% | - | 33,3% | 1 ms |
| Qwen 2.5 7B zero-shot | 74,9% (67,8% a 80,7%) | 60,5% | - | - | 1.041 ms |

O que os números dizem:
1. **Não passamos do Qwen.** Nas 53 do Mateus, que é a régua honesta, o modelo novo faz 45,4% contra 60,5% do Qwen.
2. **Melhorou bastante no geral:** de 54,9% para 63,2% de F1 no ouro. Mas 247 das 300 mensagens do ouro também foram rotuladas pelo Claude, então parte desse ganho é o modelo concordar com o jeito do Claude rotular. Nas 53 do Mateus o ganho foi de só 0,5 ponto.
3. **Quando o modelo decide sozinho, ele acerta muito:** 91,3% de acerto nas 150 mensagens do ouro que não foram para revisão, contra 65,3% nas que foram. A fila de revisão separa bem o fácil do difícil; o preço é mandar metade para um humano.
4. **O F1 caiu do desenvolvimento (70,8%) para o ouro (63,2%).**
5. **As categorias pequenas continuam fracas:** `atendimento_loja` (20,0%), `outro` (44,4%) e `cobranca_cancelamento` (53,3%). O desenvolvimento teve muito poucas mensagens de `atendimento_loja` e `cobranca_cancelamento`.

A coluna "F1 sem revisão" de `results/resultados.md` (51,1%) é um F1 macro só sobre as categorias que aparecem nas aceitas e fica baixa porque quase nenhuma mensagem das categorias pequenas é aceita. O acerto nas aceitas (91,3%) descreve melhor o que acontece.

### Limitações
- **Rótulos de treino e de teste do mesmo rotulador.** Por isso a comparação com o Qwen vale nas 53 do Mateus, que são poucas.
- **A consistência de 98% não é acerto.**
- **Categorias pequenas com poucos exemplos** no treino e no desenvolvimento.

---

# Histórico: supervisão fraca (versão anterior, sem LLM)

## 1. A decisão central
**Regras legíveis rotulam, o modelo generaliza e o humano decide na dúvida.**

Não existe um rótulo "verdadeiro" para 10 mil reclamações, e rotular tudo à mão não cabe no projeto. Então:
- **Regras legíveis** dão o rótulo de treino. Qualquer pessoa consegue ler uma regra e contestar.
- **Um modelo clássico** aprende com esses rótulos e cobre as mensagens que nenhuma regra pega.
- **Os casos incertos ou contraditórios** vão para uma fila de revisão humana.

Isso se chama supervisão fraca (*weak supervision*). Tudo roda localmente, de graça e sem LLM.

## 2. Por que não usar LLM para rotular
*Era a decisão da versão anterior; a versão atual passou a usar o Claude só para rotular o treino.*

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
| nao_recebido_atraso | 35,7% |
| item_faltando | 11,3% |
| produto_errado | 8,0% |
| defeito_qualidade | 9,9% |
| cobranca_cancelamento | 4,0% |
| atendimento_loja | 2,2% |
| outro | 1,6% |
| Sem rótulo | 27,3% |
| Com conflito | 5,6% |

Os disparos de cada regra estão em `results/regras.md`.

## 5. Modelo
`src/triagem/modelo.py`:

| | |
| --- | --- |
| Entrada | TF-IDF de palavras (1 e 2 palavras) e de caracteres (3 a 5), sobre o texto normalizado |
| Algoritmo | Regressão logística com `class_weight="balanced"`, que dá a probabilidade de cada categoria |
| Treino | As 7.019 mensagens que as regras rotularam sem conflito |
| Validação | Cruzada em 5 partes (`random_state=42`); `C` escolhido entre 0,3, 1, 3 e 10. Ficou `C = 10`, o maior valor da grade; um valor maior pode ser melhor e fica para testar |
| F1 macro na validação | 82,9%. **Isso mede concordância com as regras, não acerto real.** O acerto real está na seção 7 |
| Explicação | Para cada mensagem, as três palavras que mais puxaram para a categoria escolhida |

## 6. Decisão final e fila de revisão
`src/triagem/triagem.py`. A regra foi fixada antes de olhar o conjunto de teste:
- **Uma regra disparou sem conflito:** a categoria é a da regra. Vai para revisão se o modelo discordar.
- **Nenhuma regra disparou, ou houve conflito:** o modelo decide. Vai para revisão se houve conflito ou se a certeza ficou abaixo do limiar.
- **Texto sem nenhuma letra** (só número, emoji ou pontuação): vai sempre para revisão, com o motivo "texto sem conteúdo". Sem isso, um número de pedido colado sozinho saía com certeza alta.

**O limiar de certeza é 0,80.** Ele foi escolhido nas predições fora da amostra da validação cruzada: é o início da faixa de certeza (de 0,1 em 0,1) a partir da qual toda faixa acima concorda pelo menos 85% com as regras. Olhamos faixa por faixa porque a média de tudo que passa do limiar esconde as mensagens incertas: com a média, o limiar daria 0,00 e nenhuma decisão incerta do modelo iria para revisão.

**Resultado no pool de treino** (`results/triagem.csv`): 32,2% das mensagens vão para revisão.

| Motivo | Mensagens |
| --- | --- |
| Certeza baixa | 2.152 |
| Regra e modelo discordam | 638 |
| Conflito entre regras | 313 |
| Conflito entre regras e certeza baixa | 268 |

A fila é grande porque quase 80% das decisões do modelo vão para revisão: a maioria delas é de mensagens que nenhuma regra pegou, onde ele é inseguro. Preferimos mandar para um humano a classificar errado. Quem quiser uma fila menor pode baixar o alvo de 85% em `ALVO_CONCORDANCIA`.

## 7. Resultados
Conjunto de teste: 300 reclamações, 53 rotuladas pelo Mateus e 247 pelo Claude. Ele só foi lido na avaliação final. F1 macro com intervalo de 95% por bootstrap.

| Abordagem | F1 macro | F1 nas 53 do Mateus | Revisão | F1 sem revisão | Latência |
| --- | --- | --- | --- | --- | --- |
| Regras sozinhas (controle) | 50,8% (44,3% a 56,9%) | 36,3% | - | - | < 1 ms |
| Regressão logística sozinha | 57,8% (50,5% a 63,9%) | 42,2% | - | - | < 1 ms |
| Híbrido (decisão final) | 54,9% (47,9% a 61,1%) | 44,9% | 33,3% | 68,9% | < 1 ms |
| Referência: TF-IDF + SVM com rótulos do Qwen | 61,4% (54,1% a 68,0%) | 45,2% | - | - | < 1 ms |
| Referência: Qwen 2.5 7B zero-shot | 74,9% (67,8% a 80,7%) | 60,5% | - | - | 1.041 ms |

O que os números dizem:
1. **O modelo aprende além das regras.** Treinado só com os rótulos delas, ele ganha das regras sozinhas em 7,0 pontos de F1 e em 5,9 pontos nas 53 do Mateus. É o papel do controle, como no Fila Viva.
2. **O híbrido ficou abaixo do modelo sozinho no F1 geral** (54,9% contra 57,8%), porque quando uma regra dispara ela tem a palavra final, e as regras erram mais que o modelo. Nas 53 do Mateus, o híbrido fica um pouco acima (44,9% contra 42,2%). Não trocamos a regra de decisão depois de ver isso, porque seria escolher olhando o teste.
3. **Nas mensagens que não vão para revisão, o híbrido chega a 68,9% de F1.** A fila de revisão concentra os casos difíceis.
4. **Sem LLM, perdemos qualidade.** O Qwen fica 20 pontos acima. O SVM treinado com rótulos do Qwen fica 6,5 pontos acima do híbrido. É o preço de não depender de LLM nenhuma.
5. **`outro` é o ponto fraco** (8,7% de F1 no híbrido). Só 1,6% do pool tem regra de `outro`, e o conjunto de teste tem bem mais mensagens assim.

Tabela completa e F1 por categoria em `results/resultados.md`.

## 8. Conferência de atraso
`src/triagem/verdade.py` confere, com as datas reais de entrega da Olist, quantas mensagens classificadas como atraso são de pedidos de fato atrasados ou não entregues. Precisa de `data/raw/olist_orders_dataset.csv`, da mesma base pública no Kaggle. **Ainda não rodou:** o arquivo não está no repositório.

## 9. Limitações
- **Sem conjunto de desenvolvimento rotulado à mão.** A precisão das regras foi julgada lendo amostras, e o acerto real só apareceu na avaliação final.
- **O conjunto de teste tem 247 rótulos feitos pelo Claude.** A coluna "53 do Mateus" é a medida mais honesta, mas é pequena.
- **O modelo aprende os erros das regras.** A validação cruzada (82,9%) mede só concordância com elas.
- **Uma categoria por mensagem.** Reclamações com dois problemas ("não chegou e quero o dinheiro") ficam com a de origem.

## 10. O que ficou de fora
- **Uma ferramenta para usar a triagem** (página ou app). É o próximo passo.
- Multirrótulo.
- Embeddings e modelos pré-treinados grandes.

## 11. Quem fez o quê
- **Mateus:** a escolha da abordagem (supervisão fraca, sem LLM), as categorias e os 53 rótulos do conjunto de teste.
- **Claude (Anthropic), como apoio no código:** escreveu as regras lendo o pool de treino, o pipeline e esta documentação. As regras ficam legíveis em `src/triagem/regras.py` para revisão.
