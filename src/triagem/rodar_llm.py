"""Roda um modelo local (Ollama) sobre o conjunto ouro (avaliação) ou sobre o pool de treino (rótulos prata).

Exemplos:
    python -m triagem.rodar_llm --modelo qwen2.5:7b --modo zero
    python -m triagem.rodar_llm --modelo qwen2.5:7b --modo few
    python -m triagem.rodar_llm --modelo qwen2.5:7b --modo few --conjunto prata --n 2000

As predições vão para results/preds/*.jsonl, uma linha por mensagem. Se o arquivo já
existir, o script continua de onde parou.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from . import dados
from .llm import ClienteOllama

PASTA = dados.RAIZ / "results" / "preds"


def arquivo_saida(modelo: str, modo: str, conjunto: str) -> Path:
    seguro = modelo.replace("/", "_").replace(":", "-")
    return PASTA / f"{conjunto}__ollama__{seguro}__{modo}.jsonl"


def exemplos_fewshot() -> list[tuple[str, str]]:
    fs = pd.read_csv(dados.ARQUIVO_FEWSHOT)
    return list(zip(fs.texto, fs.rotulo))


def textos(conjunto: str, n: int | None) -> pd.DataFrame:
    if conjunto == "ouro":
        return dados.carregar_ouro()[["review_id", "texto"]]
    pool = dados.reclamacoes()
    ouro = set(dados.carregar_ouro().review_id)
    fs = set(pd.read_csv(dados.ARQUIVO_FEWSHOT).review_id)
    treino = dados.pool_treino(pool, ouro, fs)
    return treino.sample(n or 2000, random_state=dados.SEED)[["review_id", "texto"]]


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--modelo", required=True, help="nome do modelo no Ollama, ex.: qwen2.5:7b")
    p.add_argument("--modo", choices=["zero", "few"], default="zero")
    p.add_argument("--conjunto", choices=["ouro", "prata"], default="ouro")
    p.add_argument("--n", type=int, default=None, help="tamanho do conjunto prata")
    a = p.parse_args(argv)

    cliente = ClienteOllama(a.modelo)
    exemplos = exemplos_fewshot() if a.modo == "few" else None
    saida = arquivo_saida(a.modelo, a.modo, a.conjunto)
    saida.parent.mkdir(parents=True, exist_ok=True)
    feitos = set()
    if saida.exists():
        feitos = {json.loads(l)["review_id"] for l in saida.read_text().splitlines() if l.strip()}

    df = textos(a.conjunto, a.n)
    pendentes = df[~df.review_id.isin(feitos)]
    print(f"{cliente.nome} [{a.modo}] em {a.conjunto}: {len(feitos)} prontas, {len(pendentes)} pendentes")
    with saida.open("a") as f:
        for i, r in enumerate(pendentes.itertuples(), 1):
            for tentativa in range(3):
                try:
                    pr = cliente.classificar(r.texto, exemplos)
                    break
                except OSError as e:  # Ollama fora do ar ou demorou demais
                    if tentativa == 2:
                        raise
                    print(f"  erro ({e.__class__.__name__}), tentando de novo")
                    time.sleep(2 ** (tentativa + 1))
            f.write(json.dumps({
                "review_id": r.review_id, "pred": pr.rotulo, "bruto": pr.bruto,
                "tokens_entrada": pr.tokens_entrada, "tokens_saida": pr.tokens_saida,
                "latencia_s": round(pr.latencia_s, 4),
            }, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(pendentes)}")
    print(f"Salvo em {saida}")


if __name__ == "__main__":
    main()
