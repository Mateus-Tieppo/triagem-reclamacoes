import { normalizar } from "@/modelo/normalizar";
import { regrasQueDisparam } from "@/modelo/regras";
import type { Predicao, RegraExportada } from "@/modelo/tipos";
import { CATEGORIAS, type Categoria, type MensagemTriada, type Painel, type RegraTop } from "./tipos";

/** Id estável pelo conteúdo, para uma correção continuar valendo se a pessoa enviar o mesmo texto de novo. */
function idDoTexto(texto: string, i: number): string {
  let h = 0x811c9dc5;
  for (let k = 0; k < texto.length; k++) h = Math.imul(h ^ texto.charCodeAt(k), 0x01000193);
  return `u${i}-${(h >>> 0).toString(36)}`;
}

/**
 * Monta o mesmo formato do painel da Olist a partir das predições feitas no navegador.
 * Sem datas, não há evolução por mês. As expressões só contam nas filas em que o painel
 * de referência as mostra, porque a ligação entre regra e fila vem do Python.
 */
export function montarPainel(
  textos: string[],
  predicoes: Predicao[],
  regras: RegraExportada[],
  referencia: Pick<Painel, "regras_top">,
): Painel {
  const mensagens: MensagemTriada[] = textos.map((texto, i) => ({
    id: idDoTexto(texto, i),
    texto,
    categoria: predicoes[i].categoria as Categoria,
    certeza: predicoes[i].certeza,
    revisao: predicoes[i].revisao,
    motivo: predicoes[i].motivo,
    palavras: predicoes[i].palavras,
    data: null,
  }));

  const por_categoria = Object.fromEntries(CATEGORIAS.map((c) => [c, 0])) as Record<Categoria, number>;
  for (const m of mensagens) por_categoria[m.categoria] += 1;

  const regras_top: Partial<Record<Categoria, RegraTop[]>> = {};
  for (const c of CATEGORIAS) {
    const conhecidas = referencia.regras_top[c] ?? [];
    if (!conhecidas.length) continue;
    const daFila = mensagens.filter((m) => m.categoria === c).map((m) => new Set(regrasQueDisparam(normalizar(m.texto), regras)));
    const top = conhecidas
      .map((r) => ({ ...r, n: daFila.filter((s) => s.has(r.nome)).length }))
      .filter((r) => r.n > 0)
      .sort((a, b) => b.n - a.n);
    if (top.length) regras_top[c] = top;
  }

  return {
    total: mensagens.length,
    sem_humano: mensagens.filter((m) => !m.revisao).length,
    por_categoria,
    por_mes: [],
    regras_top,
    mensagens,
  };
}
