# Triagem de reclamações com LLM

Quando um cliente reclama, alguém precisa ler a mensagem e mandar para o time certo: logística, estoque, financeiro ou atendimento. Este projeto mede quão bem dá para automatizar essa triagem em português usando só modelos que rodam no próprio computador, sem API paga.

Comparo três abordagens no mesmo conjunto de teste de 300 mensagens:

1. **LLM zero-shot**: só a descrição das categorias no prompt.
2. **LLM few-shot**: a mesma descrição e 14 exemplos rotulados (2 por categoria).
3. **TF-IDF + SVM**: modelo clássico treinado com rótulos gerados pelo LLM local em outras 2.000 mensagens.

Os LLMs rodam no [Ollama](https://ollama.com): um modelo de 3 bilhões de parâmetros (Llama 3.2) e um de 7 bilhões (Qwen 2.5). A pergunta é prática: o ganho de qualidade do LLM compensa a latência e o hardware, ou um modelo clássico de poucos milissegundos resolve?

## Dados

Avaliações públicas do [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (licença CC BY-NC-SA 4.0). São pedidos de e-commerce, não de comida, mas os problemas são os mesmos de qualquer entrega: atraso, item faltando, pedido errado, produto avariado e cobrança.

- 100.000 avaliações no total; 15.093 com nota 1 ou 2.
- Depois de exigir comentário com pelo menos 15 caracteres e tirar duplicatas: **10.767 reclamações**.
- **Conjunto ouro**: 300 reclamações sorteadas (`random_state=42`). Rotulei 53 à mão; as outras 247 foram rotuladas pelo Claude (Anthropic) com as mesmas regras, sem ver os meus rótulos. As que geraram dúvida entre duas categorias ficaram marcadas, e a tabela mostra o resultado com e sem elas, e também só nas 53 rotuladas por mim.
- **Concordância entre rotuladores**: nas 53 em comum, eu e o Claude concordamos em 64% (kappa de Cohen 0,56, concordância moderada). As divergências se concentram em mensagens com mais de um problema, como "não chegou e quero o dinheiro de volta". Isso dá uma ideia do teto: nem dois rotuladores concordam sempre nessa tarefa.
- **Exemplos do few-shot**: 14 mensagens fora do conjunto ouro (`data/fewshot.csv`).
- **Conjunto prata**: 2.000 mensagens fora do ouro e do few-shot, rotuladas pelo Qwen 2.5 7B em few-shot, usadas só para treinar o SVM.

## Categorias

| Categoria | Quando usar |
| --- | --- |
| `nao_recebido_atraso` | Ainda não recebeu nada do pedido, ou recebeu fora do prazo |
| `item_faltando` | Chegou só parte do pedido |
| `produto_errado` | Outro produto, modelo, cor ou tamanho, ou diferente do anúncio |
| `defeito_qualidade` | Chegou o produto certo, mas quebrado ou ruim |
| `atendimento_loja` | A queixa é só sobre falta de resposta ou suporte |
| `cobranca_cancelamento` | Estorno, reembolso, cobrança indevida, cancelamento |
| `outro` | Elogio com nota baixa, texto sem sentido ou o que não se encaixa |

Regra principal: o rótulo é o problema que originou a reclamação. "Não chegou e a loja não responde" é `nao_recebido_atraso`, porque a falta de resposta é consequência.

## Resultados

Conjunto ouro, 300 mensagens. F1 macro com intervalo de 95% por bootstrap. Latência medida no meu MacBook Air.

| Abordagem | Acurácia | F1 macro | F1 nas 53 rotuladas por mim | Latência por mensagem |
| --- | --- | --- | --- | --- |
| Qwen 2.5 7B, zero-shot | **82,7%** | **74,9%** (67,8% a 80,7%) | **60,5%** | 1.041 ms |
| Qwen 2.5 7B, few-shot | 82,7% | 74,1% (67,4% a 80,0%) | 53,1% | 1.076 ms |
| Llama 3.2 3B, zero-shot | 68,3% | 61,5% (55,1% a 67,3%) | 51,9% | 359 ms |
| TF-IDF + SVM | 73,3% | 61,4% (54,1% a 68,0%) | 45,2% | < 1 ms |
| Llama 3.2 3B, few-shot | 57,0% | 52,7% (47,0% a 58,6%) | 43,4% | 394 ms |

Nenhum modelo devolveu resposta fora do formato pedido. A tabela completa, com F1 por categoria, está em [`results/resultados.md`](results/resultados.md), e as matrizes de confusão em `results/`.

### O que os números mostram

1. **O modelo maior vale o custo.** O Qwen 7B ganha 13 pontos de F1 sobre o Llama 3B, e os intervalos de confiança não se sobrepõem. Em troca, leva quase 3 vezes mais tempo por mensagem.
2. **Os exemplos no prompt não ajudaram.** No Qwen o few-shot empatou com o zero-shot. No Llama piorou 9 pontos: o modelo pequeno acertou só 41% das mensagens de atraso, contra 70% no zero-shot, o que sugere que ele imita a forma dos exemplos em vez de seguir as regras.
3. **O SVM aprende bem as categorias grandes.** Em `item_faltando` (86%) e `nao_recebido_atraso` (83%) ele fica perto do Qwen, rodando mais de mil vezes mais rápido. Ele erra mais nas categorias pequenas, como `atendimento_loja` (33%) e `outro` (29%), que têm poucos exemplos no treino.
4. **As categorias difíceis são as que dependem de interpretação.** Todas as abordagens vão mal em `atendimento_loja` e `cobranca_cancelamento`, que quase sempre aparecem junto com outro problema. Foi também onde eu e o Claude mais divergimos ao rotular.

Na prática, um sistema razoável seria usar o SVM como primeira passada e mandar para o Qwen só as mensagens em que ele estiver inseguro. Testar isso é o próximo passo.

### Limitações

- **Rótulos de teste.** 247 das 300 mensagens foram rotuladas por um LLM. Nas mensagens rotuladas pelo Claude, o Qwen zero-shot acerta 85,8%; nas 53 rotuladas por mim, 67,9%. Parte do desempenho, então, vem de os modelos concordarem com o jeito de um LLM rotular. A coluna "F1 nas 53 rotuladas por mim" é a medida mais honesta, mas tem amostra pequena.
- **Teto da tarefa.** Eu e o Claude concordamos em 64% (kappa 0,56). Um modelo perto desse nível está no limite do que dá para medir com uma categoria só por mensagem. Multirrótulo seria mais realista.
- **Domínio.** Os dados são de e-commerce de 2016 a 2018, não de delivery de comida.
- **O SVM aprende com o Qwen.** Por isso ele dificilmente passaria o Qwen; o que importa nele é quanto da qualidade se mantém com latência quase zero.

## Como avaliei

- **F1 macro** é a métrica principal, porque as categorias têm tamanhos bem diferentes e a acurácia esconde erro nas pequenas. Ele vem com intervalo de 95% por bootstrap (1.000 reamostragens do conjunto ouro).
- **Respostas inválidas** (o modelo não devolveu uma categoria válida) aparecem numa coluna própria e contam como `outro`, que é o que um sistema em produção faria.
- **Latência** é a mediana por mensagem, medida no meu MacBook Air.
- **Custo**: zero por chamada em todas as abordagens, porque tudo roda localmente.
- O conjunto ouro nunca é usado para escolher prompt, exemplos ou hiperparâmetros.

## Como rodar

Precisa de Python 3.9+ e do [Ollama](https://ollama.com) aberto. Os comandos criam um ambiente virtual em `.venv` sozinhos.

```bash
make tudo       # faz tudo abaixo em sequência

make testes

make modelos    # baixa llama3.2:3b e qwen2.5:7b
make llm        # zero-shot e few-shot dos dois modelos no conjunto ouro
make prata      # rotula 2.000 mensagens para treinar o SVM
make baseline   # treina e avalia TF-IDF + SVM
make avaliar    # gera results/resultados.md e as matrizes de confusão
```

As predições ficam em `results/preds/`, uma linha por mensagem com rótulo, tokens e latência. Se a execução parar no meio, rodar de novo continua de onde parou.

## Estrutura

```
src/triagem/
  taxonomia.py   categorias e regras de rotulagem
  dados.py       filtro das reclamações e montagem dos conjuntos
  prompts.py     prompt de sistema e montagem do few-shot
  llm.py         cliente do Ollama (API HTTP local)
  rodar_llm.py   roda um modelo em um conjunto e grava as predições
  baseline.py    TF-IDF (palavras e caracteres) + SVM linear
  avaliar.py     métricas, intervalos, matrizes e tabela final
data/
  fewshot.csv    exemplos do few-shot
  ouro.csv       conjunto de teste (coluna fonte diz quem rotulou)
tests/           testes do pipeline sem chamar nenhuma API
```

## Ferramentas

Python, pandas, scikit-learn, Ollama e Matplotlib. O Claude (Anthropic) foi usado como apoio no código, na página de rotulagem e para rotular 247 das 300 mensagens do conjunto ouro, como descrito acima.
