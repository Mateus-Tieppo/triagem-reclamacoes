"""Decisão final: regra quando ela decide, modelo no resto, e o humano na dúvida.

    python -m triagem.triagem

Grava results/triagem.csv (a fila do pool de treino, com motivo de revisão e explicação),
results/modelo.joblib e as predições no ouro para a avaliação. Não lê os rótulos do ouro.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from . import dados
from .modelo import palavras_que_pesaram, probabilidades, probabilidades_fora_da_amostra, treinar
from .regras import Voto, rotular

ALVO_CONCORDANCIA = 0.85


@dataclass(frozen=True)
class Decisao:
    categoria: str
    origem: str
    regra: Optional[str]
    certeza: float
    revisao: bool
    motivo_revisao: str


def escolher_limiar(probas: pd.DataFrame, rotulos: list[str], alvo: float = ALVO_CONCORDANCIA) -> float:
    """Início da faixa de certeza (largura 0,1) a partir da qual toda faixa acima concorda pelo menos `alvo`.

    Olha faixa por faixa, e não a média de tudo que passa do limiar: as mensagens fáceis, com
    certeza alta, puxariam a média para cima e esconderiam as incertas. Faixas vazias não contam.
    """
    maximo = probas.max(axis=1).to_numpy()
    acerto = probas.idxmax(axis=1).to_numpy() == np.asarray(rotulos)
    faixa = np.minimum((maximo * 10).astype(int), 9)
    limiar = 0
    for f in range(9, -1, -1):
        na_faixa = faixa == f
        if na_faixa.any() and acerto[na_faixa].mean() < alvo:
            limiar = f + 1
            break
    return round(limiar / 10, 1)


def decidir(voto: Voto, probas: pd.Series, limiar: float) -> Decisao:
    previsto = str(probas.idxmax())
    if voto.rotulo and not voto.conflito:
        discorda = previsto != voto.rotulo
        return Decisao(voto.rotulo, "regra", voto.regra, float(probas[voto.rotulo]), discorda,
                       "regra e modelo discordam" if discorda else "")
    certeza = float(probas.max())
    motivos = []
    if voto.conflito:
        motivos.append("conflito entre regras")
    if certeza < limiar:
        motivos.append("certeza baixa")
    return Decisao(previsto, "modelo", voto.regra if voto.conflito else None, certeza, bool(motivos), "; ".join(motivos))


def _gravar_jsonl(caminho: Path, linhas: list[dict]) -> None:
    caminho.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas))


def _predizer_ouro(modelo, limiar: float, pasta: Path) -> None:
    ouro = dados.amostra_ouro(dados.reclamacoes())
    regras, logistica, hibrido = [], [], []
    for r in ouro.itertuples():
        t0 = time.perf_counter()
        voto = rotular(r.texto)
        t1 = time.perf_counter()
        probas = probabilidades(modelo, [r.texto]).iloc[0]
        t2 = time.perf_counter()
        d = decidir(voto, probas, limiar)
        t3 = time.perf_counter()
        regras.append({"review_id": r.review_id, "pred": voto.rotulo or "outro", "latencia_s": round(t1 - t0, 6)})
        logistica.append({"review_id": r.review_id, "pred": str(probas.idxmax()), "latencia_s": round(t2 - t1, 6)})
        hibrido.append({"review_id": r.review_id, "pred": d.categoria, "latencia_s": round(t3 - t0, 6),
                        "revisao": d.revisao, "origem": d.origem})
    _gravar_jsonl(pasta / "ouro__supervisao-fraca__regras__sozinhas.jsonl", regras)
    _gravar_jsonl(pasta / "ouro__supervisao-fraca__logistica__sozinho.jsonl", logistica)
    _gravar_jsonl(pasta / "ouro__supervisao-fraca__hibrido__final.jsonl", hibrido)


def main():
    res = dados.RAIZ / "results"
    (res / "preds").mkdir(parents=True, exist_ok=True)

    pool = dados.pool_de_treino().reset_index(drop=True)
    votos = [rotular(t) for t in pool.texto]
    no_treino = np.array([v.rotulo is not None and not v.conflito for v in votos])
    textos_treino = pool.texto[no_treino].tolist()
    rotulos_treino = [v.rotulo for v, ok in zip(votos, no_treino) if ok]

    busca = treinar(textos_treino, rotulos_treino)
    C = busca.best_params_["logistica__C"]
    modelo = busca.best_estimator_
    fora = probabilidades_fora_da_amostra(textos_treino, rotulos_treino, C)
    limiar = escolher_limiar(fora, rotulos_treino)

    # Linhas do treino usam a predição fora da amostra, para não inflar concordância nem certeza.
    probas = probabilidades(modelo, pool.texto.tolist())
    probas.loc[no_treino] = fora.to_numpy()

    linhas = []
    for i, (r, voto) in enumerate(zip(pool.itertuples(), votos)):
        d = decidir(voto, probas.iloc[i], limiar)
        linhas.append({"review_id": r.review_id, "texto": r.texto, "categoria": d.categoria, "origem": d.origem,
                       "regra": d.regra or "", "certeza": round(d.certeza, 4), "revisao": d.revisao,
                       "motivo_revisao": d.motivo_revisao,
                       "palavras": ", ".join(palavras_que_pesaram(modelo, r.texto, d.categoria))})
    tabela = pd.DataFrame(linhas)
    tabela.to_csv(res / "triagem.csv", index=False)
    joblib.dump({"modelo": modelo, "limiar": limiar, "C": C}, res / "modelo.joblib")
    _predizer_ouro(modelo, limiar, res / "preds")

    print(f"Treino: {len(textos_treino)} mensagens rotuladas pelas regras (de {len(pool)})")
    print(f"C = {C}, F1 macro na validação cruzada (concordância com as regras) = {busca.best_score_:.3f}")
    print(f"Limiar de certeza = {limiar:.2f}; vão para revisão {tabela.revisao.mean():.1%} das mensagens")
    print(tabela.groupby("origem").revisao.mean().rename("taxa de revisão").to_string())


if __name__ == "__main__":
    main()
