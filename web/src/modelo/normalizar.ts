// Mesma normalização de src/triagem/normalizar.py. O teste de paridade garante.

export const MARCA_LINK = "_link_";
export const MARCA_NUM = "_num_";

const LINK = /https?:\/\/\S+|www\.\S+|\S+@\S+\.\S+/gu;
const NUM = /(?<![a-z])\p{Nd}+(?:[/.,:-]\p{Nd}+)*/gu;
const REPETIDO = /(.)\1{2,}/gu;
const ESPACOS = /\s+/gu;

export function normalizar(texto: string): string {
  let t = texto.replace(LINK, MARCA_LINK);
  t = t.toLowerCase().normalize("NFKD").replace(/\p{Mn}/gu, "");
  t = t.replace(NUM, MARCA_NUM);
  t = t.replace(REPETIDO, "$1");
  return t.replace(ESPACOS, " ").trim();
}

/** Texto sem nenhuma letra depois de normalizar (só número, emoji ou pontuação). */
export function semConteudo(texto: string): boolean {
  const t = normalizar(texto).replaceAll(MARCA_NUM, "").replaceAll(MARCA_LINK, "");
  return !/[a-z]/.test(t);
}
