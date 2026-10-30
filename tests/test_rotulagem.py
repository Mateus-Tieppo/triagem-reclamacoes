import pandas as pd
import pytest

from triagem.rotulagem import concordancia, dividir_em_lotes, juntar_rotulos, ler_booleano

ESP = pd.DataFrame({"review_id": ["a", "b", "c"], "texto": ["x", "y", "z"], "grupo": ["dev", "aleatorio", "incerto"]})


def lote(ids, rot="outro", duv="false"):
    return pd.DataFrame({"review_id": ids, "rotulo": rot, "duvida": duv})


def test_juntar_ok():
    r = juntar_rotulos(ESP, [lote(["a", "b"]), lote(["c"], duv="sim")])
    assert list(r.columns) == ["review_id", "rotulo", "duvida", "grupo"]
    assert r.set_index("review_id").loc["c", "duvida"] == True  # noqa: E712


@pytest.mark.parametrize("devolvidos,trecho", [
    ([lote(["a", "b"])], "faltando: c"),
    ([lote(["a", "b", "c", "a"])], "repetidos: a"),
    ([lote(["a", "b", "c", "zz"])], "desconhecidos: zz"),
    ([lote(["a", "b"]), lote(["c"], rot="frete")], "rótulo inválido: c"),
])
def test_juntar_falha_com_ids(devolvidos, trecho):
    with pytest.raises(ValueError, match=trecho):
        juntar_rotulos(ESP, devolvidos)


@pytest.mark.parametrize("v,esperado", [
    ("sim", True), ("true", True), ("1", True), (True, True), (1, True),
    ("não", False), ("false", False), ("", False), (False, False),
])
def test_ler_booleano(v, esperado):
    assert ler_booleano(v) is esperado


def test_lotes_cobrem_tudo_sem_repetir():
    df = pd.DataFrame({"review_id": [f"r{i}" for i in range(320)], "texto": "t"})
    lotes = dividir_em_lotes(df, 150)
    assert [len(l) for l in lotes] == [150, 150, 20]
    assert sorted(pd.concat(lotes).review_id) == sorted(df.review_id)
    assert list(lotes[0].columns) == ["review_id", "texto"]


def test_concordancia():
    r = concordancia(pd.Series(["a", "b", "a"]), pd.Series(["a", "b", "b"]))
    assert r["acordo"] == pytest.approx(2 / 3)
    assert "kappa" in r


def test_ler_devolvidos_nao_mistura_consistencia(tmp_path, monkeypatch):
    from triagem import rotulagem
    monkeypatch.setattr(rotulagem, "PASTA_LOTES", tmp_path)
    lote(["a"]).to_csv(tmp_path / "rotulos_01.csv", index=False)
    lote(["b"]).to_csv(tmp_path / "rotulos_consistencia_01.csv", index=False)
    assert len(rotulagem._ler_devolvidos("rotulos")) == 1
    assert len(rotulagem._ler_devolvidos("rotulos_consistencia")) == 1
