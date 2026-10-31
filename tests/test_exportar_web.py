import joblib
import pandas as pd

from triagem.dados import RAIZ
from triagem.exportar_web import exportar_modelo, nunca_vistas, prever_com_export
from triagem.modelo import probabilidades
from triagem.taxonomia import ROTULOS


def artefato():
    # O joblib é gerado pelo próprio projeto (make treinar).
    return joblib.load(RAIZ / "results" / "modelo.joblib")


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
