"""Carregamento das avaliações da Olist e montagem dos conjuntos."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_BRUTO = RAIZ / "data" / "raw" / "olist_order_reviews_dataset.csv"
ARQUIVO_OURO = RAIZ / "data" / "ouro.csv"
ARQUIVO_FEWSHOT = RAIZ / "data" / "fewshot.csv"
SEED = 42


def reclamacoes(caminho: Path = ARQUIVO_BRUTO) -> pd.DataFrame:
    """Avaliações com nota 1 ou 2 e comentário de pelo menos 15 caracteres, sem duplicatas."""
    df = pd.read_csv(caminho)
    neg = df[(df.review_score <= 2) & df.review_comment_message.notna()].copy()
    neg["texto"] = neg.review_comment_message.str.replace(r"\s+", " ", regex=True).str.strip()
    neg = neg[neg.texto.str.len() >= 15]
    neg = neg.drop_duplicates("texto").drop_duplicates("review_id")
    return neg[["review_id", "order_id", "review_score", "texto"]].reset_index(drop=True)


def amostra_ouro(pool: pd.DataFrame, n: int = 300) -> pd.DataFrame:
    """A mesma amostra que foi rotulada à mão (seed 42)."""
    return pool.sample(n, random_state=SEED)


def carregar_ouro(caminho: Path = ARQUIVO_OURO) -> pd.DataFrame:
    """Conjunto ouro rotulado à mão: review_id, texto, rotulo, duvida."""
    return pd.read_csv(caminho)


def pool_treino(pool: pd.DataFrame, ouro_ids: set[str], excluir: set[str] = frozenset()) -> pd.DataFrame:
    """Tudo que não está no ouro nem nos exemplos do few-shot."""
    fora = set(ouro_ids) | set(excluir)
    return pool[~pool.review_id.isin(fora)].reset_index(drop=True)


def pool_de_treino() -> pd.DataFrame:
    """Reclamações fora do ouro e do few-shot. Usa só os ids do ouro, nunca os rótulos."""
    pool = reclamacoes()
    ouro_ids = set(amostra_ouro(pool).review_id)
    fewshot_ids = set(pd.read_csv(ARQUIVO_FEWSHOT).review_id)
    return pool_treino(pool, ouro_ids, fewshot_ids)


def amostra_desenvolvimento(n: int = 200, seed: int = SEED) -> pd.DataFrame:
    """Amostra do pool de treino para ler e escrever as regras."""
    pool = pool_de_treino()
    return pool.sample(min(n, len(pool)), random_state=seed)
