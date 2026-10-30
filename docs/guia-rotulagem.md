# Guia de rotulagem (versão 4.1)

Uma categoria principal por mensagem e, quando houver um segundo problema, uma secundária. O guia foi calibrado em três rodadas entre o Mateus e o Claude sobre mensagens do treino (nunca do teste). Na última rodada, com mensagens que ninguém tinha visto, a concordância na principal foi de 75% (kappa 0,69) e de 90% contando a secundária.

## Categorias

| Categoria | Quando usar |
| --- | --- |
| `sem_estoque` | A loja vendeu, anunciou ou cancelou por não ter o produto. |
| `nao_recebido_atraso` | Problema de entrega: não chegou, atrasou, endereço errado, não entregou em casa, devolvido; comentário de lentidão quando é a única queixa. |
| `item_faltando` | Chegou parte do pedido, ou um item específico do pedido não veio. |
| `produto_errado` | Diferente do pedido ou do anúncio (cor, modelo, voltagem, tamanho), anúncio omisso ou incompleto, caixa vazia, falsificado ou não original. |
| `defeito_qualidade` | Chegou o certo, mas quebrado, com defeito, ruim ou abaixo do esperado; inclui cheiro ruim. |
| `atendimento_loja` | Falta de resposta, suporte ou atendimento, quando é o único problema citado. |
| `cobranca_cancelamento` | Estorno, reembolso, cobrança indevida ou cancelamento, quando é o único problema citado. |
| `outro` | Genérica sem dizer o problema; só pedir o dinheiro de volta sem dizer o problema; engano do consumidor sem diferença real ("é da Dell e veio feito na China"); elogio com nota baixa; texto sem sentido. |

## Regras

1. **Mais de um problema, uma regra só (origem):** a principal é o primeiro na ordem `sem_estoque`, `nao_recebido_atraso`, `item_faltando`, `produto_errado`, `defeito_qualidade`. O segundo vai como secundária.
2. **Comentário leve** ("um pouco demorada", "frete caro") nunca vence um problema concreto.
3. **Atendimento e cobrança são consequências:** só são principal quando são o único problema citado.
4. Na dúvida entre duas, escolher a melhor e marcar dúvida.

## Histórico da calibração

| Rodada | Guia | Mensagens | Principal | Kappa | Contando a secundária |
| --- | --- | --- | --- | --- | --- |
| Antes | 7 categorias, sem regra de desempate | 12 difíceis | 33% | | |
| 1 | v2: ordem da entrega, sem estoque | 40 | 72,5% | 0,68 | 82,5% |
| 2 | v3: exceções (consequência vence com sem estoque; defeito vence produto errado) | 20 | 50,0% | 0,42 | 80,0% |
| 3 | v4: volta à regra única da origem | 20 | 75,0% | 0,69 | 90,0% |

A rodada 2 mostrou que as exceções escolhidas em tese contradiziam o jeito como o Mateus rotula na prática; a v4 voltou à regra única. A regra 2 (comentário leve) entrou depois da rodada 3, a partir de uma das divergências, e por isso não tem medida própria.
