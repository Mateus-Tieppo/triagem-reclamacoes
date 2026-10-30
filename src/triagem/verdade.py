"""Conferência de atraso com as datas reais de entrega da Olist.

É só conferência, não variável do modelo. Precisa de data/raw/olist_orders_dataset.csv,
que vem da mesma base pública no Kaggle; sem o arquivo, a avaliação pula esta parte.
"""

from __future__ import annotations

import pandas as pd

from . import dados

ARQUIVO_PEDIDOS = dados.RAIZ / "data" / "raw" / "olist_orders_dataset.csv"


def _atrasado(pedidos: pd.DataFrame) -> pd.Series:
    entregue = pd.to_datetime(pedidos.order_delivered_customer_date)
    prometido = pd.to_datetime(pedidos.order_estimated_delivery_date)
    return (pedidos.order_status != "delivered") | (entregue > prometido)


def conferir_atraso(triagem: pd.DataFrame, pedidos: pd.DataFrame) -> dict:
    """Entre as mensagens classificadas como atraso, quantas são de pedidos de fato atrasados."""
    if "order_id" not in triagem:
        triagem = triagem.merge(dados.reclamacoes()[["review_id", "order_id"]], on="review_id", how="left")
    ped = pedidos.assign(atrasado=_atrasado(pedidos))[["order_id", "atrasado"]]
    m = triagem.merge(ped, on="order_id", how="inner")
    atraso = m[m.categoria == "nao_recebido_atraso"]
    return {
        "n_atraso": int(len(atraso)),
        "pct_atrasado_entre_atraso": float(atraso.atrasado.mean()) if len(atraso) else float("nan"),
        "pct_atrasado_geral": float(m.atrasado.mean()) if len(m) else float("nan"),
    }
