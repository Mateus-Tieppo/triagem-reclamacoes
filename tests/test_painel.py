import json

import pandas as pd

from triagem.dados import RAIZ
from triagem.painel import ROTULO_LEGIVEL, montar_painel
from triagem.regras import REGRAS


def tri_falso():
    return pd.DataFrame({"review_id": ["a", "b", "c"], "texto": ["não recebi", "veio quebrado", "xyz"],
                         "categoria": ["nao_recebido_atraso", "defeito_qualidade", "outro"],
                         "certeza": [0.9, 0.95, 0.4], "revisao": [False, False, True],
                         "motivo_revisao": ["", "", "certeza baixa"], "palavras": ["recebi", "quebrado", ""]})


def test_montar_painel_conta():
    p = montar_painel(tri_falso(), pd.Series(["2018-01-05", "2018-01-20", "2018-02-01"], index=["a", "b", "c"]))
    assert p["total"] == 3 and p["sem_humano"] == 2
    assert p["por_mes"][0]["mes"] == "2018-01" and p["por_mes"][0]["nao_recebido_atraso"] == 1
    assert p["regras_top"]["nao_recebido_atraso"][0]["nome"] == "nao_recebi"
    assert p["mensagens"][0]["id"] == "a" and p["mensagens"][0]["data"] == "2018-01-05"


def test_rotulo_legivel_cobre_todas_as_regras():
    assert {r.nome for r in REGRAS} == set(ROTULO_LEGIVEL)


def test_painel_real_so_nunca_vistas():
    p = json.loads((RAIZ / "web" / "public" / "painel.json").read_text())
    assert p["total"] == 7453 == len(p["mensagens"])
