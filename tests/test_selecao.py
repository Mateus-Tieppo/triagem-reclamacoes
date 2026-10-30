import numpy as np
import pandas as pd

from triagem import dados
from triagem.selecao import ids_lidos_para_regras, selecionar


def pool_falso(n=4000):
    return pd.DataFrame({"review_id": [f"r{i}" for i in range(n)], "texto": [f"t{i}" for i in range(n)]})


def test_tamanhos_e_grupos_disjuntos():
    pool = pool_falso()
    cert = pd.Series(np.linspace(0, 1, len(pool)))
    s = selecionar(pool, cert, set())
    assert s.grupo.value_counts().to_dict() == {"dev": 500, "aleatorio": 1000, "incerto": 1500}
    assert s.review_id.is_unique


def test_dev_exclui_ids_lidos():
    pool = pool_falso()
    cert = pd.Series(0.5, index=pool.index)
    excluir = {f"r{i}" for i in range(0, 4000, 2)}
    s = selecionar(pool, cert, excluir)
    assert not set(s[s.grupo == "dev"].review_id) & excluir


def test_incerto_tem_menor_certeza_do_restante():
    pool = pool_falso()
    cert = pd.Series(np.linspace(0, 1, len(pool)))
    s = selecionar(pool, cert, set())
    resto = pool[~pool.review_id.isin(s[s.grupo != "incerto"].review_id)]
    limite = cert[resto.index].sort_values().iloc[1499]
    assert (s[s.grupo == "incerto"].certeza <= limite).all()


def test_reproduzivel():
    pool = pool_falso()
    cert = pd.Series(np.linspace(0, 1, len(pool)))
    assert selecionar(pool, cert, set()).equals(selecionar(pool, cert, set()))


def test_ids_lidos_para_regras_fora_do_ouro():
    ids = ids_lidos_para_regras()
    assert 800 <= len(ids) <= 1000
    assert not ids & set(dados.amostra_ouro(dados.reclamacoes()).review_id)


def test_ids_lidos_inclui_a_semente_padrao():
    assert set(dados.amostra_desenvolvimento(200, dados.SEED).review_id) <= ids_lidos_para_regras()
