# Triagem de reclamações com ML clássico

[![Testes](https://github.com/Mateus-Tieppo/triagem-reclamacoes/actions/workflows/testes.yml/badge.svg)](https://github.com/Mateus-Tieppo/triagem-reclamacoes/actions/workflows/testes.yml)

Quando um cliente reclama, alguém precisa ler a mensagem e mandar para o time certo: logística, estoque, financeiro ou atendimento. Este projeto automatiza essa triagem em português com um modelo clássico que roda num notebook, **sem LLM na triagem e sem custo por mensagem**.

- **Acerta tanto quanto um LLM:** nas 53 mensagens de teste que eu rotulei, o modelo clássico acerta 75,5%, igual ao Qwen 2.5 7B, mas em menos de 1 milissegundo, contra cerca de 1 segundo.
- **Custo zero na triagem:** sem API, sem GPU e sem LLM.
- **Humano na dúvida:** a mensagem incerta vai para uma fila de revisão. Nas que o modelo decide sozinho, ele acerta 90,3%.
- **Guia de rotulagem calibrado:** eu e o Claude rotulamos as mesmas mensagens às cegas, em três rodadas, até o guia deixar pouca margem para interpretação.

As decisões, com os porquês e o que ficou de fora, estão em [DECISOES.md](DECISOES.md); o guia, em [docs/guia-rotulagem.md](docs/guia-rotulagem.md).

## O que mais pesou: os rótulos, não o algoritmo

Na primeira versão, eu e o Claude concordávamos em só 64% das mensagens. O modelo aprendia o jeito do Claude rotular e era cobrado pelo meu, então trocar de algoritmo não resolvia. Reescrevemos o guia de rotulagem em três rodadas de calibração, sempre com mensagens do treino:

| Rodada | Mudança no guia | Concordância | Kappa |
| --- | --- | --- | --- |
| Antes | 7 categorias, sem regra de desempate | 33% nas difíceis | |
| 1 | categoria nova `sem_estoque` e ordem de desempate | 72,5% | 0,68 |
| 2 | exceções que pareciam boas em tese | 50,0% | 0,42 |
| 3 | uma regra só: vale a origem do problema | 75,0% | 0,69 |

A rodada 2 piorou, e foi a que mais ensinou: as regras que eu escolhi no papel contradiziam o jeito como eu rotulava na prática. Contando a categoria secundária, na rodada 3 concordamos em 90% das mensagens.

## Como funciona

1. **Rotulagem (uma vez):** 3.000 reclamações do treino rotuladas pelo Claude com o guia calibrado. Parte delas fica separada como conjunto de desenvolvimento.
2. **Variáveis:** TF-IDF de palavras e de caracteres sobre o texto normalizado, mais 44 regras legíveis ("não recebi", "só veio um", "sem estoque", "estorno") como colunas 0/1.
3. **Modelo:** comparei regressão logística, SVM linear e Naive Bayes no desenvolvimento; venceu a regressão logística (73,8% de F1 macro no desenvolvimento).
4. **Decisão:** o modelo decide e dá a certeza. Abaixo de 0,80 de certeza, ou sem texto, a mensagem vai para revisão.

A saída é `results/triagem.csv`: uma linha por reclamação com categoria, certeza, se vai para revisão, o motivo e as palavras que mais pesaram.

## Resultados

Conjunto de teste de 300 reclamações, lido só na avaliação final. Os LLMs rodaram com o mesmo guia no prompt.

| Abordagem | Acurácia nas 53 rotuladas por mim | F1 macro nas 53 | Acurácia nas 300 | F1 macro nas 300 | Latência |
| --- | --- | --- | --- | --- | --- |
| **ML clássico (este projeto)** | **75,5%** | 50,7% | **82,3%** | 65,7% (56,6% a 73,4%) | **< 1 ms** |
| Qwen 2.5 7B zero-shot (LLM local) | **75,5%** | **56,0%** | 81,3% | **72,9%** (65,8% a 79,1%) | 1.123 ms |
| Llama 3.2 3B zero-shot (LLM local) | 58,5% | 38,0% | 66,0% | 52,9% (45,3% a 60,1%) | 517 ms |

1. **Na acurácia, empata com o Qwen** e passa do Llama, rodando mais de mil vezes mais rápido.
2. **No F1 macro, o Qwen ainda ganha.** Essa métrica dá o mesmo peso a cada categoria, e o Qwen vai melhor nas pequenas (`sem_estoque`, `atendimento_loja`, `outro`), que têm poucos exemplos.
3. **A fila de revisão é pequena e confiável:** no teste, o modelo decide sozinho 72% das mensagens e acerta 90,3% delas.
4. **Nas 53 rotuladas por mim, as versões do projeto ficam próximas.** Medidas no mesmo gabarito, a versão só com regras faz 52,1% de F1 e 75,5% de acurácia, e esta, 50,7% e 75,5%. Com 53 mensagens, essas diferenças estão dentro do ruído. Onde o modelo novo se separa é nas 300: 82,3% de acurácia contra 71,3% da versão só com regras.

Na prática: o modelo clássico resolve sozinho quase três quartos das reclamações com acerto alto, a custo zero, e manda o resto para uma pessoa. O Qwen é um pouco melhor nas categorias raras, mas precisa de um computador que rode um modelo de 7 bilhões de parâmetros.

Tabela completa e F1 por categoria em [`results/resultados.md`](results/resultados.md); a escolha do modelo em [`results/desenvolvimento.md`](results/desenvolvimento.md).

### Limitações

- **Mesmo rotulador no treino e no teste.** O Claude rotulou o treino e 247 das 300 mensagens de teste. Por isso a régua principal são as 53 rotuladas por mim, que são poucas: a diferença de F1 para o Qwen tem intervalo largo.
- **Concordância humana de 75%.** É o teto realista: nem duas pessoas concordam sempre sobre qual é o problema principal.
- **Categorias pequenas** têm poucos exemplos no treino e no teste.
- **Domínio.** Os dados são de e-commerce de 2016 a 2018. Outros tipos de entrega podem ter vocabulário e categorias diferentes.

## Dados

Avaliações públicas do [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (licença CC BY-NC-SA 4.0).

- 100.000 avaliações no total; 15.093 com nota 1 ou 2.
- Depois de exigir comentário com pelo menos 15 caracteres e tirar duplicatas: **10.767 reclamações**.
- **Teste**: 300 reclamações sorteadas (`random_state=42`), em `data/ouro.csv`. Rotulei 53 à mão (e revisei no guia calibrado); as outras 247 foram rotuladas pelo Claude.
- **Treino e desenvolvimento**: 3.000 das outras 10.453, rotuladas pelo Claude, em `data/rotulos_claude.csv`.

## Categorias

| Categoria | Quando usar |
| --- | --- |
| `sem_estoque` | A loja vendeu, anunciou ou cancelou por não ter o produto |
| `nao_recebido_atraso` | Problema de entrega: não chegou, atrasou, endereço errado, não entregou em casa |
| `item_faltando` | Chegou só parte do pedido |
| `produto_errado` | Diferente do pedido ou do anúncio, anúncio incompleto, caixa vazia, falsificado |
| `defeito_qualidade` | Chegou o produto certo, mas quebrado, ruim ou abaixo do esperado |
| `atendimento_loja` | A queixa é só sobre falta de resposta ou suporte |
| `cobranca_cancelamento` | A queixa é só sobre estorno, reembolso, cobrança indevida ou cancelamento |
| `outro` | Genérica, só pedir o dinheiro de volta, engano do consumidor, elogio com nota baixa ou texto sem sentido |

Regra principal: quando há mais de um problema, vale o primeiro na ordem sem estoque, entrega, item faltando, produto errado, defeito. "Não chegou e a loja não responde" é `nao_recebido_atraso`, porque a falta de resposta é consequência.

## Como rodar

Precisa de Python 3.9+. Os comandos criam um ambiente virtual em `.venv` sozinhos. Não precisa de Ollama nem de acesso ao Claude: os rótulos já estão no repositório.

```bash
make tudo        # testes, regras, supervisão fraca, treino e avaliação

make testes
make treinar     # compara os modelos no desenvolvimento e gera results/triagem.csv
make avaliar     # gera results/resultados.md e as matrizes de confusão
```

`make selecionar` refaz a escolha das mensagens para rotular (só faz sentido antes de uma nova rotulagem). A comparação com LLM (`make modelos`, `make llm`, `make prata`, `make baseline`) precisa do Ollama aberto.

## Estrutura

```
src/triagem/
  normalizar.py       limpeza do texto
  regras.py           regras legíveis (variáveis do modelo)
  selecao.py          escolha das mensagens para rotular
  rotulagem.py        lotes e checagem dos rótulos do Claude
  modelo.py           TF-IDF, regras como variáveis e os modelos candidatos
  desenvolvimento.py  escolha do modelo, fila e predições no teste
  triagem.py          decisão, limiar e a supervisão fraca (versão anterior)
  avaliar.py          métricas, intervalos, matrizes e tabela final
  taxonomia.py        categorias e guia de rotulagem
  dados.py            filtro das reclamações e montagem dos conjuntos
  llm.py, rodar_llm.py, prompts.py, baseline.py, verdade.py   comparação com LLM e conferências
tests/                testes do pipeline, sem chamar nenhuma API
```

## Licença

Código sob a licença MIT (veja `LICENSE`). Os dados em `data/` derivam da base da Olist e seguem a licença CC BY-NC-SA 4.0.

## Ferramentas

Python, pandas, scikit-learn e Matplotlib. O Claude (Anthropic) foi usado como apoio no código, para escrever as regras a partir de amostras do treino e para rotular o treino e 247 das 300 mensagens de teste, como descrito acima.
