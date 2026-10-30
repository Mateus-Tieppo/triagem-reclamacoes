import re

import pandas as pd
import pytest

from triagem import dados
from triagem.regras import PRIORIDADE, REGRAS, regras_que_disparam, relatorio, rotular


@pytest.mark.parametrize("texto,rotulo", [
    ("Até hoje não recebi o produto", "nao_recebido_atraso"),
    ("NÃO CHEGOU", "nao_recebido_atraso"),
    ("naõ chegou ainda", "nao_recebido_atraso"),
    ("ñ chegou", "nao_recebido_atraso"),
    ("comprei 2 e só veio 1", "item_faltando"),
    ("veio a cor errada", "produto_errado"),
    ("diferente do anúncio", "produto_errado"),
    ("chegou rápido mas veio quebrado", "defeito_qualidade"),
    ("quero meu estorno", "cobranca_cancelamento"),
    ("a loja não responde meus emails", "atendimento_loja"),
    ("produto ótimo, entrega rápida", "outro"),
])
def test_rotular_categoria(texto, rotulo):
    assert rotular(texto).rotulo == rotulo


def test_sem_regra_fica_sem_rotulo():
    v = rotular("xyz abc qwerty")
    assert v.rotulo is None and v.regra is None and not v.conflito


def test_consequencia_perde_para_origem():
    v = rotular("não chegou e a loja não responde")
    assert v.rotulo == "nao_recebido_atraso" and not v.conflito


def test_duas_origens_marcam_conflito_e_seguem_prioridade():
    v = rotular("veio quebrado e faltou um item")
    assert v.conflito and v.rotulo == "item_faltando"


def test_outro_so_quando_nada_mais_dispara():
    assert rotular("produto ótimo mas não chegou").rotulo == "nao_recebido_atraso"


def test_nota_fiscal_nao_e_item_faltando():
    assert rotular("não veio a nota fiscal").rotulo != "item_faltando"


def test_regras_validas():
    nomes = [r.nome for r in REGRAS]
    assert len(nomes) == len(set(nomes))
    assert {r.categoria for r in REGRAS} == set(PRIORIDADE)
    for r in REGRAS:
        re.compile(r.padrao)


def test_pool_de_treino_sem_ouro_nem_fewshot():
    pool = dados.pool_de_treino()
    ouro = set(dados.amostra_ouro(dados.reclamacoes()).review_id)
    fs = set(pd.read_csv(dados.ARQUIVO_FEWSHOT).review_id)
    assert not (ouro | fs) & set(pool.review_id)
    assert {"review_id", "order_id", "texto"} <= set(pool.columns)


def test_relatorio_tem_cobertura():
    md = relatorio(["não chegou", "veio quebrado", "xyz"])
    assert "Sem rótulo" in md and "nao_recebido_atraso" in md


EXEMPLOS = {
    "sem_estoque": "vendeu sem ter o produto em estoque",
    "nao_recebi": "ainda não recebi o pedido",
    "nao_chegou": "o pedido não chegou",
    "nao_entregue": "não foi entregue",
    "nao_veio_produto": "não veio meu produto",
    "entrega_nao_realizada": "a entrega não foi realizada",
    "atrasou": "entrega atrasada",
    "demorou_chegar": "demorou demais para chegar",
    "demora_entrega": "muita demora na entrega",
    "prazo_nao_cumprido": "já passou do prazo",
    "aguardando_entrega": "aguardando a entrega",
    "quando_entrega": "quando vai chegar?",
    "so_veio_um": "só veio um",
    "veio_so_um": "chegou apenas uma",
    "faltando_item": "veio faltando um item",
    "entrega_parcial": "pedido incompleto",
    "outro_nao_veio": "o outro ainda não chegou",
    "um_entregue_outro_nao": "uma foi entregue e a outra ainda não",
    "so_o_primeiro": "só foi entregue a boneca",
    "faltou_o": "faltou o carregador",
    "nao_chegou_todo": "não chegou completo",
    "produto_errado": "modelo errado",
    "veio_errado": "veio errado",
    "diferente_anuncio": "diferente do anúncio",
    "nao_e_o_mesmo": "não é o mesmo da foto",
    "veio_outro": "veio outro produto",
    "nao_original": "produto falsificado",
    "quebrado": "veio quebrado",
    "defeito": "chegou com defeito",
    "nao_funciona": "não funciona",
    "ma_qualidade": "péssima qualidade",
    "parte_ruim": "costura muito ruim",
    "acabamento_ruim": "mal acabado",
    "estorno_reembolso": "quero o reembolso",
    "dinheiro_de_volta": "quero meu dinheiro de volta",
    "cancelamento": "pedi o cancelamento",
    "cobranca_indevida": "cobrança indevida no cartão",
    "nao_responde": "a loja não responde",
    "sem_resposta": "sem resposta da loja",
    "atendimento_ruim": "péssimo atendimento",
    "falta_comunicacao": "falta de comunicação",
    "elogio": "produto excelente",
    "entrega_rapida": "chegou antes do prazo",
    "ainda_nao_usei": "ainda não usei",
}


def test_toda_regra_tem_exemplo():
    assert set(EXEMPLOS) == {r.nome for r in REGRAS}


@pytest.mark.parametrize("nome,texto", sorted(EXEMPLOS.items()))
def test_regra_dispara_no_exemplo(nome, texto):
    assert nome in regras_que_disparam(texto)


@pytest.mark.parametrize("texto,nao_pode", [
    ("não chegou a nota fiscal", "nao_recebido_atraso"),
    ("não recebi a NF", "nao_recebido_atraso"),
    ("não recebi meu estorno ainda", "nao_recebido_atraso"),
    ("nao recebi a devolução do valor", "nao_recebido_atraso"),
    ("o produto não atendeu minhas expectativas", "atendimento_loja"),
    ("não atende o que promete", "atendimento_loja"),
    ("nem chegou perto do anunciado", "nao_recebido_atraso"),
    ("recebi outro e-mail da loja", "produto_errado"),
    ("Na hora que recebi o produto estava quebrado", "nao_recebido_atraso"),
    ("chegou sem atraso porém com defeito", "nao_recebido_atraso"),
])
def test_falso_positivo(texto, nao_pode):
    assert rotular(texto).rotulo != nao_pode


def test_sem_estoque_vence_entrega():
    assert rotular("cancelaram por falta de estoque e não recebi").rotulo == "sem_estoque"
