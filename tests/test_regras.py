import re

import pandas as pd
import pytest

from triagem import dados
from triagem.regras import PRIORIDADE, REGRAS, relatorio, rotular


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
