import type { MensagemTriada } from "./tipos";

export type Resumo = { total: number; semHumano: number; pctSemHumano: number; horasPoupadas: number };

/** Números do topo do painel. Horas poupadas são estimativa: mensagens sem humano vezes a premissa. */
export function calcularResumo(mensagens: Pick<MensagemTriada, "revisao">[], segundosPorMensagem: number): Resumo {
  const total = mensagens.length;
  const semHumano = mensagens.filter((m) => !m.revisao).length;
  const segundos = Number.isFinite(segundosPorMensagem) && segundosPorMensagem > 0 ? segundosPorMensagem : 0;
  return {
    total,
    semHumano,
    pctSemHumano: total ? semHumano / total : 0,
    horasPoupadas: (semHumano * segundos) / 3600,
  };
}
