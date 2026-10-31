const PREFERIDAS = ["texto", "review_comment_message", "mensagem", "comentario", "reclamacao"];

function semAcento(s: string): string {
  return s.normalize("NFKD").replace(/\p{Mn}/gu, "").toLowerCase().trim();
}

/** Escolhe o separador que mais aparece fora de aspas na primeira linha. */
function separador(conteudo: string): string {
  let dentro = false;
  const conta: Record<string, number> = { ";": 0, ",": 0, "\t": 0 };
  for (const ch of conteudo) {
    if (ch === '"') dentro = !dentro;
    else if (!dentro && (ch === "\n" || ch === "\r")) break;
    else if (!dentro && ch in conta) conta[ch] += 1;
  }
  const [maior, n] = Object.entries(conta).sort((a, b) => b[1] - a[1])[0];
  return n ? maior : ";";
}

/** Lê CSV como o Excel salva: separador ; , ou tab, BOM, aspas com quebra de linha dentro. */
export function lerCsv(conteudo: string): { colunas: string[]; linhas: Record<string, string>[] } {
  const texto = conteudo.replace(/^﻿/, "");
  const sep = separador(texto);
  const registros: string[][] = [];
  let campo = "";
  let registro: string[] = [];
  let dentro = false;

  for (let i = 0; i < texto.length; i++) {
    const ch = texto[i];
    if (dentro) {
      if (ch === '"' && texto[i + 1] === '"') {
        campo += '"';
        i++;
      } else if (ch === '"') dentro = false;
      else campo += ch;
    } else if (ch === '"') dentro = true;
    else if (ch === sep) {
      registro.push(campo);
      campo = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && texto[i + 1] === "\n") i++;
      registro.push(campo);
      registros.push(registro);
      registro = [];
      campo = "";
    } else campo += ch;
  }
  if (campo || registro.length) {
    registro.push(campo);
    registros.push(registro);
  }

  const cheios = registros.filter((r) => r.some((c) => c.trim()));
  const [cabecalho = [], ...resto] = cheios;
  const colunas = cabecalho.map((c, i) => c.trim() || `coluna_${i + 1}`);
  const linhas = resto.map((r) => Object.fromEntries(colunas.map((c, i) => [c, r[i] ?? ""])));
  return { colunas, linhas };
}

/** A coluna que parece ter o texto da reclamação, ou null para a pessoa escolher. */
export function colunaDeTexto(colunas: string[]): string | null {
  for (const p of PREFERIDAS) {
    const achada = colunas.find((c) => semAcento(c) === p);
    if (achada) return achada;
  }
  return null;
}

/** Texto colado: uma reclamação por linha, sem linhas vazias. */
export function linhasColadas(texto: string): string[] {
  return texto
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
}
