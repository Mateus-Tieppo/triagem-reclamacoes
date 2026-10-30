import json

import pandas as pd
import pytest

from triagem import dados, triagem
from triagem.modelo import probabilidades, treinar
from triagem.regras import Voto, rotular
from triagem.taxonomia import ROTULOS
from triagem.triagem import decidir, escolher_limiar

TEXTOS = ["não chegou ainda"] * 20 + ["veio quebrado com defeito"] * 20 + ["faltou um item no pacote"] * 20
ROTS = ["nao_recebido_atraso"] * 20 + ["defeito_qualidade"] * 20 + ["item_faltando"] * 20


def p(**kw):
    s = pd.Series(0.0, index=ROTULOS)
    s.update(pd.Series(kw, dtype=float))
    return s


def test_regra_e_modelo_concordam():
    d = decidir(Voto("item_faltando", "so_veio_um", False, ("item_faltando",)), p(item_faltando=0.7, outro=0.3), 0.5)
    assert (d.categoria, d.origem, d.revisao, d.certeza) == ("item_faltando", "regra", False, 0.7)


def test_regra_e_modelo_discordam_vai_para_revisao():
    d = decidir(Voto("item_faltando", "so_veio_um", False, ("item_faltando",)), p(defeito_qualidade=0.8, item_faltando=0.2), 0.5)
    assert d.categoria == "item_faltando" and d.revisao and d.motivo_revisao == "regra e modelo discordam"


def test_sem_regra_modelo_decide_com_certeza_baixa():
    d = decidir(Voto(None, None, False, ()), p(outro=0.4, atendimento_loja=0.35, defeito_qualidade=0.25), 0.6)
    assert (d.categoria, d.origem, d.revisao, d.motivo_revisao) == ("outro", "modelo", True, "certeza baixa")


def test_conflito_modelo_decide_e_revisa():
    v = Voto("item_faltando", "faltou", True, ("item_faltando", "defeito_qualidade"))
    d = decidir(v, p(defeito_qualidade=0.9, item_faltando=0.1), 0.5)
    assert d.origem == "modelo" and d.categoria == "defeito_qualidade" and d.motivo_revisao == "conflito entre regras"


def test_texto_vazio_nao_quebra():
    m = treinar(TEXTOS, ROTS).best_estimator_
    d = decidir(rotular("😡😡"), probabilidades(m, ["😡😡"]).iloc[0], 0.9)
    assert d.revisao and d.categoria in ROTULOS


def test_escolher_limiar_olha_a_faixa_logo_acima():
    # Cada faixa de 0,1 acima do limiar precisa concordar pelo menos 85%; a média geral não basta.
    # Aqui a média geral é 80%, mas a faixa 0,6 erra tudo e a 0,9 acerta tudo.
    probas = pd.DataFrame([p(outro=0.95)] * 8 + [p(outro=0.65)] * 2)
    rotulos = ["outro"] * 8 + ["item_faltando"] * 2
    assert escolher_limiar(probas, rotulos, alvo=0.85) == pytest.approx(0.7)


def test_escolher_limiar_tudo_bom_fica_em_zero():
    probas = pd.DataFrame([p(outro=0.35), p(outro=0.95)])
    assert escolher_limiar(probas, ["outro", "outro"], alvo=0.85) == 0.0


def test_triagem_csv_sem_ouro(tmp_path, monkeypatch):
    pool = pd.DataFrame({"review_id": [f"t{i}" for i in range(60)], "order_id": "x", "texto": TEXTOS})
    ouro = pd.DataFrame({"review_id": ["o0", "o1", "o2"], "order_id": "x",
                         "texto": ["não chegou", "veio quebrado", "xyz"]})
    monkeypatch.setattr(dados, "pool_de_treino", lambda: pool)
    monkeypatch.setattr(dados, "reclamacoes", lambda *a, **k: pd.concat([pool, ouro]))
    monkeypatch.setattr(dados, "amostra_ouro", lambda *a, **k: ouro)
    monkeypatch.setattr(dados, "RAIZ", tmp_path)

    triagem.main()

    csv = pd.read_csv(tmp_path / "results" / "triagem.csv")
    assert list(csv.columns) == ["review_id", "texto", "categoria", "origem", "regra", "certeza",
                                 "revisao", "motivo_revisao", "palavras"]
    assert len(csv) == 60 and not csv.review_id.str.startswith("o").any()
    for nome in ["regras__sozinhas", "logistica__sozinho", "hibrido__final"]:
        arq = tmp_path / "results" / "preds" / f"ouro__supervisao-fraca__{nome}.jsonl"
        linhas = [json.loads(l) for l in arq.read_text().splitlines()]
        assert [l["review_id"] for l in linhas] == ["o0", "o1", "o2"]
        assert all({"pred", "latencia_s"} <= set(l) for l in linhas)
    assert "revisao" in linhas[0]
