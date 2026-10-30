"""Regras legíveis que rotulam as reclamações (supervisão fraca).

Cada regra é uma expressão regular sobre o texto normalizado e vota numa categoria ou se
abstém. As regras foram escritas lendo amostras do pool de treino, nunca o conjunto ouro.

    python -m triagem.regras                 # grava results/regras.md
    python -m triagem.regras --amostra 200   # imprime mensagens do pool para ler
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from . import dados
from .normalizar import normalizar

PRIORIDADE: list[str] = [
    "sem_estoque",
    "nao_recebido_atraso",
    "item_faltando",
    "produto_errado",
    "defeito_qualidade",
    "cobranca_cancelamento",
    "atendimento_loja",
    "outro",
]
CATEGORIAS_ORIGEM = PRIORIDADE[:5]


@dataclass(frozen=True)
class Regra:
    nome: str
    categoria: str
    padrao: str


@dataclass(frozen=True)
class Voto:
    rotulo: Optional[str]
    regra: Optional[str]
    conflito: bool
    categorias: tuple[str, ...]


# Negação comum nas mensagens: "não", "n", "ñ" (vira "n"), "nunca", "nem".
NAO = r"\b(?:nao|n|nunca|nem)\s+(?:\w+\s+){0,2}"
# Depois de "não recebi", estas palavras indicam outra queixa (resposta, dinheiro, nota).
NAO_E_PRODUTO = r"(?!\s+(?:nenhum[a]? (?:resposta|retorno|contato|posicionamento|posicao|satisfacao|informac\w*|e-?mail|mensagem|parecer|comunicado)|resposta|retorno|contato|o estorno|estorno|o reembolso|reembolso|meu estorno|meu reembolso|a devolucao|devolucao|meu dinheiro|o dinheiro|o valor|a nota|nota|a nf|nf|e-?mail|_link_))"
QUANTIDADE = r"(?:um|uma|_num_|dois|duas|tres|quatro|o|a|os|as|parte|metade)\b(?!\s+(?:nota|nf)\b)"

REGRAS: list[Regra] = [
    # sem_estoque
    Regra("sem_estoque", "sem_estoque", r"\b(?:estoque|indisponive(?:l|is)|esgotad[oa]s?)\b|\b(?:nao|n) (?:tinha|tem|tinham|havia) (?:mais )?(?:o produto|disponive)"),
    # nao_recebido_atraso
    Regra("nao_recebi", "nao_recebido_atraso", r"(?:\b(?:nao|n|nunca|nem)\s+(?:\w+\s+){0,2}|\bna\s+)" + r"rec[e]?b(?:i|emos|ido|eu|er|e)\b" + NAO_E_PRODUTO),
    Regra("nao_chegou", "nao_recebido_atraso", NAO + r"cheg(?:ou|aram|a)\b(?!\s+(?:tod[oa]s?|complet[oa]|perto|a nota|nota|a nf|nf)\b)"),
    Regra("nao_entregue", "nao_recebido_atraso", NAO + r"(?:foi |foram |me foi )?entreg(?:ue|ues|ou|aram|ado)\b(?!\s+(?:a |)nota|\s+(?:totalmente|completo|integralmente|tudo))"),
    Regra("nao_veio_produto", "nao_recebido_atraso", NAO + r"(?:veio|vieram|enviaram|enviou|mandaram|mandou)\s+(?:o |a |meu |minha )?(?:produto|pedido|encomenda|mercadoria|compra)\b"),
    Regra("entrega_nao_realizada", "nao_recebido_atraso", r"\bentrega\s+(?:nao|n)\s+(?:foi\s+)?(?:realizada|feita|efetuada)"),
    Regra("atrasou", "nao_recebido_atraso", r"(?<!sem )\batras(?:o|ad[oa]s?|ou|aram)\b"),
    Regra("demorou_chegar", "nao_recebido_atraso", r"\b(?:demor(?:ou|a|ando|ei)|levou)\b.{0,25}\b(?:cheg|entreg|receb|vir\b)\w*"),
    Regra("demora_entrega", "nao_recebido_atraso", r"\b(?:demora|demorada|demorado|lentidao)\s+(?:\w+\s+){0,2}(?:entrega|chegar|receber)|\bentrega\s+(?:muito\s+)?(?:demorada|lenta|atrasada)|\b(?:ta|esta|estao) demorando\b|\bchateada? com a demora\b|\b(?:estravi|extravi)\w*"),
    Regra("prazo_nao_cumprido", "nao_recebido_atraso", r"\b(?:fora do prazo|passou (?:d[ao] |o |a )?(?:data|prazo)|nao (?:\w+\s+)?cumpri\w*\s+(?:\w+\s+){0,3}(?:prazo|data|combinado)|prazo (?:\w+\s+){0,3}(?:passou|vencido|venceu|expirou|estourou|acabou|esgotou|finalizou))"),
    Regra("aguardando_entrega", "nao_recebido_atraso", r"\b(?:aguard\w*|esperando|espera)\s+(?:a |o |pela |pelo |meu |minha )?(?:entrega|recebimento|chegada|produto|pedido|encomenda|mercadoria)\b|\bno aguardo d[oa] (?:entrega|produto|pedido)"),
    Regra("quando_entrega", "nao_recebido_atraso", r"\bquando (?:ira|vai|vao|sera|irao) (?:ser )?(?:entregue|chegar)|\b(?:vai|vao|ira) entregar\b|\bsolicito (?:a )?entrega\b|\bate (?:agora|hoje|o momento) nada\b|\b(?:dias|semanas|mes|meses) e nada\b|\bquero (?:o )?meu produto\b|\baguardo receber\b|\bno aguardo\W+ainda d[oa]\b|\bnao entrega (?:os |o |as )?(?:produtos?|pedidos?|mercadorias?)\b|\bnao (?:ter |tenha )?chegado\b"),
    # item_faltando
    Regra("so_veio_um", "item_faltando", r"\b(?:so|somente|apenas)\s+(?:me\s+)?(?:\w+ e )?(?:veio|vieram|chegou|chego|chegaram|recebi|recebemos|entregaram|entregou|foi entregue|foram entregues|enviaram|mandaram|embalaram)\s+" + QUANTIDADE),
    Regra("veio_so_um", "item_faltando", r"\b(?:veio|vieram|chegou|chegaram|recebi|entregaram|entregou|enviaram|enviou|mandaram(?:-me)?|foi entregue|foram entregues|entregue)\s+(?:so|somente|apenas)\s+" + QUANTIDADE + r"|\b(?:so|somente|apenas)\s+(?:um|uma|_num_)\s+(?:\w+\s+)?(?:chegou|veio|foi entregue)\b"),
    Regra("faltando_item", "item_faltando", r"\b(?:faltando|faltou|faltam|falta|faltaram)\s+(?!de\b)(?:\w+\s+)?(?:um|uma|_num_|o outro|a outra|os outros|as outras|item|itens|peca|pecas|produto|produtos|unidade|unidades|encomendas|parte)\b"),
    Regra("entrega_parcial", "item_faltando", r"\b(?:parcial|parcialmente|incomplet[oa]s?|pela metade|metade do (?:kit|pedido)|parte do pedido|parte da compra|na quantidade|a quantidade)\b|\b(?:somente|so|apenas)\s+(?:o|a|os|as)\s+(?!prazo|frete)\w+"),
    Regra("outro_nao_veio", "item_faltando", r"\b(?:o outro|a outra|os outros|as outras|e outr[oa]|o restante|o resto)\b.{0,30}" + NAO + r"(?:veio|vieram|chegou|chegaram|recebi|entregue)|\b(?:o outro|a outra|os outros|as outras)\s+(?:ainda\s+)?(?:nao|n)\b|\b(?:um|uma|_num_|duas|dois)\s+(?:foram entregues|foi entregue|chegaram|chegou)\W+(?:um|uma|_num_)\s+(?:nao|n)\b"),
    Regra("um_entregue_outro_nao", "item_faltando", r"\b(?:um|uma|_num_)\s+(?:\w+\s+){0,4}(?:foi entregue|chegou|veio)\b.{0,25}\b(?:a outra|o outro|e outr[oa])\b"),
    Regra("so_o_primeiro", "item_faltando", r"\b(?:so|somente|apenas)\s+(?:foi entregue\s+)?(?:o|a)\s+(?:\w+\s+){0,2}(?:foi entregue|chegou|veio)\b|\b(?:recebi|veio|chegou)\s+(?:um|uma|_num_)\s+(?:\w+\s+)?so\b|\bso foi entregue (?:o|a)\b"),
    Regra("faltou_o", "item_faltando", r"\b(?:faltou|faltando|faltaram)\s+(?:o|a|os|as)\s+(?!de\b)\w+|\bfalta (?:ser entregue|eu receber|receber)\b|\be (?:ela|ele|elas|eles) (?:nao|n) (?:veio|vieram|chegou|chegaram)\b"),
    Regra("nao_chegou_todo", "item_faltando", NAO + r"(?:foi |foram )?(?:cheg|entreg)\w*\s+(?:tod[oa]s?|complet[oa]|totalmente|integralmente)"),
    # produto_errado
    Regra("produto_errado", "produto_errado", r"\b(?:produto|item|modelo|cor|tamanho|numero|numeracao|voltagem|mercadoria|pedido|pecas)\s+(?:\w+\s+)?(?:errad[oa]s?|trocad[oa]s?)\b|\bno lugar d[oa]\b|\bnem se parece\b|\bveio tudo diferente\b"),
    Regra("veio_errado", "produto_errado", r"\b(?:veio|vieram|recebi|enviaram|mandaram|mandou|entregaram|chegou)\s+(?:o |a |um |uma )?(?:\w+\s+){0,2}errad[oa]s?\b"),
    Regra("diferente_anuncio", "produto_errado", r"\b(?:diferente|inferior|menor|maior|difere|nao condiz|noa condiz|condizente|nao (?:e|esta) como|nao e igual)\b.{0,30}\b(?:anuncio|anunciad[oa]|foto|fotos|imagem|imagens|descricao|descrito|site|pedido|comprei|pedi|encomendei|comprado|solicitado)\b"),
    Regra("nao_e_o_mesmo", "produto_errado", r"\b(?:nao|n)\s+(?:e|era|foi|corresponde|condiz)\s+(?:o |a )?(?:mesm[oa]|igual|conforme|com o|ao|o que (?:comprei|pedi)|(?:o )?que (?:comprei|pedi))"),
    Regra("veio_outro", "produto_errado", r"\b(?:veio|venho|chegou|recebi|enviaram|mandaram|entregaram|enviado|entregue)\s+(?:um |uma |o |a )?outr[oa]s?\b(?!\s+(?:nao|n|e-?mail|_link_|mensagem|codigo)\b)|\boutr[oa] (?:marca|modelo|cor|tamanho|produto)\b|\bfoi outr[oa]\b|\bque (?:chegou|veio|recebi) (?:e|era|foi) outr[oa]\b|\bque (?:nao|n) (?:pedi|comprei|encomendei|solicitei)\b"),
    Regra("nao_original", "produto_errado", r"\b(?:nao (?:e|era|parece ser) (?:o )?original|falsificad[oa]|replica|pirata|fals[oa])\b"),
    # defeito_qualidade
    Regra("quebrado", "defeito_qualidade", r"\b(?:quebrad[oa]s?|quebrou|trincad[oa]s?|rachad[oa]s?|amassad[oa]s?|avariad[oa]s?|danificad[oa]s?|rasgad[oa]s?|furad[oa]s?|riscad[oa]s?|estragad[oa]s?|manchad[oa]s?|lascad[oa]s?|vazando|vazou|esfarelad[oa]|avaria\w*|violad[oa]|suj[oa]s?|travando|trava muito|sem funcionar|nao funcionando|soltando|descolando|descascando|enferrujad[oa]|mal lacrad[oa]|tort[oa]|mancha\w*|descostur\w*|derret\w*|queim\w*|sem funcionalidade|ja veio usad[oa]|era usad[oa]|linha solta|instavel)\b|\b(?:veio|chegou|produto|recebi o produto|deve estar) com problema|\bnao (?:tem|possui) (?:muita |boa )?qualidade\b|\bmaterial nao e (?:tao )?bom\b"),
    Regra("defeito", "defeito_qualidade", r"\b(?:defeito|defeitos|defeituos[oa]s?)\b"),
    Regra("nao_funciona", "defeito_qualidade", NAO + r"(?:funciona|funcionou|funcionam|liga|ligou|carrega|encaixa|encaixam|serve|serviu|presta)\b|\bparou de funcionar\b|\bja parou\b"),
    Regra("ma_qualidade", "defeito_qualidade", r"\b(?:pessima|ma|baixa|horrivel|pouca|sem)\s+qualidade\b|\bqualidade\s+(?:\w+\s+)?(?:pessima|ruim|horrivel|inferior|baixa|duvidosa)\b"),
    Regra("parte_ruim", "defeito_qualidade", r"\b(?:impressao|costura|tecido|som|imagem|tela|bateria|sabor|potencia)\s+(?:\w+\s+){0,2}(?:pessim[oa]|ruim|horrivel|fraca|baixa)\b"),
    Regra("acabamento_ruim", "defeito_qualidade", r"\b(?:fragil|frageis|mal acabad[oa]s?|porcaria|vagabund[oa]|acabamento (?:\w+\s+)?(?:ruim|pessimo|grosseiro))\b|\bmaterial (?:\w+\s+)?(?:ruim|pessimo|fraco|inferior)\b"),
    # cobranca_cancelamento
    Regra("estorno_reembolso", "cobranca_cancelamento", r"\b(?:estorn\w*|reembols\w*|reimbo\w*|ressarc\w*)\b"),
    Regra("dinheiro_de_volta", "cobranca_cancelamento", r"\b(?:dinheiro de volta|valor de volta|devol\w* (?:o |do |meu )?(?:dinheiro|valor)|(?:o |meu )?dinheiro (?:\w+\s+)?devolvido)\b"),
    Regra("cancelamento", "cobranca_cancelamento", r"\bcancel\w*\b"),
    Regra("cobranca_indevida", "cobranca_cancelamento", r"\b(?:cobranca|cobrad[oa]s?|cobraram|descontad[oa]|debitad[oa]|duas vezes no cartao|valor (?:\w+\s+)?(?:a mais|errado|indevido|divergente))\b"),
    # atendimento_loja
    Regra("nao_responde", "atendimento_loja", r"\b(?:nao|n|ninguem|nem)\s+(?:me\s+)?(?:\w+\s+)?(?:respond\w*|retorn(?:am|aram|ou|a)\b|me atend\w*|atend(?:em|eram|e o telefone|e telefone|imento)\b(?!\s+(?:o que|as|minhas|a minha|ao que))|deu (?:retorno|resposta|satisfacao)|dao (?:retorno|satisfacao|resposta)|entr\w+ em contato)"),
    Regra("sem_resposta", "atendimento_loja", r"\b(?:sem|nenhum|nenhuma|nao tive|nao obtive|nao recebi)\s+(?:\w+\s+)?(?:resposta|retorno|contato|satisfacao|posicionamento|posicao|explicac\w*|previsao|informac\w*|atendimento|comunicado)\b"),
    Regra("atendimento_ruim", "atendimento_loja", r"\b(?:pessimo|horrivel|mau|mal|falta de|sem|demora no|qualidade no)\s+atendimento\b|\bpouco caso\b|\batendimento\s+(?:\w+\s+)?(?:pessimo|horrivel|ruim|lamentavel)\b"),
    Regra("falta_comunicacao", "atendimento_loja", r"\bfalta de (?:comunicacao|informac\w*|respeito|atencao|contato|retorno|satisfacao)\b|\bdescaso\b|\bdificil (?:o )?contato\b|\bnao consig\w* (?:\w+ ){0,2}(?:contato|falar)\b"),
    # outro
    Regra("elogio", "outro", r"\b(?:otim[oa]s?|excelente|perfeit[oa]|adorei|amei|gostei muito|parabens|tudo certo|tudo certinho|muito bom|muito boa|lind[oa]|maravilhos[oa]|obrigad[oa]|de primeira)\b|(?<!nao )(?<!n )\brecomendo\b"),
    Regra("entrega_rapida", "outro", r"\b(?:chegou|entregue|entrega)\s+(?:muito\s+)?(?:antes|rapid[oa]|no prazo|dentro do prazo)\b"),
    Regra("ainda_nao_usei", "outro", r"\bainda nao (?:usei|testei|abri|montei|instalei|utilizei)\b"),
]

_COMPILADAS = [(r, re.compile(r.padrao)) for r in REGRAS]


def regras_que_disparam(texto: str) -> list[str]:
    """Nomes das regras que disparam no texto."""
    t = normalizar(texto)
    return [r.nome for r, p in _COMPILADAS if p.search(t)]


def rotular(texto: str) -> Voto:
    """Aplica as regras e combina os votos pela prioridade da taxonomia."""
    t = normalizar(texto)
    disparos = [r for r, p in _COMPILADAS if p.search(t)]
    cats = {r.categoria for r in disparos}
    if cats - {"outro"}:
        cats.discard("outro")
    if not cats:
        return Voto(None, None, False, ())
    ordem = tuple(c for c in PRIORIDADE if c in cats)
    rotulo = ordem[0]
    regra = next(r.nome for r in disparos if r.categoria == rotulo)
    conflito = len(cats & set(CATEGORIAS_ORIGEM)) >= 2
    return Voto(rotulo, regra, conflito, ordem)


def _pct(n: int, total: int) -> str:
    return f"{n} ({100 * n / total:.1f}%)".replace(".", ",") if total else "0"


def relatorio(textos: list[str]) -> str:
    """Cobertura das regras: por categoria, por regra, sem rótulo e com conflito."""
    total = len(textos)
    votos = [rotular(t) for t in textos]
    por_cat = Counter(v.rotulo for v in votos if v.rotulo)
    por_regra = Counter()
    for t in textos:
        por_regra.update(regras_que_disparam(t))
    sem = sum(v.rotulo is None for v in votos)
    conflito = sum(v.conflito for v in votos)
    md = [f"## Cobertura das regras ({total} mensagens do pool de treino)", "",
          "| Categoria | Mensagens |", "| --- | --- |"]
    md += [f"| {c} | {_pct(por_cat[c], total)} |" for c in PRIORIDADE]
    md += [f"| Sem rótulo | {_pct(sem, total)} |", f"| Com conflito | {_pct(conflito, total)} |", "",
           "### Disparos por regra", "", "| Regra | Categoria | Disparos |", "| --- | --- | --- |"]
    md += [f"| {r.nome} | {r.categoria} | {por_regra[r.nome]} |" for r in REGRAS]
    return "\n".join(md) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--amostra", type=int, help="imprime N mensagens do pool de treino")
    p.add_argument("--seed", type=int, default=dados.SEED)
    a = p.parse_args(argv)
    if a.amostra:
        for t in dados.amostra_desenvolvimento(a.amostra, a.seed).texto:
            v = rotular(t)
            print(f"[{v.rotulo or '-'}{' CONFLITO' if v.conflito else ''}] {t}")
        return
    md = relatorio(dados.pool_de_treino().texto.tolist())
    (dados.RAIZ / "results" / "regras.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
