"""Escolhe, uma vez, as mensagens que o Claude vai rotular.

    python -m triagem.selecao

Grava data/para_rotular.csv: 500 de desenvolvimento (sorteadas, fora das mensagens lidas
para escrever as regras), 1.000 de treino sorteadas e 1.500 de treino em que o modelo da
supervisão fraca tem menos certeza. Fica fora do `make tudo`.
"""

from __future__ import annotations

import joblib
import pandas as pd

from . import dados
from .modelo import probabilidades
from .triagem import PASTA_SUPERVISAO

SEED_NOVO = 2026
N_DEV, N_ALEATORIO, N_INCERTO = 500, 1000, 1500
ARQUIVO_PARA_ROTULAR = dados.RAIZ / "data" / "para_rotular.csv"


def ids_lidos_para_regras() -> set[str]:
    """Mensagens lidas para escrever as regras: amostras de desenvolvimento das sementes 0 a 3 e da padrão."""
    ids: set[str] = set()
    for s in (0, 1, 2, 3, dados.SEED):
        ids |= set(dados.amostra_desenvolvimento(200, s).review_id)
    return ids


def selecionar(pool: pd.DataFrame, certeza: pd.Series, excluir_do_dev: set[str]) -> pd.DataFrame:
    pool = pool.assign(certeza=certeza)
    dev = pool[~pool.review_id.isin(excluir_do_dev)].sample(N_DEV, random_state=SEED_NOVO)
    resto = pool.drop(dev.index)
    aleatorio = resto.sample(N_ALEATORIO, random_state=SEED_NOVO)
    resto = resto.drop(aleatorio.index)
    incerto = resto.sort_values(["certeza", "review_id"]).head(N_INCERTO)
    partes = [dev.assign(grupo="dev"), aleatorio.assign(grupo="aleatorio"), incerto.assign(grupo="incerto")]
    return pd.concat(partes)[["review_id", "texto", "grupo", "certeza"]].reset_index(drop=True)


def main():
    pool = dados.pool_de_treino().reset_index(drop=True)
    # O joblib é gerado pelo próprio projeto (`make supervisao`), não vem de fora.
    modelo = joblib.load(dados.RAIZ / "results" / PASTA_SUPERVISAO / "modelo.joblib")["modelo"]
    certeza = probabilidades(modelo, pool.texto.tolist()).max(axis=1)
    sel = selecionar(pool, certeza, ids_lidos_para_regras())
    sel.to_csv(ARQUIVO_PARA_ROTULAR, index=False)
    print(sel.grupo.value_counts().to_string())


if __name__ == "__main__":
    main()
