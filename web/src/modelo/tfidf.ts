import type { Bloco } from "./tipos";

// Equivalente ao `(?u)\b\w\w+\b` do scikit-learn: sequências de 2 ou mais caracteres de palavra.
const TOKEN = /[\p{L}\p{N}_]{2,}/gu;

export function ngramasPalavras(t: string, [min, max]: [number, number]): string[] {
  const tokens = t.match(TOKEN) ?? [];
  const saida: string[] = [];
  for (let n = min; n <= max; n++) {
    for (let i = 0; i + n <= tokens.length; i++) saida.push(tokens.slice(i, i + n).join(" "));
  }
  return saida;
}

/** Mesmo algoritmo do analyzer="char_wb" do scikit-learn, contando por código Unicode. */
export function ngramasCharWb(t: string, [min, max]: [number, number]): string[] {
  const saida: string[] = [];
  for (const palavra of t.split(/\s+/u).filter(Boolean)) {
    const w = Array.from(" " + palavra + " ");
    for (let n = min; n <= max; n++) {
      let offset = 0;
      saida.push(w.slice(offset, offset + n).join(""));
      while (offset + n < w.length) {
        offset += 1;
        saida.push(w.slice(offset, offset + n).join(""));
      }
      if (offset === 0) break;
    }
  }
  return saida;
}

/** TF sublinear vezes idf, normalizado por L2. Devolve índice do vocabulário → peso. */
export function vetorBloco(ngramas: string[], bloco: Bloco): Map<number, number> {
  const contagem = new Map<number, number>();
  for (const g of ngramas) {
    const i = bloco.vocab[g];
    if (i !== undefined) contagem.set(i, (contagem.get(i) ?? 0) + 1);
  }
  const v = new Map<number, number>();
  let soma = 0;
  for (const [i, c] of contagem) {
    const x = (1 + Math.log(c)) * bloco.idf[i];
    v.set(i, x);
    soma += x * x;
  }
  const norma = Math.sqrt(soma);
  if (norma) for (const [i, x] of v) v.set(i, x / norma);
  return v;
}
