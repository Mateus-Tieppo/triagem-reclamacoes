import { CATEGORIAS, type Painel } from "@/dados/tipos";
import { mesCurto, numero } from "@/dados/formato";
import estilos from "./PorMes.module.css";

const ALTURA = 160;

/** Colunas com o volume de reclamações por mês. */
export function PorMes({ porMes }: { porMes: Painel["por_mes"] }) {
  if (porMes.length < 2) return null;
  const meses = porMes.map((m) => ({ mes: m.mes, total: CATEGORIAS.reduce((s, c) => s + (m[c] ?? 0), 0) }));
  const pico = meses.reduce((a, b) => (b.total > a.total ? b : a));
  const largura = meses.length * 24;
  const marcas = meses.filter((m, i) => i === 0 || i === meses.length - 1 || m.mes.endsWith("-01"));

  return (
    <section aria-labelledby="por-mes" className={estilos.secao}>
      <h2 id="por-mes" className={estilos.titulo}>
        Ao longo do tempo
      </h2>
      <p className="apoio">
        Pico em {mesCurto(pico.mes)}, com {numero.format(pico.total)} reclamações.
      </p>
      <figure className={estilos.figura}>
        <svg
          viewBox={`0 0 ${largura} ${ALTURA + 22}`}
          className={estilos.grafico}
          role="img"
          aria-label={`Reclamações por mês, de ${mesCurto(meses[0].mes)} a ${mesCurto(meses.at(-1)!.mes)}. Pico em ${mesCurto(pico.mes)} com ${pico.total}.`}
        >
          <line x1="0" x2={largura} y1={ALTURA} y2={ALTURA} className={estilos.base} />
          {meses.map((m, i) => {
            const h = Math.max(1, (m.total / pico.total) * (ALTURA - 8));
            return (
              <rect
                key={m.mes}
                x={i * 24 + 4}
                y={ALTURA - h}
                width={16}
                height={h}
                rx={2}
                className={m === pico ? estilos.pico : estilos.coluna}
              >
                <title>{`${mesCurto(m.mes)}: ${numero.format(m.total)}`}</title>
              </rect>
            );
          })}
          {marcas.map((m) => (
            <text key={m.mes} x={meses.indexOf(m) * 24 + 12} y={ALTURA + 16} className={estilos.rotulo}>
              {mesCurto(m.mes)}
            </text>
          ))}
        </svg>
      </figure>
    </section>
  );
}
