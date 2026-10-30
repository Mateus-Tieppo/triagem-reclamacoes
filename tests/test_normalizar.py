import pytest

from triagem.normalizar import normalizar


@pytest.mark.parametrize("entrada,esperado", [
    ("NÃO Chegou", "nao chegou"),
    ("péssimooooo", "pessimo"),
    ("muuuito ruim!!!", "muito ruim!"),
    ("veja http://x.com/a e mail@x.com", "veja _link_ e _link_"),
    ("pedido 12345 de 20/12/2017 R$ 59,90", "pedido _num_ de _num_ r$ _num_"),
    ("  linha1\n\nlinha2\t ", "linha1 linha2"),
    ("", ""),
    ("😡😡😡", "😡"),
])
def test_normalizar(entrada, esperado):
    assert normalizar(entrada) == esperado


def test_normalizar_e_idempotente():
    t = "NÃO chegouuu, pedido 123 http://a.b"
    assert normalizar(normalizar(t)) == normalizar(t)


def test_normalizar_preserva_letras_duplas():
    assert normalizar("carro passou") == "carro passou"
