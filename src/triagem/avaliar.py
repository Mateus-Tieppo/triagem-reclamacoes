"""Junta todas as predições no ouro e gera a tabela de resultados.

    python -m triagem.avaliar

Para cada abordagem: acurácia, F1 macro (com intervalo de 95% por bootstrap),
F1 só nas mensagens rotuladas pelo Mateus, taxa de respostas inválidas e latência.
Tudo roda localmente, então não há custo por chamada.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from . import dados
from .llm import INVALIDO
from .taxonomia import ROTULOS
from .verdade import ARQUIVO_PEDIDOS, conferir_atraso

PASTA_PREDS = dados.RAIZ / "results" / "preds"
PASTA_RES = dados.RAIZ / "results"


def ler_preds(caminho: Path) -> pd.DataFrame:
    return pd.DataFrame([json.loads(l) for l in caminho.read_text().splitlines() if l.strip()])


def nome_abordagem(caminho: Path) -> tuple[str, str, str]:
    _, provedor, modelo, modo = caminho.stem.split("__")
    return provedor, modelo, modo


def f1_bootstrap(y, p, n=1000, seed=dados.SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    y, p = np.asarray(y), np.asarray(p)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        vals.append(f1_score(y[idx], p[idx], labels=ROTULOS, average="macro", zero_division=0))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def avaliar(ouro: pd.DataFrame, preds: pd.DataFrame) -> dict:
    m = ouro.merge(preds, on="review_id", how="left")
    m["pred"] = m.pred.fillna(INVALIDO)
    # Resposta inválida cai em "outro", como faria um sistema em produção.
    # Assim ela pesa na precisão de "outro" em vez de sumir da conta.
    m["pred_final"] = m.pred.replace(INVALIDO, "outro")
    y, p = m.rotulo, m.pred_final
    baixo, alto = f1_bootstrap(y, p)
    seguro = m[~m.duvida.astype(bool)]
    humano = m[m.fonte == "mateus"] if "fonte" in m else m.iloc[0:0]
    if "revisao" in m:
        aceitas = m[~m.revisao.fillna(True).astype(bool)]
        presentes = sorted(set(aceitas.rotulo) | set(aceitas.pred_final))
        taxa_revisao = float(1 - len(aceitas) / len(m))
        f1_aceitas = f1_score(aceitas.rotulo, aceitas.pred_final, labels=presentes, average="macro", zero_division=0) if len(aceitas) else float("nan")
    else:
        taxa_revisao = f1_aceitas = float("nan")
    return {
        "n": len(m),
        "acuracia": accuracy_score(y, p),
        "f1_macro": f1_score(y, p, labels=ROTULOS, average="macro", zero_division=0),
        "f1_ic95": (baixo, alto),
        "f1_sem_duvida": f1_score(seguro.rotulo, seguro.pred_final, labels=ROTULOS, average="macro", zero_division=0),
        "f1_humano": f1_score(humano.rotulo, humano.pred_final, labels=ROTULOS, average="macro", zero_division=0) if len(humano) else float("nan"),
        "invalidas": float((m.pred == INVALIDO).mean()),
        "latencia_mediana_ms": float(m.latencia_s.median() * 1000),
        "taxa_revisao": taxa_revisao,
        "f1_aceitas": f1_aceitas,
        "f1_por_classe": dict(zip(ROTULOS, f1_score(y, p, labels=ROTULOS, average=None, zero_division=0))),
        "matriz": confusion_matrix(y, m.pred, labels=ROTULOS + [INVALIDO]),
    }


def desenhar_matriz(matriz, titulo: str, caminho: Path):
    rot = ROTULOS + [INVALIDO]
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.imshow(matriz, cmap="Greens")
    ax.set_xticks(range(len(rot)), rot, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(rot)), rot, fontsize=8)
    ax.set_xlabel("predito")
    ax.set_ylabel("rótulo humano")
    for i in range(len(rot)):
        for j in range(len(rot)):
            if matriz[i, j]:
                ax.text(j, i, matriz[i, j], ha="center", va="center", fontsize=8,
                        color="white" if matriz[i, j] > matriz.max() / 2 else "black")
    ax.set_title(titulo, fontsize=10)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def fmt_pct(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def tabela_md(df: pd.DataFrame, indice: bool = False) -> str:
    """Tabela em Markdown sem depender do pacote tabulate."""
    if indice:
        df = df.reset_index().rename(columns={"index": ""})
    cab = [str(c) for c in df.columns]
    linhas = ["| " + " | ".join(cab) + " |", "| " + " | ".join("---" for _ in cab) + " |"]
    for row in df.itertuples(index=False):
        linhas.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(linhas)


def secao_aviso(ouro: pd.DataFrame) -> list[str]:
    """Aviso de que parte do ouro foi rotulada pelo mesmo Claude que rotulou o treino do modelo novo."""
    n = int((ouro.fonte == "claude").sum())
    return [f"Atenção: {n} das {len(ouro)} mensagens do ouro foram rotuladas pelo Claude, que também rotulou o treino "
            "do modelo novo (`rotulos-claude`). A comparação honesta com o Qwen é na coluna das rotuladas pelo Mateus.", ""]


def secao_desenvolvimento() -> list[str]:
    """F1 no desenvolvimento do modelo escolhido, para comparar com o F1 no ouro."""
    arq = PASTA_RES / "modelo.joblib"
    if not arq.exists():
        return []
    # O joblib é gerado pelo próprio projeto (`make treinar`).
    m = joblib.load(arq)
    return [f"F1 macro no desenvolvimento do modelo escolhido ({m['nome']}, forma {m['forma']}): "
            f"{fmt_pct(m['f1_dev'])}. Detalhes em `results/desenvolvimento.md`.", ""]


def secao_regras() -> list[str]:
    """Linhas de cobertura copiadas de results/regras.md."""
    arq = PASTA_RES / "regras.md"
    if not arq.exists():
        return []
    linhas = [l for l in arq.read_text().splitlines() if l.startswith(("| Sem rótulo", "| Com conflito"))]
    return ["### Cobertura das regras no pool de treino", "", "| | Mensagens |", "| --- | --- |", *linhas, ""]


def secao_atraso() -> list[str]:
    """Conferência de atraso com as datas reais, se o arquivo de pedidos existir."""
    md = ["### Conferência de atraso com datas reais de entrega", ""]
    tri = PASTA_RES / "triagem.csv"
    if not ARQUIVO_PEDIDOS.exists() or not tri.exists():
        return md + ["Pulada: falta `data/raw/olist_orders_dataset.csv` (base pública da Olist no Kaggle).", ""]
    r = conferir_atraso(pd.read_csv(tri), pd.read_csv(ARQUIVO_PEDIDOS))
    return md + [f"Entre as {r['n_atraso']} mensagens do pool classificadas como `nao_recebido_atraso`, "
                 f"{fmt_pct(r['pct_atrasado_entre_atraso'])} são de pedidos de fato atrasados ou não entregues, "
                 f"contra {fmt_pct(r['pct_atrasado_geral'])} no pool todo.", ""]


def main():
    ouro = dados.carregar_ouro()
    linhas, detalhes = [], {}
    for arq in sorted(PASTA_PREDS.glob("ouro__*.jsonl")):
        provedor, modelo, modo = nome_abordagem(arq)
        chave = f"{provedor}/{modelo}"
        preds = ler_preds(arq)
        r = avaliar(ouro, preds)
        nome = f"{chave} ({modo})"
        detalhes[nome] = r
        linhas.append({
            "Abordagem": nome,
            "Acurácia": fmt_pct(r["acuracia"]),
            "F1 macro": f"{fmt_pct(r['f1_macro'])} ({fmt_pct(r['f1_ic95'][0])} a {fmt_pct(r['f1_ic95'][1])})",
            "F1 sem dúvida": fmt_pct(r["f1_sem_duvida"]),
            "F1 nas 53 humanas": fmt_pct(r["f1_humano"]),
            "Inválidas": fmt_pct(r["invalidas"]),
            "Revisão": "-" if pd.isna(r["taxa_revisao"]) else fmt_pct(r["taxa_revisao"]),
            "F1 sem revisão": "-" if pd.isna(r["f1_aceitas"]) else fmt_pct(r["f1_aceitas"]),
            "Latência mediana": f"{r['latencia_mediana_ms']:.0f} ms" if r["latencia_mediana_ms"] >= 1 else "< 1 ms",
            "_f1": r["f1_macro"],
        })
        desenhar_matriz(r["matriz"], nome, PASTA_RES / f"matriz__{arq.stem.split('__', 1)[1]}.png")

    if not linhas:
        print("Nenhuma predição em results/preds/. Rode triagem.rodar_llm ou triagem.baseline antes.")
        return
    tab = pd.DataFrame(linhas).sort_values("_f1", ascending=False).drop(columns="_f1")
    por_classe = pd.DataFrame({k: v["f1_por_classe"] for k, v in detalhes.items()}).map(fmt_pct)

    md = ["## Resultados no conjunto ouro", "",
          f"{len(ouro)} mensagens no conjunto ouro ({int((ouro.fonte == 'mateus').sum())} rotuladas pelo Mateus, o resto pelo Claude); "
          f"{int(ouro.duvida.sum())} marcadas como dúvida. "
          "F1 macro com intervalo de 95% por bootstrap (1.000 reamostragens).", "",
          tabela_md(tab), "", "### F1 por categoria", "", tabela_md(por_classe, indice=True), ""]
    md += secao_aviso(ouro) + secao_desenvolvimento() + secao_regras() + secao_atraso()
    (PASTA_RES / "resultados.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
