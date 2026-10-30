"""Categorias da triagem. Um rótulo principal por mensagem."""

CATEGORIAS: dict[str, str] = {
    "sem_estoque": "A loja vendeu, anunciou ou cancelou por não ter o produto.",
    "nao_recebido_atraso": "Problema de entrega: não chegou, atrasou, endereço errado, não entregou em casa, devolvido.",
    "item_faltando": "Chegou só parte do pedido: faltou um ou mais itens ou unidades.",
    "produto_errado": "Diferente do pedido ou do anúncio (cor, modelo, voltagem, tamanho), anúncio omisso, caixa vazia, falsificado.",
    "defeito_qualidade": "Chegou o produto certo, mas quebrado, com defeito, ruim ou abaixo do esperado.",
    "atendimento_loja": "A queixa é só sobre falta de resposta, suporte ou atendimento da loja.",
    "cobranca_cancelamento": "O assunto é só dinheiro: cobrança indevida, estorno ou reembolso não feito, cancelamento.",
    "outro": "Genérica sem dizer o problema, só pedir o dinheiro de volta, engano do consumidor, elogio com nota baixa ou texto sem sentido.",
}

ROTULOS: list[str] = list(CATEGORIAS)

# Guia v4.1, calibrado entre o Mateus e o Claude (ver docs/guia-rotulagem.md).
REGRAS = """\
- Mais de um problema, uma regra só (origem): a principal é o primeiro na ordem sem_estoque, nao_recebido_atraso, item_faltando, produto_errado, defeito_qualidade.
- Comentário leve ("um pouco demorada", "frete caro") nunca vence um problema concreto.
- atendimento_loja e cobranca_cancelamento são consequências: só são o rótulo quando são o único problema citado.
- Comentário de lentidão, quando é a única queixa, é nao_recebido_atraso.
- Engano do consumidor sem diferença real ("é da Dell e veio feito na China") é outro.
"""

# Guia entregue a quem rotula: as definições, as regras acima e o bloco
# "Regras de rotulagem" da página usada para rotular o ouro.
GUIA_ROTULAGEM = (
    "Categorias:\n"
    + "\n".join(f"- {k}: {v}" for k, v in CATEGORIAS.items())
    + "\n\nRegras:\n"
    + REGRAS
    + "- Se ficar em dúvida entre duas, escolha a melhor e marque dúvida.\n"
)
