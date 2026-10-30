"""Cliente do Ollama, que roda os modelos no próprio computador, sem custo.

Usa a API HTTP local do Ollama (http://localhost:11434) direto pela biblioteca padrão
do Python. Cada chamada devolve o rótulo, os tokens e a latência.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass

from .prompts import mensagens, sistema
from .taxonomia import ROTULOS

INVALIDO = "invalido"
URL_PADRAO = "http://localhost:11434"


@dataclass
class Predicao:
    rotulo: str
    bruto: str
    tokens_entrada: int
    tokens_saida: int
    latencia_s: float


def extrair_rotulo(bruto: str) -> str:
    """Lê o JSON da resposta; se vier texto solto, procura o nome de uma categoria."""
    trecho = re.search(r"\{.*?\}", bruto, flags=re.S)
    if trecho:
        try:
            valor = str(json.loads(trecho.group(0)).get("categoria", "")).strip()
            if valor in ROTULOS:
                return valor
        except (json.JSONDecodeError, AttributeError):
            pass
    achados = [r for r in ROTULOS if r in bruto]
    return achados[0] if len(achados) == 1 else INVALIDO


class ClienteOllama:
    def __init__(self, modelo: str, url: str | None = None):
        self.modelo = modelo
        self.nome = f"ollama/{modelo}"
        self.url = (url or os.getenv("OLLAMA_URL", URL_PADRAO)).rstrip("/") + "/api/chat"

    def _post(self, corpo: dict) -> dict:
        req = urllib.request.Request(self.url, data=json.dumps(corpo).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())

    def classificar(self, texto: str, exemplos=None) -> Predicao:
        corpo = {
            "model": self.modelo,
            "messages": [{"role": "system", "content": sistema()}, *mensagens(texto, exemplos)],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0, "num_predict": 30},
        }
        inicio = time.perf_counter()
        r = self._post(corpo)
        latencia = time.perf_counter() - inicio
        bruto = r.get("message", {}).get("content", "")
        return Predicao(extrair_rotulo(bruto), bruto, r.get("prompt_eval_count", 0), r.get("eval_count", 0), latencia)
