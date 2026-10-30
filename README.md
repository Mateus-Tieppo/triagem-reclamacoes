# Triagem de reclamações com ML clássico

[![Testes](https://github.com/Mateus-Tieppo/triagem-reclamacoes/actions/workflows/testes.yml/badge.svg)](https://github.com/Mateus-Tieppo/triagem-reclamacoes/actions/workflows/testes.yml)

Quando um cliente reclama, alguém precisa ler a mensagem e mandar para o time certo: logística, estoque, financeiro ou atendimento. Este projeto automatiza essa triagem em português com um modelo clássico que roda num notebook, **sem LLM na triagem e sem custo por mensagem**.

- **Custo zero na triagem:** sem API, sem GPU e sem LLM, em cerca de 2 milissegundos por mensagem.
- **Humano na dúvida:** a mensagem incerta vai para uma fila de revisão. Nas que o modelo decide sozinho, ele acerta 91,3%.
- **Rótulos de treino feitos uma vez pelo Claude (Anthropic).** A LLM entra só no desenvolvimento, para rotular 3.000 mensagens; a triagem não depende dela.

As decisões, com os porquês e o que ficou de fora, estão em [DECISOES.md](DECISOES.md).

## Como funciona

1. **Rotulagem (uma vez):** 3.000 reclamações do treino rotuladas pelo Claude com o mesmo guia usado no conjunto de teste. 500 delas ficam separadas como conjunto de desenvolvimento.
2. **Variáveis:** TF-IDF de palavras e de caracteres sobre o texto normalizado, mais 43 regras legíveis ("não recebi", "só veio um", "veio quebrado", "estorno") como colunas 0/1.
3. **Modelo:** comparei SVM linear, regressão logística e Naive Bayes no desenvolvimento; venceu o SVM linear calibrado (71,0% de F1 macro no desenvolvimento).
4. **Decisão:** o modelo decide e dá a certeza. Abaixo de 0,80 de certeza, ou sem texto, a mensagem vai para revisão.

A saída é `results/triagem.csv`: uma linha por reclamação com categoria, certeza, se vai para revisão, o motivo e as palavras que mais pesaram.

## Resultados

Conjunto de teste de 300 reclamações, lido só na avaliação final. F1 macro com intervalo de 95% por bootstrap.

| Abordagem | F1 macro | F1 nas 53 rotuladas por mim | Latência |
| --- | --- | --- | --- |
| Qwen 2.5 7B zero-shot (LLM local) | 74,9% (67,8% a 80,7%) | **60,5%** | 1.041 ms |
| **ML clássico com rótulos do Claude** | **63,2%** (55,2% a 70,4%) | 45,4% | 2 ms |
| Supervisão fraca, só regras (versão anterior) | 54,9% (47,9% a 61,1%) | 44,9% | 1 ms |

1. **O Qwen continua na frente.** Nas 53 mensagens rotuladas por mim, a comparação mais honesta, ele faz 60,5% contra 45,4%.
2. **O modelo clássico melhorou de 54,9% para 63,2%** com os rótulos do Claude. Parte desse ganho vem de 247 das 300 mensagens de teste também terem sido rotuladas pelo Claude; nas 53 rotuladas por mim o ganho foi pequeno.
3. **A fila de revisão separa bem o fácil do difícil.** Metade das mensagens de teste vai para revisão; nas que o modelo decide sozinho, ele acerta 91,3%, contra 65,3% nas que vão para um humano.
4. **O ponto fraco são as categorias pequenas:** `atendimento_loja`, `outro` e `cobranca_cancelamento`.

Na prática: o modelo clássico resolve sozinho metade das reclamações com acerto alto, a custo zero, e manda o resto para uma pessoa. O Qwen classifica melhor, mas precisa de um computador que rode um modelo de 7 bilhões de parâmetros e leva cerca de um segundo por mensagem.

Tabela completa, F1 por categoria e as versões anteriores em [`results/resultados.md`](results/resultados.md); a escolha do modelo em [`results/desenvolvimento.md`](results/desenvolvimento.md).

### Limitações

- **Mesmo rotulador no treino e no teste.** O Claude rotulou o treino e 247 das 300 mensagens de teste. Por isso a coluna "53 rotuladas por mim" é a régua principal, mas tem amostra pequena. Nas 53 em comum, eu e o Claude concordamos em 64% (kappa de Cohen 0,56).
- **Autoconsistência não é acerto.** Rotulando 200 mensagens duas vezes, o Claude concordou com ele mesmo em 98%.
- **Categorias pequenas** têm poucos exemplos no treino e no desenvolvimento.
- **Domínio.** Os dados são de e-commerce de 2016 a 2018. Outros tipos de entrega podem ter vocabulário e categorias diferentes.

## Dados

Avaliações públicas do [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (licença CC BY-NC-SA 4.0).

- 100.000 avaliações no total; 15.093 com nota 1 ou 2.
- Depois de exigir comentário com pelo menos 15 caracteres e tirar duplicatas: **10.767 reclamações**.
- **Teste**: 300 reclamações sorteadas (`random_state=42`), em `data/ouro.csv`. Rotulei 53 à mão; as outras 247 foram rotuladas pelo Claude.
- **Treino e desenvolvimento**: 3.000 das outras 10.453, rotuladas pelo Claude, em `data/rotulos_claude.csv`.

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

Python, pandas, scikit-learn e Matplotlib. O Claude (Anthropic) foi usado como apoio no código e para rotular o treino e 247 das 300 mensagens de teste, como descrito acima.
