"""Categorias da triagem. Um rótulo principal por mensagem."""

CATEGORIAS: dict[str, str] = {
    "nao_recebido_atraso": "A pessoa ainda não recebeu nada do pedido, ou recebeu fora do prazo.",
    "item_faltando": "Chegou só parte do pedido: faltou um ou mais itens ou unidades.",
    "produto_errado": "Chegou outro produto, modelo, cor ou tamanho, ou o produto é diferente do anúncio.",
    "defeito_qualidade": "Chegou o produto certo, mas quebrado, danificado, com defeito ou de qualidade ruim.",
    "atendimento_loja": "A queixa é só sobre falta de resposta, suporte ou atendimento da loja.",
    "cobranca_cancelamento": "O assunto é dinheiro: cobrança indevida, estorno ou reembolso não feito, cancelamento.",
    "outro": "Elogio com nota baixa, texto sem sentido ou algo que não se encaixa nas outras.",
}

ROTULOS: list[str] = list(CATEGORIAS)

REGRAS = """\
- Escolha o problema que originou a reclamação. Consequências (loja não responde, pedi reembolso) só viram o rótulo quando são o único problema citado.
- Se a pessoa não recebeu nada daquele pedido, use nao_recebido_atraso. Se recebeu parte, use item_faltando.
- produto_errado inclui modelo, cor ou tamanho diferente do pedido e produto diferente do anúncio.
- defeito_qualidade é quando chegou o produto certo, mas com problema.
"""

# Guia entregue a quem rotula: as definições, as regras acima e o bloco
# "Regras de rotulagem" da página usada para rotular o ouro.
GUIA_ROTULAGEM = (
    "Categorias:\n"
    + "\n".join(f"- {k}: {v}" for k, v in CATEGORIAS.items())
    + "\n\nRegras:\n"
    + REGRAS
    + """- Escolha o problema que originou a reclamação. Consequências (loja não responde, pedi reembolso) só viram o rótulo quando são o único problema citado.
- nao_recebido_atraso vence quando a pessoa ainda não recebeu nada daquele pedido. Se recebeu parte, é item_faltando.
- defeito_qualidade é quando chegou o produto certo, mas quebrado, com defeito ou ruim.
- cobranca_cancelamento é quando o dinheiro é o assunto: cobrança indevida, estorno não feito, cancelamento sem pedido.
- outro cobre elogios com nota baixa, texto sem sentido e o que não couber em nada.
- Se ficar em dúvida entre duas, escolha a melhor e marque dúvida.
"""
)
