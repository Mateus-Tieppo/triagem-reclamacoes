"""Prompts zero-shot e few-shot. A saída pedida é um JSON com uma chave."""

from __future__ import annotations

import json

from .taxonomia import CATEGORIAS, REGRAS


def sistema() -> str:
    linhas = "\n".join(f"- {k}: {v}" for k, v in CATEGORIAS.items())
    return (
        "Você faz a triagem de reclamações de clientes de um e-commerce brasileiro.\n"
        "Classifique cada mensagem em exatamente uma categoria:\n"
        f"{linhas}\n\n"
        f"Regras:\n{REGRAS}\n"
        'Responda só com JSON no formato {"categoria": "<uma das categorias acima>"}.'
    )


def mensagens(texto: str, exemplos: list[tuple[str, str]] | None = None) -> list[dict]:
    """Monta a conversa. No few-shot, cada exemplo vira um par usuário/assistente."""
    msgs: list[dict] = []
    for ex_texto, ex_rotulo in exemplos or []:
        msgs.append({"role": "user", "content": f"Mensagem: {ex_texto}"})
        msgs.append({"role": "assistant", "content": json.dumps({"categoria": ex_rotulo})})
    msgs.append({"role": "user", "content": f"Mensagem: {texto}"})
    return msgs
