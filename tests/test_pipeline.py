import json

import pandas as pd
import pytest

from triagem import avaliar, dados, prompts
from triagem.baseline import treinar
from triagem.llm import INVALIDO, extrair_rotulo
from triagem.taxonomia import ROTULOS


@pytest.mark.parametrize("bruto,esperado", [
    ('{"categoria": "item_faltando"}', "item_faltando"),
    ('Claro! {"categoria":"produto_errado"}', "produto_errado"),
    ("A categoria é defeito_qualidade.", "defeito_qualidade"),
    ('{"categoria": "frete"}', INVALIDO),
    ("item_faltando ou produto_errado", INVALIDO),
    ("", INVALIDO),
])
def test_extrair_rotulo(bruto, esperado):
    assert extrair_rotulo(bruto) == esperado


def test_prompt_lista_todas_as_categorias():
    s = prompts.sistema()
    assert all(r in s for r in ROTULOS)


def test_fewshot_vira_pares_usuario_assistente():
    msgs = prompts.mensagens("oi", [("a", "outro"), ("b", "item_faltando")])
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant", "user"]
    assert json.loads(msgs[1]["content"]) == {"categoria": "outro"}


def test_fewshot_valido_e_fora_do_ouro():
    fs = pd.read_csv(dados.ARQUIVO_FEWSHOT)
    assert set(fs.rotulo) == set(ROTULOS)
    ouro_ids = set(dados.amostra_ouro(dados.reclamacoes()).review_id)
    assert not ouro_ids & set(fs.review_id)


def test_amostra_ouro_reproduzivel():
    pool = dados.reclamacoes()
    a, b = dados.amostra_ouro(pool), dados.amostra_ouro(pool)
    assert len(a) == 300 and list(a.review_id) == list(b.review_id)


def test_avaliar_conta_ausente_como_invalido():
    ouro = pd.DataFrame({"review_id": ["a", "b", "c"], "rotulo": ["outro", "item_faltando", "outro"], "duvida": [False, False, True]})
    preds = pd.DataFrame({"review_id": ["a", "b"], "pred": ["outro", "outro"], "latencia_s": [0.1, 0.2],
                          "tokens_entrada": [10, 10], "tokens_saida": [5, 5]})
    r = avaliar.avaliar(ouro, preds)
    # "c" não tem predição: conta como inválida e cai em "outro", que é o rótulo certo dela
    assert r["invalidas"] == pytest.approx(1 / 3)
    assert r["acuracia"] == pytest.approx(2 / 3)


def test_cliente_ollama_monta_pedido_e_le_resposta(monkeypatch):
    from triagem.llm import ClienteOllama

    enviado = {}

    def falso_post(self, corpo):
        enviado.update(corpo)
        return {"message": {"content": '{"categoria": "item_faltando"}'}, "prompt_eval_count": 321, "eval_count": 9}

    monkeypatch.setattr(ClienteOllama, "_post", falso_post)
    p = ClienteOllama("qwen2.5:7b").classificar("veio só uma unidade", [("x", "outro")])
    assert p.rotulo == "item_faltando" and p.tokens_entrada == 321 and p.tokens_saida == 9
    assert enviado["format"] == "json" and enviado["options"]["temperature"] == 0
    assert enviado["messages"][0]["role"] == "system" and len(enviado["messages"]) == 4


def test_ouro_completo_e_valido():
    ouro = dados.carregar_ouro()
    assert len(ouro) == 300 and ouro.review_id.is_unique
    assert set(ouro.rotulo) <= set(ROTULOS)
    assert set(ouro.fonte) == {"mateus", "claude"}


def test_baseline_aprende_padrao_simples():
    textos = ["não chegou ainda"] * 20 + ["veio quebrado com defeito"] * 20 + ["faltou um item no pacote"] * 20
    rotulos = ["nao_recebido_atraso"] * 20 + ["defeito_qualidade"] * 20 + ["item_faltando"] * 20
    m = treinar(textos, rotulos).best_estimator_
    assert list(m.predict(["o pedido não chegou", "chegou com defeito"])) == ["nao_recebido_atraso", "defeito_qualidade"]


def test_avaliar_com_revisao():
    ouro = pd.DataFrame({"review_id": ["a", "b"], "rotulo": ["outro", "item_faltando"], "duvida": [False, False]})
    preds = pd.DataFrame({"review_id": ["a", "b"], "pred": ["outro", "outro"], "latencia_s": [0.0, 0.0], "revisao": [False, True]})
    r = avaliar.avaliar(ouro, preds)
    assert r["taxa_revisao"] == 0.5 and r["f1_aceitas"] == pytest.approx(1.0)


def test_avaliar_sem_revisao_fica_nan():
    ouro = pd.DataFrame({"review_id": ["a"], "rotulo": ["outro"], "duvida": [False]})
    preds = pd.DataFrame({"review_id": ["a"], "pred": ["outro"], "latencia_s": [0.0]})
    r = avaliar.avaliar(ouro, preds)
    assert pd.isna(r["taxa_revisao"]) and pd.isna(r["f1_aceitas"])


def test_guia_tem_categorias_e_regra_principal():
    from triagem.taxonomia import GUIA_ROTULAGEM
    assert all(r in GUIA_ROTULAGEM for r in ROTULOS)
    assert "problema que originou" in GUIA_ROTULAGEM
