import { CATEGORIAS, type Categoria, type MensagemTriada } from "./tipos";

const CHAVE = "triia:correcoes";
const memoria: Record<string, string> = {};

/** A categoria escolhida por uma pessoa vence a do modelo e tira a mensagem da revisão. */
export function aplicarCorrecoes(msgs: MensagemTriada[], correcoes: Record<string, string>): MensagemTriada[] {
  return msgs.map((m) => {
    const nova = correcoes[m.id];
    if (!nova || !(CATEGORIAS as readonly string[]).includes(nova)) return m;
    return { ...m, categoria: nova as Categoria, revisao: false, corrigida: true };
  });
}

/** Lê as correções salvas. Sem localStorage (modo privado, bloqueado), usa as da memória. */
export function lerCorrecoes(): Record<string, string> {
  try {
    const salvo = JSON.parse(localStorage.getItem(CHAVE) ?? "{}");
    return typeof salvo === "object" && salvo ? { ...salvo, ...memoria } : { ...memoria };
  } catch {
    return { ...memoria };
  }
}

export function salvarCorrecao(id: string, categoria: string): void {
  memoria[id] = categoria;
  try {
    localStorage.setItem(CHAVE, JSON.stringify(lerCorrecoes()));
  } catch {
    // Sem localStorage a correção vale até fechar a aba.
  }
}
