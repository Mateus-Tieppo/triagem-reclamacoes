import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import GridSearchCV

from triagem.desenvolvimento import montar_treino
from triagem.modelo import CANDIDATOS, GRADES, montar_candidato
from triagem.taxonomia import ROTULOS
from triagem.triagem import decidir_modelo

TEXTOS = ["não chegou ainda"] * 20 + ["veio quebrado com defeito"] * 20 + ["faltou um item no pacote"] * 20
ROTS = ["nao_recebido_atraso"] * 20 + ["defeito_qualidade"] * 20 + ["item_faltando"] * 20


def p(**kw):
    s = pd.Series(0.0, index=ROTULOS)
    s.update(pd.Series(kw, dtype=float))
    return s


def test_decidir_modelo():
    assert decidir_modelo(p(outro=0.9, item_faltando=0.1), 0.8, "não gostei").revisao is False
    assert decidir_modelo(p(outro=0.6, item_faltando=0.4), 0.8, "não gostei").motivo_revisao == "certeza baixa"
    assert decidir_modelo(p(outro=0.99), 0.8, "123").motivo_revisao == "texto sem conteúdo"
    assert decidir_modelo(p(outro=0.9), 0.8, "ok").origem == "modelo"


def test_montar_treino_formas():
    rot = pd.DataFrame({"review_id": ["a", "b", "d"], "rotulo": ["outro", "item_faltando", "outro"],
                        "grupo": ["aleatorio", "incerto", "dev"]})
    pool = pd.DataFrame({"review_id": ["a", "b", "c", "d", "e"], "texto": ["xyz", "só veio um", "não chegou", "ok", "abc"]})
    t, r, w = montar_treino(rot, pool, None)
    assert len(t) == 2 and (w == 1).all()
    t, r, w = montar_treino(rot, pool, 0.3)
    assert len(t) == 3 and r[-1] == "nao_recebido_atraso" and w[-1] == pytest.approx(0.3)


@pytest.mark.parametrize("nome", CANDIDATOS)
def test_peso_chega_ao_classificador(nome):
    w = np.r_[np.ones(30), np.full(30, 0.1)]
    busca = GridSearchCV(montar_candidato(nome), GRADES[nome], cv=3)
    busca.fit(TEXTOS, ROTS, clf__sample_weight=w)
    assert busca.best_estimator_ is not None


def test_tabela_md_formata_percentual_e_mantem_forma():
    from triagem.desenvolvimento import _tabela_md
    md = _tabela_md(pd.DataFrame([{"modelo": "nb", "forma": "B0.1", "f1_dev": 0.704, "params": {"a": 1}}]))
    assert "| nb | B0.1 | 70,4% |" in md


def test_palavras_no_svm_calibrado():
    from triagem.modelo import palavras_que_pesaram
    m = montar_candidato("svm").fit(TEXTOS, ROTS)
    assert "quebrado" in palavras_que_pesaram(m, "veio quebrado", "defeito_qualidade")
