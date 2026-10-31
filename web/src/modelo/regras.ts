import type { RegraExportada } from "./tipos";

const compiladas = new WeakMap<RegraExportada[], { nome: string; re: RegExp }[]>();

// As regras vêm do Python. O `\w` do Python considera letras de qualquer alfabeto,
// então vira uma classe Unicode; o resto da sintaxe é igual no JavaScript.
function compilar(regras: RegraExportada[]) {
  let c = compiladas.get(regras);
  if (!c) {
    c = regras.map((r) => ({ nome: r.nome, re: new RegExp(r.padrao.replaceAll("\\w", "[\\p{L}\\p{N}_]"), "u") }));
    compiladas.set(regras, c);
  }
  return c;
}

/** Nomes das regras que disparam no texto já normalizado. */
export function regrasQueDisparam(textoNormalizado: string, regras: RegraExportada[]): string[] {
  return compilar(regras)
    .filter((r) => r.re.test(textoNormalizado))
    .map((r) => r.nome);
}
