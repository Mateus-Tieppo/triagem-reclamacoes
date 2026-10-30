"""Lotes para o Claude rotular e checagem do que volta.

    python -m triagem.rotulagem preparar               # data/lotes/lote_XX.csv
    python -m triagem.rotulagem juntar                 # data/rotulos_claude.csv
    python -m triagem.rotulagem consistencia-preparar  # data/lotes/consistencia_XX.csv
    python -m triagem.rotulagem consistencia-juntar    # data/rotulos_claude_consistencia.csv

Cada lote vai para um agente que lê só os textos e o guia de rotulagem e grava
rotulos_XX.csv (review_id, rotulo, duvida). A junção falha se faltar, sobrar ou
repetir algum id, ou se algum rótulo não for uma das 7 categorias.
"""

from __future__ import annotations

import argparse

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from . import dados
from .selecao import ARQUIVO_PARA_ROTULAR, SEED_NOVO
from .taxonomia import ROTULOS

PASTA_LOTES = dados.RAIZ / "data" / "lotes"
ARQUIVO_ROTULOS = dados.RAIZ / "data" / "rotulos_claude.csv"
ARQUIVO_CONSISTENCIA = dados.RAIZ / "data" / "rotulos_claude_consistencia.csv"
N_CONSISTENCIA = 200


def dividir_em_lotes(df: pd.DataFrame, tamanho: int = 150, seed: int = SEED_NOVO) -> list[pd.DataFrame]:
    """Embaralha (quem rotula não sabe o grupo) e corta em lotes de `tamanho`."""
    misturado = df.sample(frac=1, random_state=seed)[["review_id", "texto"]].reset_index(drop=True)
    return [misturado.iloc[i:i + tamanho] for i in range(0, len(misturado), tamanho)]


def ler_booleano(valor) -> bool:
    return str(valor).strip().lower() in {"true", "sim", "s", "1"}


def juntar_rotulos(esperados: pd.DataFrame, devolvidos: list[pd.DataFrame]) -> pd.DataFrame:
    todos = pd.concat(devolvidos, ignore_index=True)
    todos["review_id"] = todos.review_id.astype(str)
    esperado = set(esperados.review_id)
    contagem = todos.review_id.value_counts()
    problemas = {
        "faltando": sorted(esperado - set(todos.review_id)),
        "repetidos": sorted(contagem[contagem > 1].index),
        "desconhecidos": sorted(set(todos.review_id) - esperado),
        "rótulo inválido": sorted(set(todos[~todos.rotulo.isin(ROTULOS)].review_id) & esperado),
    }
    if "secundaria" in todos:
        todos["secundaria"] = todos.secundaria.fillna("").astype(str).str.strip()
        invalida = todos[(todos.secundaria != "") & ~todos.secundaria.isin(ROTULOS)]
        problemas["secundária inválida"] = sorted(set(invalida.review_id) & esperado)
    partes = [f"{k}: {', '.join(v)}" for k, v in problemas.items() if v]
    if partes:
        raise ValueError("; ".join(partes))
    todos["duvida"] = todos.duvida.map(ler_booleano)
    extra = ["secundaria"] if "secundaria" in todos else []
    r = esperados[["review_id", "grupo"]].merge(todos[["review_id", "rotulo", *extra, "duvida"]], on="review_id")
    return r[["review_id", "rotulo", *extra, "duvida", "grupo"]]


def concordancia(a: pd.Series, b: pd.Series) -> dict:
    a, b = list(a), list(b)
    return {"acordo": sum(x == y for x, y in zip(a, b)) / len(a), "kappa": float(cohen_kappa_score(a, b))}


def _gravar_lotes(lotes: list[pd.DataFrame], prefixo: str) -> None:
    PASTA_LOTES.mkdir(parents=True, exist_ok=True)
    for i, l in enumerate(lotes, 1):
        l.to_csv(PASTA_LOTES / f"{prefixo}_{i:02d}.csv", index=False)
    print(f"{len(lotes)} lotes gravados em {PASTA_LOTES}")


def _ler_devolvidos(prefixo: str) -> list[pd.DataFrame]:
    return [pd.read_csv(p, dtype={"review_id": str}) for p in sorted(PASTA_LOTES.glob(f"{prefixo}_[0-9]*.csv"))]


def _amostra_consistencia(para_rotular: pd.DataFrame) -> pd.DataFrame:
    return para_rotular[para_rotular.grupo == "dev"].sample(N_CONSISTENCIA, random_state=SEED_NOVO)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("acao", choices=["preparar", "juntar", "consistencia-preparar", "consistencia-juntar"])
    a = p.parse_args(argv)
    para_rotular = pd.read_csv(ARQUIVO_PARA_ROTULAR, dtype={"review_id": str})
    if a.acao == "preparar":
        _gravar_lotes(dividir_em_lotes(para_rotular), "lote")
    elif a.acao == "juntar":
        r = juntar_rotulos(para_rotular, _ler_devolvidos("rotulos"))
        r.to_csv(ARQUIVO_ROTULOS, index=False)
        print(f"{len(r)} rótulos em {ARQUIVO_ROTULOS}")
        print(r.rotulo.value_counts().to_string())
    elif a.acao == "consistencia-preparar":
        _gravar_lotes(dividir_em_lotes(_amostra_consistencia(para_rotular), 100), "consistencia")
    else:
        amostra = _amostra_consistencia(para_rotular)
        r = juntar_rotulos(amostra, _ler_devolvidos("rotulos_consistencia"))
        r.to_csv(ARQUIVO_CONSISTENCIA, index=False)
        primeira = pd.read_csv(ARQUIVO_ROTULOS, dtype={"review_id": str}).set_index("review_id").rotulo
        c = concordancia(primeira[r.review_id], r.rotulo)
        print(f"Acordo {c['acordo']:.1%}, kappa {c['kappa']:.2f} em {len(r)} mensagens")


if __name__ == "__main__":
    main()
