import { normalizar, semConteudo } from "./normalizar";
import { regrasQueDisparam } from "./regras";
import { ngramasCharWb, ngramasPalavras, vetorBloco } from "./tfidf";
import type { Modelo, Motivo, Predicao } from "./tipos";

const TAMANHO_LOTE = 200;

/** Prediz como o pipeline do scikit-learn: TF-IDF de palavras e caracteres, regras, softmax. */
export function prever(modelo: Modelo, texto: string): Predicao {
  const t = normalizar(texto);
  const palavras = vetorBloco(ngramasPalavras(t, modelo.palavras.ngram), modelo.palavras);
  const caracteres = vetorBloco(ngramasCharWb(t, modelo.caracteres.ngram), modelo.caracteres);
  const nPal = modelo.palavras.idf.length;
  const nCar = modelo.caracteres.idf.length;

  const x = new Map<number, number>(palavras);
  for (const [i, v] of caracteres) x.set(nPal + i, v);
  const disparadas = new Set(regrasQueDisparam(t, modelo.regras));
  modelo.regras.forEach((r, j) => {
    if (disparadas.has(r.nome)) x.set(nPal + nCar + j, 1);
  });

  const escores = modelo.coef.map((linha, k) => {
    let s = modelo.intercepto[k];
    for (const [i, v] of x) s += linha[i] * v;
    return s;
  });
  const maior = Math.max(...escores);
  const exps = escores.map((s) => Math.exp(s - maior));
  const total = exps.reduce((a, b) => a + b, 0);
  const probas: Record<string, number> = {};
  modelo.classes.forEach((c, k) => (probas[c] = exps[k] / total));

  const k = escores.indexOf(maior);
  const categoria = modelo.classes[k];
  const certeza = probas[categoria];
  const motivo: Motivo = semConteudo(texto) ? "texto sem conteúdo" : certeza < modelo.limiar ? "certeza baixa" : "";
  return { categoria, probas, certeza, revisao: motivo !== "", motivo, palavras: palavrasQuePesaram(modelo, palavras, k) };
}

function palavrasQuePesaram(modelo: Modelo, palavras: Map<number, number>, k: number, n = 3): string[] {
  const termos = Object.keys(modelo.palavras.vocab);
  const porIndice = new Map(termos.map((t) => [modelo.palavras.vocab[t], t]));
  return [...palavras]
    .map(([i, v]) => ({ i, contrib: v * modelo.coef[k][i] }))
    .filter((c) => c.contrib > 0)
    .sort((a, b) => b.contrib - a.contrib)
    .slice(0, n)
    .map((c) => porIndice.get(c.i) ?? "");
}

/** Prediz em lotes, cedendo a vez ao navegador entre eles para a tela não travar. */
export async function preverEmLotes(
  modelo: Modelo,
  textos: string[],
  aoProgredir: (feitos: number) => void,
): Promise<Predicao[]> {
  const saida: Predicao[] = [];
  for (let i = 0; i < textos.length; i += TAMANHO_LOTE) {
    for (const t of textos.slice(i, i + TAMANHO_LOTE)) saida.push(prever(modelo, t));
    aoProgredir(saida.length);
    await new Promise((r) => setTimeout(r, 0));
  }
  return saida;
}
