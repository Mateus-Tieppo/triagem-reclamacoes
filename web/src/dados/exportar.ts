import type { MensagemTriada } from "./tipos";

const CABECALHO = ["id", "texto", "categoria", "certeza", "revisao", "motivo"];

function celula(valor: string): string {
  // Planilhas executam células que começam com estes caracteres como fórmula.
  const seguro = /^[=+\-@\t\r]/.test(valor) ? `'${valor}` : valor;
  return /[;"\n\r]/.test(seguro) ? `"${seguro.replace(/"/g, '""')}"` : seguro;
}

/** CSV no formato que o Excel em português abre direto: ponto e vírgula, vírgula decimal e BOM. */
export function paraCsv(msgs: MensagemTriada[]): string {
  const linhas = msgs.map((m) =>
    [m.id, m.texto, m.categoria, m.certeza.toFixed(2).replace(".", ","), m.revisao ? "sim" : "nao", m.motivo]
      .map((v) => celula(String(v)))
      .join(";"),
  );
  return "﻿" + [CABECALHO.join(";"), ...linhas].join("\r\n");
}

/** Entrega o CSV para o navegador baixar. */
export function baixarCsv(nome: string, conteudo: string): void {
  const url = URL.createObjectURL(new Blob([conteudo], { type: "text/csv;charset=utf-8" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: nome });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
