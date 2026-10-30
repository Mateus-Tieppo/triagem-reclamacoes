"""Modelo clássico: TF-IDF (palavras e caracteres) + regressão logística.

Treina com os rótulos das regras. A normalização roda dentro do TF-IDF, então o mesmo
tratamento de texto vale no treino e na predição.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from . import dados
from .normalizar import normalizar
from .regras import REGRAS, regras_que_disparam
from .taxonomia import ROTULOS


def _validacao() -> StratifiedKFold:
    return StratifiedKFold(5, shuffle=True, random_state=dados.SEED)


def montar_pipeline(C: float = 1.0) -> Pipeline:
    feats = FeatureUnion([
        ("palavras", TfidfVectorizer(preprocessor=normalizar, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("caracteres", TfidfVectorizer(preprocessor=normalizar, analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
    ])
    return Pipeline([("tfidf", feats), ("logistica", LogisticRegression(C=C, class_weight="balanced", max_iter=2000))])


class VariaveisRegras(BaseEstimator, TransformerMixin):
    """Uma coluna 0/1 por regra: as regras viram pistas para o modelo, não decisão."""

    def fit(self, textos, y=None):
        return self

    def transform(self, textos) -> csr_matrix:
        indice = {r.nome: i for i, r in enumerate(REGRAS)}
        linhas, colunas = [], []
        for i, t in enumerate(textos):
            for nome in regras_que_disparam(t):
                linhas.append(i)
                colunas.append(indice[nome])
        return csr_matrix((np.ones(len(linhas)), (linhas, colunas)), shape=(len(textos), len(REGRAS)))


CANDIDATOS = ("logistica", "svm", "nb")
GRADES = {
    "logistica": {"clf__C": [0.3, 1, 3, 10, 30]},
    "svm": {"clf__estimator__C": [0.03, 0.1, 0.3, 1]},
    "nb": {"clf__alpha": [0.1, 0.3, 1]},
}


def montar_candidato(nome: str) -> Pipeline:
    """TF-IDF de palavras e caracteres mais as regras como variáveis, e um classificador."""
    feats = FeatureUnion([
        ("palavras", TfidfVectorizer(preprocessor=normalizar, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("caracteres", TfidfVectorizer(preprocessor=normalizar, analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
        ("regras", VariaveisRegras()),
    ])
    clf = {
        "logistica": lambda: LogisticRegression(class_weight="balanced", max_iter=2000),
        "svm": lambda: CalibratedClassifierCV(LinearSVC(class_weight="balanced"), cv=3),
        "nb": lambda: ComplementNB(),
    }[nome]()
    return Pipeline([("tfidf", feats), ("clf", clf)])


def treinar(textos: list[str], rotulos: list[str]) -> GridSearchCV:
    busca = GridSearchCV(montar_pipeline(), {"logistica__C": [0.3, 1, 3, 10]},
                         scoring="f1_macro", cv=_validacao(), n_jobs=-1)
    busca.fit(textos, rotulos)
    return busca


def _como_tabela(probas: np.ndarray, classes) -> pd.DataFrame:
    df = pd.DataFrame(probas, columns=list(classes))
    return df.reindex(columns=ROTULOS, fill_value=0.0)


def probabilidades(modelo: Pipeline, textos: list[str]) -> pd.DataFrame:
    """Probabilidade de cada categoria; categoria que não apareceu no treino fica com 0."""
    return _como_tabela(modelo.predict_proba(textos), modelo.classes_)


def probabilidades_fora_da_amostra(textos: list[str], rotulos: list[str], C: float) -> pd.DataFrame:
    """Probabilidades de cada linha vindas de um modelo que não a viu no treino."""
    probas = cross_val_predict(montar_pipeline(C), textos, rotulos, cv=_validacao(), method="predict_proba", n_jobs=-1)
    return _como_tabela(probas, sorted(set(rotulos)))


def palavras_que_pesaram(modelo: Pipeline, texto: str, categoria: str, k: int = 3) -> list[str]:
    """Os termos (só palavras, para ser legível) que mais puxaram o texto para a categoria."""
    logistica = modelo.named_steps.get("logistica", modelo.named_steps.get("clf"))
    if not hasattr(logistica, "coef_"):
        return []
    classes = list(logistica.classes_)
    if categoria not in classes:
        return []
    if len(classes) == 2:
        coef = logistica.coef_[0] * (1 if categoria == classes[1] else -1)
    else:
        coef = logistica.coef_[classes.index(categoria)]
    palavras = dict(modelo.named_steps["tfidf"].transformer_list)["palavras"]
    pesos = palavras.transform([texto]).toarray()[0]
    contrib = pesos * coef[: len(pesos)]
    ordem = np.argsort(-contrib)[:k]
    termos = palavras.get_feature_names_out()
    return [termos[i] for i in ordem if contrib[i] > 0]
