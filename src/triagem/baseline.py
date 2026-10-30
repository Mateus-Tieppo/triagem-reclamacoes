"""Baseline clássico: TF-IDF (palavras e caracteres) + SVM linear.

Treina com os rótulos prata (gerados por um LLM no pool de treino) e avalia no ouro.
Grava as predições no mesmo formato dos LLMs para entrar na mesma tabela.

    python -m triagem.baseline --prata results/preds/prata__ollama__qwen2.5-7b__few.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from . import dados
from .llm import INVALIDO


def montar_pipeline() -> Pipeline:
    feats = FeatureUnion([
        ("palavras", TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("caracteres", TfidfVectorizer(lowercase=True, strip_accents="unicode", analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
    ])
    return Pipeline([("tfidf", feats), ("svm", LinearSVC(class_weight="balanced"))])


def treinar(textos: list[str], rotulos: list[str]) -> GridSearchCV:
    busca = GridSearchCV(
        montar_pipeline(),
        {"svm__C": [0.1, 0.3, 1, 3]},
        scoring="f1_macro",
        cv=StratifiedKFold(5, shuffle=True, random_state=dados.SEED),
        n_jobs=-1,
    )
    busca.fit(textos, rotulos)
    return busca


def carregar_prata(caminho: Path) -> pd.DataFrame:
    linhas = [json.loads(l) for l in Path(caminho).read_text().splitlines() if l.strip()]
    prata = pd.DataFrame(linhas)
    prata = prata[prata.pred != INVALIDO]
    pool = dados.reclamacoes()
    return prata.merge(pool[["review_id", "texto"]], on="review_id")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--prata", required=True, type=Path)
    a = p.parse_args(argv)

    prata = carregar_prata(a.prata)
    print(f"Treinando com {len(prata)} rótulos prata")
    print(prata.pred.value_counts().to_string())
    busca = treinar(prata.texto.tolist(), prata.pred.tolist())
    print(f"Melhor C = {busca.best_params_['svm__C']}, F1 macro na validação cruzada = {busca.best_score_:.3f}")

    ouro = dados.carregar_ouro()
    modelo = busca.best_estimator_
    saida = dados.RAIZ / "results" / "preds" / "ouro__classico__tfidf-svm__treino-prata.jsonl"
    with saida.open("w") as f:
        for r in ouro.itertuples():
            t0 = time.perf_counter()
            pred = modelo.predict([r.texto])[0]
            lat = time.perf_counter() - t0
            f.write(json.dumps({"review_id": r.review_id, "pred": pred, "bruto": pred,
                                "tokens_entrada": 0, "tokens_saida": 0, "latencia_s": round(lat, 6)}) + "\n")
    joblib.dump(modelo, dados.RAIZ / "results" / "tfidf_svm.joblib")
    print(f"Salvo em {saida}")


if __name__ == "__main__":
    main()
