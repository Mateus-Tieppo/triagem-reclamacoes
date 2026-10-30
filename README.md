# Triagem de reclamações sem LLM

[![Testes](https://github.com/Mateus-Tieppo/triagem-reclamacoes/actions/workflows/testes.yml/badge.svg)](https://github.com/Mateus-Tieppo/triagem-reclamacoes/actions/workflows/testes.yml)

Quando um cliente reclama, alguém precisa ler a mensagem e mandar para o time certo: logística, estoque, financeiro ou atendimento. Este projeto automatiza essa triagem em português **sem LLM e sem custo**: regras legíveis rotulam as reclamações, um modelo clássico aprende com elas e o que fica incerto vai para revisão humana.

- **Custo zero:** roda num notebook, sem API, sem GPU e sem LLM, em cerca de 1 milissegundo por mensagem.
- **Explicável:** cada decisão diz qual regra disparou e quais palavras pesaram.
- **Humano na dúvida:** a mensagem incerta não é classificada no chute, vai para uma fila de revisão com o motivo.

As decisões, com os porquês e o que ficou de fora, estão em [DECISOES.md](DECISOES.md).

## Como funciona

1. **Normalização** (`normalizar.py`): minúsculas, sem acentos, links e números viram marcadores, "péssimooooo" vira "pessimo". A mesma função roda nas regras, no treino e na predição.
2. **Regras legíveis** (`regras.py`): 43 expressões como "não recebi", "só veio um", "veio quebrado" e "estorno", cada uma votando numa categoria. Elas rotulam 72,9% das 10.453 reclamações de treino.
3. **Modelo** (`modelo.py`): TF-IDF + regressão logística, treinado só com os rótulos das regras. Ele cobre as mensagens que nenhuma regra pega e dá a certeza de cada resposta.
4. **Decisão final** (`triagem.py`): quando uma regra dispara, vale a regra; senão, o modelo. Vai para revisão quando regra e modelo discordam, quando duas regras se contradizem ou quando a certeza do modelo fica abaixo de 0,80.

A saída é `results/triagem.csv`: uma linha por reclamação com categoria, origem (regra ou modelo), certeza, se vai para revisão, o motivo e as palavras que pesaram.

## Resultados

Conjunto de teste de 300 reclamações, que só foi lido na avaliação final. F1 macro com intervalo de 95% por bootstrap.

| Abordagem | F1 macro | F1 nas 53 rotuladas por mim | Revisão | F1 sem revisão | Latência |
| --- | --- | --- | --- | --- | --- |
| Regras sozinhas | 50,8% (44,3% a 56,9%) | 36,3% | - | - | < 1 ms |
| Regressão logística sozinha | **57,3%** (50,4% a 63,3%) | 42,2% | - | - | < 1 ms |
| Sistema completo (regras + modelo + revisão) | 54,8% (47,9% a 61,0%) | **44,9%** | 32,3% | **67,7%** | 1 ms |

1. **O modelo aprende além das regras.** Treinado só com os rótulos delas, ganha das regras sozinhas em 6,5 pontos de F1.
2. **A fila de revisão concentra os casos difíceis.** Nas mensagens que o sistema decide sozinho, o F1 chega a 67,7%. Em troca, cerca de um terço das mensagens vai para um humano.
3. **O sistema completo ficou abaixo do modelo sozinho no F1 geral**, porque quando uma regra dispara ela decide, e as regras erram mais que o modelo. A regra de decisão foi fixada antes de olhar o teste, e não mudei depois para não escolher olhando o resultado.
4. **O ponto fraco é a categoria `outro`** (elogio com nota baixa, texto sem sentido), que quase nenhuma regra cobre.

Tabela completa e F1 por categoria em [`results/resultados.md`](results/resultados.md); matrizes de confusão em `results/`.

### Comparação com LLM

Antes de chegar aqui, testei LLMs locais no [Ollama](https://ollama.com) no mesmo conjunto de teste:

| Abordagem | F1 macro | F1 nas 53 rotuladas por mim | Latência |
| --- | --- | --- | --- |
| Qwen 2.5 7B, zero-shot | 74,9% (67,8% a 80,7%) | 60,5% | 1.041 ms |
| TF-IDF + SVM treinado com rótulos do Qwen | 61,4% (54,1% a 68,0%) | 45,2% | < 1 ms |
| Llama 3.2 3B, zero-shot | 61,5% (55,1% a 67,3%) | 51,9% | 359 ms |

O Qwen é bem melhor, mas leva cerca de um segundo por mensagem e precisa de um computador capaz de rodar um modelo de 7 bilhões de parâmetros. Sem LLM, a perda é de cerca de 20 pontos de F1 em troca de custo e latência quase zero e de rótulos que qualquer pessoa consegue ler e corrigir.

### Limitações

- **Sem conjunto de desenvolvimento rotulado à mão.** As regras foram julgadas lendo amostras do treino; o acerto real só aparece no teste.
- **Rótulos de teste.** 247 das 300 mensagens de teste foram rotuladas pelo Claude (Anthropic) com as mesmas regras de rotulagem, sem ver os meus rótulos. A coluna "53 rotuladas por mim" é a medida mais honesta, mas tem amostra pequena. Nas 53 em comum, eu e o Claude concordamos em 64% (kappa de Cohen 0,56).
- **O modelo aprende os erros das regras.** Por isso a validação cruzada (82,8%) mede só concordância com as regras.
- **Domínio.** Os dados são de e-commerce de 2016 a 2018. Outros tipos de entrega podem ter vocabulário e categorias diferentes.

## Dados

Avaliações públicas do [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (licença CC BY-NC-SA 4.0).

- 100.000 avaliações no total; 15.093 com nota 1 ou 2.
- Depois de exigir comentário com pelo menos 15 caracteres e tirar duplicatas: **10.767 reclamações**.
- **Teste**: 300 reclamações sorteadas (`random_state=42`), em `data/ouro.csv`. Rotulei 53 à mão.
- **Treino**: as outras 10.453, sem rótulo humano; as regras rotulam.

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

Precisa de Python 3.9+. Os comandos criam um ambiente virtual em `.venv` sozinhos. Não precisa de Ollama.

```bash
make tudo       # testes, regras, treino, triagem e avaliação

make testes
make regras     # aplica as regras e gera results/regras.md
make triagem    # treina o modelo e gera results/triagem.csv
make avaliar    # gera results/resultados.md e as matrizes de confusão
```

A comparação com LLM fica fora do `make tudo`: `make modelos`, `make llm`, `make prata` e `make baseline` precisam do Ollama aberto.

## Estrutura

```
src/triagem/
  normalizar.py  limpeza do texto
  regras.py      regras legíveis e combinação dos votos
  modelo.py      TF-IDF + regressão logística e explicação por palavras
  triagem.py     decisão final, limiar e fila de revisão
  verdade.py     conferência de atraso com as datas reais de entrega
  avaliar.py     métricas, intervalos, matrizes e tabela final
  taxonomia.py   categorias e regras de rotulagem
  dados.py       filtro das reclamações e montagem dos conjuntos
  llm.py, rodar_llm.py, prompts.py, baseline.py   comparação com LLM
tests/           testes do pipeline, sem chamar nenhuma API
```

## Licença

Código sob a licença MIT (veja `LICENSE`). Os dados em `data/` derivam da base da Olist e seguem a licença CC BY-NC-SA 4.0.

## Ferramentas

Python, pandas, scikit-learn e Matplotlib. O Claude (Anthropic) foi usado como apoio no código, para escrever as regras a partir de amostras do treino e para rotular 247 das 300 mensagens de teste, como descrito acima.
