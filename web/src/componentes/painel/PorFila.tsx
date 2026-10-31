import Link from "next/link";
import { useMemo } from "react";
import { Etiqueta } from "@/componentes/Etiqueta";
import { numero } from "@/dados/formato";
import { CATEGORIAS, FILAS, type Categoria, type MensagemTriada } from "@/dados/tipos";
import estilos from "./PorFila.module.css";

/** Uma linha por fila, da maior para a menor. Clicar abre a fila. */
export function PorFila({ mensagens }: { mensagens: MensagemTriada[] }) {
  const linhas = useMemo(() => {
    const conta = new Map<Categoria, { total: number; revisao: number }>(CATEGORIAS.map((c) => [c, { total: 0, revisao: 0 }]));
    for (const m of mensagens) {
      const c = conta.get(m.categoria)!;
      c.total += 1;
      if (m.revisao) c.revisao += 1;
    }
    return [...conta].map(([categoria, c]) => ({ categoria, ...c })).sort((a, b) => b.total - a.total);
  }, [mensagens]);
  const maior = Math.max(1, ...linhas.map((l) => l.total));

  return (
    <section aria-labelledby="por-fila" className={estilos.secao}>
      <h2 id="por-fila" className={estilos.titulo}>
        Para onde vão
      </h2>
      <ol className={estilos.lista}>
        {linhas.map((l) => (
          <li key={l.categoria}>
            <Link href={`/filas?fila=${FILAS[l.categoria].codigo}`} className={estilos.linha}>
              <Etiqueta categoria={l.categoria} />
              <span className={estilos.nome}>
                {FILAS[l.categoria].nome}
                <span className={`${estilos.time} apoio`}>{FILAS[l.categoria].time}</span>
              </span>
              <span className={estilos.trilho} aria-hidden>
                <span className={estilos.barra} style={{ inlineSize: `${(l.total / maior) * 100}%` }} />
              </span>
              <span className={estilos.numeros}>
                <span className={estilos.total}>{numero.format(l.total)}</span>
                <span className={`${estilos.revisao} codigo`}>
                  {l.revisao ? `${numero.format(l.revisao)} p/ revisão` : "nenhuma p/ revisão"}
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
