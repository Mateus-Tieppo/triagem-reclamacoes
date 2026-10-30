"""Normalização do texto, usada igual nas regras, no treino e na predição."""

from __future__ import annotations

import re
import unicodedata

MARCA_LINK = "_link_"
MARCA_NUM = "_num_"

_LINK = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+")
_NUM = re.compile(r"(?<![a-z])\d+(?:[/.,:-]\d+)*")
_REPETIDO = re.compile(r"(.)\1{2,}")
_ESPACOS = re.compile(r"\s+")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos, links e números como marcadores, letras repetidas reduzidas."""
    t = _LINK.sub(MARCA_LINK, texto)
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = _NUM.sub(MARCA_NUM, t)
    t = _REPETIDO.sub(r"\1", t)
    return _ESPACOS.sub(" ", t).strip()
