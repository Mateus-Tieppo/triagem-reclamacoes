import json
from functools import cache

import pandas as pd

from triagem import dados
from triagem.dados import RAIZ
from triagem.desenvolvimento import montar_treino
from triagem.exportar_web import ARQUIVO_MODELO_WEB, ARQUIVO_PARIDADE, exportar_modelo, nunca_vistas, prever_com_export
from triagem.modelo import montar_candidato, probabilidades
from triagem.rotulagem import ARQUIVO_ROTULOS
from triagem.taxonomia import ROTULOS


@cache
def artefato():
    # Treina aqui, com a receita do modelo escolhido (logística, C=10, forma A), para o teste
    # não depender do results/modelo.joblib, que só existe depois do make treinar.
    rotulos = pd.read_csv(ARQUIVO_ROTULOS, dtype={"review_id": str})
    textos, rots, _ = montar_treino(rotulos, dados.pool_de_treino().reset_index(drop=True), None)
    modelo = montar_candidato("logistica").set_params(clf__C=10).fit(textos, rots)
    return {"modelo": modelo, "limiar": 0.8}


def test_export_tem_formato():
    exp = exportar_modelo(artefato())
    assert sorted(exp["classes"]) == sorted(ROTULOS)
    n = len(exp["palavras"]["vocab"]) + len(exp["caracteres"]["vocab"]) + len(exp["regras"])
    assert len(exp["coef"]) == 8 and len(exp["coef"][0]) == n
    assert len(exp["intercepto"]) == 8 and 0 < exp["limiar"] < 1


def test_python_puro_igual_ao_sklearn():
    art = artefato()
    exp = exportar_modelo(art)
    textos = nunca_vistas().sample(300, random_state=1).texto.tolist() + ["", "😡😡", "123", "NÃO CHEGOU"]
    ref = probabilidades(art["modelo"], textos)
    for i, t in enumerate(textos):
        p = prever_com_export(exp, t)
        assert p["categoria"] == ref.iloc[i].idxmax(), t
        assert max(abs(p["probas"][c] - ref.iloc[i][c]) for c in ROTULOS) < 1e-3, t


def test_nunca_vistas_exclui_rotuladas():
    rot = set(pd.read_csv(RAIZ / "data" / "rotulos_claude.csv", dtype={"review_id": str}).review_id)
    nv = nunca_vistas()
    assert len(nv) == 7453 and not rot & set(nv.review_id)


def test_modelo_publicado_bate_com_a_paridade():
    # O modelo.json que vai para o site e as referências do scikit-learn ficam no git.
    exp = json.loads(ARQUIVO_MODELO_WEB.read_text())
    for r in json.loads(ARQUIVO_PARIDADE.read_text()):
        p = prever_com_export(exp, r["texto"])
        assert p["categoria"] == r["categoria"], r["texto"]
        assert max(abs(p["probas"][c] - r["probas"][c]) for c in ROTULOS) < 1e-3, r["texto"]
