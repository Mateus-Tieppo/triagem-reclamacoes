import { useMemo } from "react";
import { Etiqueta } from "@/componentes/Etiqueta";
import { numero } from "@/dados/formato";
import { FILAS, type Categoria, type Painel } from "@/dados/tipos";
import estilos from "./Problemas.module.css";

const LIMITE_EXEMPLO = 140;

/** As expressões que mais disparam em cada fila, com uma reclamação de exemplo. */
export function Problemas({ painel }: { painel: Painel }) {
  const blocos = useMemo(() => {
    const ordem = (Object.keys(painel.regras_top) as Categoria[])
      .filter((c) => painel.regras_top[c]?.length)
      .sort((a, b) => (painel.por_categoria[b] ?? 0) - (painel.por_categoria[a] ?? 0))
      .slice(0, 4);
    return ordem.map((c) => {
      const exemplo = painel.mensagens
        .filter((m) => m.categoria === c && !m.revisao && m.texto.length >= 40 && m.texto.length <= LIMITE_EXEMPLO)
        .sort((a, b) => b.certeza - a.certeza)[0];
      return { categoria: c, regras: painel.regras_top[c]!, exemplo };
    });
  }, [painel]);

  if (!blocos.length) return null;

  return (
    <section aria-labelledby="problemas">
      <h2 id="problemas" className={estilos.titulo}>
        Problemas que mais aparecem
      </h2>
      <p className="apoio">Expressões que o modelo reconhece em cada fila e quantas vezes apareceram.</p>
      <div className={estilos.grade}>
        {blocos.map((b) => (
          <article key={b.categoria} className={estilos.bloco}>
            <h3 className={estilos.fila}>
              <Etiqueta categoria={b.categoria} /> {FILAS[b.categoria].nome}
            </h3>
            <ul className={estilos.regras}>
              {b.regras.map((r) => (
                <li key={r.nome}>
                  <span>{r.rotulo_legivel}</span>
                  <span className="codigo">{numero.format(r.n)}</span>
                </li>
              ))}
            </ul>
            {b.exemplo ? <blockquote className={estilos.exemplo}>“{b.exemplo.texto}”</blockquote> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
