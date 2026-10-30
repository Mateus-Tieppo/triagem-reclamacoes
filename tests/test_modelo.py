import pytest

from triagem.modelo import palavras_que_pesaram, probabilidades, probabilidades_fora_da_amostra, treinar
from triagem.taxonomia import ROTULOS

TEXTOS = ["não chegou ainda"] * 20 + ["veio quebrado com defeito"] * 20 + ["faltou um item no pacote"] * 20
ROTS = ["nao_recebido_atraso"] * 20 + ["defeito_qualidade"] * 20 + ["item_faltando"] * 20


def test_aprende_padrao_simples():
    m = treinar(TEXTOS, ROTS).best_estimator_
    assert list(m.predict(["o pedido NÃO chegou", "chegou com defeito"])) == ["nao_recebido_atraso", "defeito_qualidade"]


def test_probabilidades_tem_todas_as_categorias():
    m = treinar(TEXTOS, ROTS).best_estimator_
    p = probabilidades(m, ["não chegou"])
    assert list(p.columns) == ROTULOS
    assert p.loc[0, "outro"] == 0 and p.loc[0, "produto_errado"] == 0
    assert p.loc[0].sum() == pytest.approx(1)


def test_fora_da_amostra_mesmo_formato():
    p = probabilidades_fora_da_amostra(TEXTOS, ROTS, C=1.0)
    assert p.shape == (60, len(ROTULOS))
    assert list(p.columns) == ROTULOS


def test_palavras_que_pesaram():
    m = treinar(TEXTOS, ROTS).best_estimator_
    assert "quebrado" in palavras_que_pesaram(m, "veio quebrado", "defeito_qualidade")
    assert palavras_que_pesaram(m, "veio quebrado", "outro") == []
