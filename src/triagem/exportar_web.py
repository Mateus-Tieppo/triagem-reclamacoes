"""Exporta o modelo para a ferramenta web e gera as referências de paridade.

    python -m triagem.exportar_web

Grava web/public/modelo.json (vocabulários, idf, regras, coeficientes e limiar) e
web/tests/fixtures/paridade.json (textos com a categoria e as probabilidades do
scikit-learn), que o teste do TypeScript usa para provar que o navegador dá a mesma
resposta. `prever_com_export` é a predição em Python puro a partir do export: a
referência do algoritmo que o TypeScript copia.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter

import joblib
import numpy as np
import pandas as pd

from . import dados
from .modelo import probabilidades
from .normalizar import normalizar
from .regras import REGRAS
from .selecao import SEED_NOVO
from .triagem import sem_conteudo

ARQUIVO_MODELO_WEB = dados.RAIZ / "web" / "public" / "modelo.json"
ARQUIVO_PARIDADE = dados.RAIZ / "web" / "tests" / "fixtures" / "paridade.json"
_TOKEN = re.compile(r"(?u)\b\w\w+\b")


def nunca_vistas() -> pd.DataFrame:
    """Pool de treino sem as 3.000 mensagens rotuladas pelo Claude (treino e desenvolvimento)."""
    rotuladas = set(pd.read_csv(dados.RAIZ / "data" / "rotulos_claude.csv", dtype={"review_id": str}).review_id)
    pool = dados.pool_de_treino()
    return pool[~pool.review_id.isin(rotuladas)][["review_id", "texto"]].reset_index(drop=True)


def _bloco(vetorizador) -> dict:
    vocab = {k: int(v) for k, v in vetorizador.vocabulary_.items()}
    return {"vocab": vocab, "idf": [round(float(x), 6) for x in vetorizador.idf_],
            "ngram": list(vetorizador.ngram_range)}


def exportar_modelo(artefato: dict) -> dict:
    modelo = artefato["modelo"]
    blocos = dict(modelo.named_steps["tfidf"].transformer_list)
    clf = modelo.named_steps["clf"]
    return {
        "classes": [str(c) for c in clf.classes_],
        "palavras": _bloco(blocos["palavras"]),
        "caracteres": _bloco(blocos["caracteres"]),
        "regras": [{"nome": r.nome, "padrao": r.padrao} for r in REGRAS],
        "coef": np.round(clf.coef_, 6).tolist(),
        "intercepto": np.round(clf.intercept_, 6).tolist(),
        "limiar": float(artefato["limiar"]),
    }


def _ngramas_palavras(t: str, ngram: list[int]) -> list[str]:
    tokens = _TOKEN.findall(t)
    saida = []
    for n in range(ngram[0], ngram[1] + 1):
        saida += [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
    return saida


def _ngramas_char_wb(t: str, ngram: list[int]) -> list[str]:
    # Mesmo algoritmo do analyzer="char_wb" do scikit-learn.
    saida = []
    for w in t.split():
        w = " " + w + " "
        for n in range(ngram[0], ngram[1] + 1):
            offset = 0
            saida.append(w[offset:offset + n])
            while offset + n < len(w):
                offset += 1
                saida.append(w[offset:offset + n])
            if offset == 0:
                break
    return saida


def _vetor_bloco(ngramas: list[str], bloco: dict) -> dict[int, float]:
    contagem = Counter(g for g in ngramas if g in bloco["vocab"])
    v = {bloco["vocab"][g]: (1 + math.log(c)) * bloco["idf"][bloco["vocab"][g]] for g, c in contagem.items()}
    norma = math.sqrt(sum(x * x for x in v.values()))
    return {i: x / norma for i, x in v.items()} if norma else {}


def prever_com_export(exp: dict, texto: str) -> dict:
    t = normalizar(texto)
    pal = _vetor_bloco(_ngramas_palavras(t, exp["palavras"]["ngram"]), exp["palavras"])
    car = _vetor_bloco(_ngramas_char_wb(t, exp["caracteres"]["ngram"]), exp["caracteres"])
    n_pal, n_car = len(exp["palavras"]["vocab"]), len(exp["caracteres"]["vocab"])
    x = dict(pal)
    x.update({n_pal + i: v for i, v in car.items()})
    for j, r in enumerate(exp["regras"]):
        if re.search(r["padrao"], t):
            x[n_pal + n_car + j] = 1.0
    escores = [b + sum(linha[i] * v for i, v in x.items()) for linha, b in zip(exp["coef"], exp["intercepto"])]
    m = max(escores)
    e = [math.exp(s - m) for s in escores]
    probas = {c: v / sum(e) for c, v in zip(exp["classes"], e)}
    return {"categoria": max(probas, key=probas.get), "probas": probas}


def main():
    # O joblib é gerado pelo próprio projeto (`make treinar`), não vem de fora.
    artefato = joblib.load(dados.RAIZ / "results" / "modelo.joblib")
    exp = exportar_modelo(artefato)
    ARQUIVO_MODELO_WEB.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_MODELO_WEB.write_text(json.dumps(exp, ensure_ascii=False, separators=(",", ":")))

    textos = dados.amostra_ouro(dados.reclamacoes()).texto.tolist()
    textos += nunca_vistas().sample(1000, random_state=SEED_NOVO).texto.tolist()
    textos += ["", "😡😡😡", "123456789012345"]
    probas = probabilidades(artefato["modelo"], textos)
    ref = [{"texto": t, "categoria": str(probas.iloc[i].idxmax()), "sem_conteudo": sem_conteudo(t),
            "probas": {c: round(float(probas.iloc[i][c]), 6) for c in exp["classes"]}}
           for i, t in enumerate(textos)]
    ARQUIVO_PARIDADE.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_PARIDADE.write_text(json.dumps(ref, ensure_ascii=False))
    print(f"{ARQUIVO_MODELO_WEB} ({ARQUIVO_MODELO_WEB.stat().st_size / 1e6:.1f} MB), {len(ref)} referências")


if __name__ == "__main__":
    main()
