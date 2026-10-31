"""Gera os dados do painel da ferramenta web.

    python -m triagem.painel

Usa as predições de results/triagem.csv só das mensagens que o modelo nunca viu e as
datas reais das avaliações. Grava web/public/painel.json.
"""

from __future__ import annotations

import json
from collections import Counter

import pandas as pd

from . import dados
from .exportar_web import nunca_vistas
from .regras import REGRAS, regras_que_disparam

ARQUIVO_PAINEL = dados.RAIZ / "web" / "public" / "painel.json"
N_REGRAS_TOP = 5

ROTULO_LEGIVEL: dict[str, str] = {
    "sem_estoque": "Vendeu sem ter em estoque",
    "nao_recebi": "Não recebi",
    "nao_chegou": "Não chegou",
    "nao_entregue": "Não foi entregue",
    "nao_veio_produto": "Não veio o produto",
    "entrega_nao_realizada": "Entrega não realizada",
    "atrasou": "Atrasou",
    "demorou_chegar": "Demorou para chegar",
    "demora_entrega": "Demora na entrega",
    "prazo_nao_cumprido": "Prazo não cumprido",
    "aguardando_entrega": "Ainda aguardando",
    "quando_entrega": "Quando vai chegar?",
    "so_veio_um": "Só veio um",
    "veio_so_um": "Veio só uma parte",
    "faltando_item": "Faltando item",
    "entrega_parcial": "Entrega parcial",
    "outro_nao_veio": "O outro não veio",
    "um_entregue_outro_nao": "Um chegou, outro não",
    "so_o_primeiro": "Só chegou um dos itens",
    "faltou_o": "Faltou uma peça",
    "nao_chegou_todo": "Não chegou completo",
    "produto_errado": "Produto errado",
    "veio_errado": "Veio errado",
    "diferente_anuncio": "Diferente do anúncio",
    "nao_e_o_mesmo": "Não é o mesmo",
    "veio_outro": "Veio outro produto",
    "nao_original": "Não é original",
    "quebrado": "Chegou quebrado",
    "defeito": "Com defeito",
    "nao_funciona": "Não funciona",
    "ma_qualidade": "Qualidade ruim",
    "parte_ruim": "Parte ruim",
    "acabamento_ruim": "Acabamento ruim",
    "estorno_reembolso": "Estorno ou reembolso",
    "dinheiro_de_volta": "Quero o dinheiro de volta",
    "cancelamento": "Cancelamento",
    "cobranca_indevida": "Cobrança indevida",
    "nao_responde": "A loja não responde",
    "sem_resposta": "Sem resposta",
    "atendimento_ruim": "Atendimento ruim",
    "falta_comunicacao": "Falta de comunicação",
    "elogio": "Elogio",
    "entrega_rapida": "Entrega rápida",
    "ainda_nao_usei": "Ainda não usei",
}


def montar_painel(tri: pd.DataFrame, datas: pd.Series) -> dict:
    """Números, distribuição, evolução por mês, regras mais frequentes e as mensagens."""
    tri = tri.assign(data=tri.review_id.map(datas).astype(str).str[:10])
    tri = tri.assign(mes=tri.data.str[:7])
    categoria_da_regra = {r.nome: r.categoria for r in REGRAS}
    regras_top: dict[str, list[dict]] = {}
    contagens: dict[str, Counter] = {}
    for texto, cat in zip(tri.texto, tri.categoria):
        for nome in regras_que_disparam(texto):
            if categoria_da_regra[nome] == cat:
                contagens.setdefault(cat, Counter())[nome] += 1
    for cat, c in contagens.items():
        regras_top[cat] = [{"nome": n, "rotulo_legivel": ROTULO_LEGIVEL[n], "n": k} for n, k in c.most_common(N_REGRAS_TOP)]
    por_mes = (tri.groupby(["mes", "categoria"]).size().unstack(fill_value=0).sort_index())
    return {
        "total": int(len(tri)),
        "sem_humano": int((~tri.revisao.astype(bool)).sum()),
        "por_categoria": {k: int(v) for k, v in tri.categoria.value_counts().items()},
        "por_mes": [{"mes": m, **{c: int(v) for c, v in linha.items()}} for m, linha in por_mes.iterrows()],
        "regras_top": regras_top,
        "mensagens": [{"id": r.review_id, "texto": r.texto, "categoria": r.categoria, "certeza": float(r.certeza),
                       "revisao": bool(r.revisao), "motivo": "" if pd.isna(r.motivo_revisao) else r.motivo_revisao,
                       "palavras": [] if pd.isna(r.palavras) or not r.palavras else r.palavras.split(", "),
                       "data": r.data} for r in tri.itertuples()],
    }


def main():
    tri = pd.read_csv(dados.RAIZ / "results" / "triagem.csv", dtype={"review_id": str})
    tri = tri[tri.review_id.isin(set(nunca_vistas().review_id))]
    bruto = pd.read_csv(dados.ARQUIVO_BRUTO, usecols=["review_id", "review_creation_date"]).drop_duplicates("review_id")
    datas = bruto.set_index("review_id").review_creation_date
    p = montar_painel(tri, datas)
    ARQUIVO_PAINEL.write_text(json.dumps(p, ensure_ascii=False, separators=(",", ":")))
    print(f"{p['total']} mensagens, {p['sem_humano']} sem humano, {ARQUIVO_PAINEL.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
