"""Escolhe o modelo no conjunto de desenvolvimento e gera a fila com os rótulos do Claude.

    python -m triagem.desenvolvimento

Compara três modelos clássicos (com as regras como variáveis) e três formas de treino no
desenvolvimento rotulado pelo Claude. O melhor por F1 macro vira results/modelo.joblib, a
fila results/triagem.csv e as predições no ouro. O ouro não é lido aqui.
"""

from __future__ import annotations

import json
import time
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from . import dados
from .modelo import CANDIDATOS, GRADES, montar_candidato, palavras_que_pesaram, probabilidades
from .regras import rotular
from .rotulagem import ARQUIVO_ROTULOS
from .selecao import SEED_NOVO
from .triagem import decidir_modelo, escolher_limiar

FORMAS = {"A": None, "B0.1": 0.1, "B0.3": 0.3}


def montar_treino(rotulos: pd.DataFrame, pool: pd.DataFrame, peso_regras: Optional[float]):
    """Textos, rótulos e pesos de treino. O desenvolvimento nunca entra."""
    treino = rotulos[rotulos.grupo != "dev"].merge(pool[["review_id", "texto"]], on="review_id")
    textos, rots = treino.texto.tolist(), treino.rotulo.tolist()
    pesos = [1.0] * len(textos)
    if peso_regras is not None:
        for t in pool[~pool.review_id.isin(rotulos.review_id)].texto:
            v = rotular(t)
            if v.rotulo and not v.conflito:
                textos.append(t)
                rots.append(v.rotulo)
                pesos.append(peso_regras)
    return textos, rots, np.asarray(pesos)


def _f1(y, p) -> float:
    return float(f1_score(y, p, labels=sorted(set(y) | set(p)), average="macro", zero_division=0))


def comparar(rotulos: pd.DataFrame, pool: pd.DataFrame):
    """F1 no desenvolvimento de cada par (modelo, forma de treino) e o melhor estimador de cada um."""
    dev = rotulos[rotulos.grupo == "dev"].merge(pool[["review_id", "texto"]], on="review_id")
    linhas, modelos = [], {}
    for forma, peso in FORMAS.items():
        textos, rots, pesos = montar_treino(rotulos, pool, peso)
        for nome in CANDIDATOS:
            busca = GridSearchCV(montar_candidato(nome), GRADES[nome], scoring="f1_macro", n_jobs=-1,
                                 cv=StratifiedKFold(3, shuffle=True, random_state=SEED_NOVO))
            busca.fit(textos, rots, clf__sample_weight=pesos)
            f1 = _f1(dev.rotulo, busca.best_estimator_.predict(dev.texto.tolist()))
            linhas.append({"modelo": nome, "forma": forma, "f1_dev": f1, "params": busca.best_params_})
            modelos[(nome, forma)] = busca.best_estimator_
            print(f"{nome:10s} forma {forma:5s} F1 no desenvolvimento = {f1:.3f}")
    return pd.DataFrame(linhas), modelos, dev


def _tabela_md(df: pd.DataFrame) -> str:
    md = ["| Modelo | Forma de treino | F1 macro no desenvolvimento | Hiperparâmetros |", "| --- | --- | --- | --- |"]
    for r in df.sort_values("f1_dev", ascending=False).itertuples():
        pct = f"{r.f1_dev * 100:.1f}%".replace(".", ",")
        md.append(f"| {r.modelo} | {r.forma} | {pct} | {r.params} |")
    return "\n".join(md)


def main():
    res = dados.RAIZ / "results"
    pool = dados.pool_de_treino().reset_index(drop=True)
    rotulos = pd.read_csv(ARQUIVO_ROTULOS, dtype={"review_id": str})
    tabela, modelos, dev = comparar(rotulos, pool)
    melhor = tabela.sort_values("f1_dev", ascending=False).iloc[0]
    modelo = modelos[(melhor.modelo, melhor.forma)]
    limiar = escolher_limiar(probabilidades(modelo, dev.texto.tolist()), dev.rotulo.tolist())

    (res / "desenvolvimento.md").write_text(
        f"## Escolha no desenvolvimento ({len(dev)} mensagens rotuladas pelo Claude)\n\n"
        "Forma A: só os rótulos do Claude. Forma B: mais os rótulos das regras no resto do pool, com o peso indicado.\n\n"
        + _tabela_md(tabela) + f"\n\nEscolhido: {melhor.modelo}, forma {melhor.forma}. Limiar de certeza: {limiar:.1f}.\n")
    # O joblib é gerado aqui mesmo e lido só pelo projeto.
    joblib.dump({"modelo": modelo, "limiar": limiar, "nome": melhor.modelo, "forma": melhor.forma,
                 "f1_dev": float(melhor.f1_dev)}, res / "modelo.joblib")

    probas = probabilidades(modelo, pool.texto.tolist())
    linhas = []
    for i, r in enumerate(pool.itertuples()):
        d = decidir_modelo(probas.iloc[i], limiar, r.texto)
        linhas.append({"review_id": r.review_id, "texto": r.texto, "categoria": d.categoria, "origem": d.origem,
                       "regra": "", "certeza": round(d.certeza, 4), "revisao": d.revisao,
                       "motivo_revisao": d.motivo_revisao,
                       "palavras": ", ".join(palavras_que_pesaram(modelo, r.texto, d.categoria))})
    fila = pd.DataFrame(linhas)
    fila.to_csv(res / "triagem.csv", index=False)

    for antigo in (res / "preds").glob("ouro__rotulos-claude__*.jsonl"):
        antigo.unlink()
    ouro = dados.amostra_ouro(dados.reclamacoes())
    saida = []
    for r in ouro.itertuples():
        t0 = time.perf_counter()
        d = decidir_modelo(probabilidades(modelo, [r.texto]).iloc[0], limiar, r.texto)
        saida.append({"review_id": r.review_id, "pred": d.categoria, "latencia_s": round(time.perf_counter() - t0, 6),
                      "revisao": d.revisao})
    arq = res / "preds" / f"ouro__rotulos-claude__{melhor.modelo}__forma-{melhor.forma}.jsonl"
    arq.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in saida))

    print(f"Escolhido: {melhor.modelo}, forma {melhor.forma}, F1 no desenvolvimento {melhor.f1_dev:.3f}")
    print(f"Limiar {limiar:.1f}; vão para revisão {fila.revisao.mean():.1%} do pool")


if __name__ == "__main__":
    main()
