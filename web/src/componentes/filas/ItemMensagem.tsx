import { memo } from "react";
import { Etiqueta } from "@/componentes/Etiqueta";
import { CATEGORIAS, FILAS, type Categoria, type MensagemTriada } from "@/dados/tipos";
import estilos from "./ItemMensagem.module.css";

/** Os marcadores da normalização viram palavras para quem lê. */
const legivel = (p: string) => p.replace(/_num_/g, "número").replace(/_link_/g, "link");

const data = new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium", timeZone: "UTC" });

export const ItemMensagem = memo(function ItemMensagem({
  m,
  onMover,
}: {
  m: MensagemTriada;
  onMover: (id: string, categoria: Categoria) => void;
}) {
  const campo = `mover-${m.id}`;
  return (
    <article className={estilos.item}>
      <div className={estilos.topo}>
        <Etiqueta categoria={m.categoria} certeza={m.corrigida ? undefined : m.certeza} />
        {m.revisao ? (
          <span className={`${estilos.carimbo} codigo`}>Revisão · {m.motivo}</span>
        ) : null}
        {m.corrigida ? <span className={`${estilos.corrigida} codigo`}>movida por você</span> : null}
        {m.data ? (
          <time className={`${estilos.data} codigo`} dateTime={m.data}>
            {data.format(new Date(m.data))}
          </time>
        ) : null}
      </div>
      <p className={estilos.texto}>{m.texto || <span className="apoio">(sem texto)</span>}</p>
      <div className={estilos.rodape}>
        {m.palavras.length && !m.corrigida ? (
          <p className={`${estilos.porque} apoio`}>
            Por quê:{" "}
            {m.palavras.map((p, i) => (
              <span key={p}>
                {i ? ", " : ""}
                <mark className={estilos.palavra}>{legivel(p)}</mark>
              </span>
            ))}
          </p>
        ) : (
          <span />
        )}
        <span className={estilos.mover}>
          {m.revisao ? (
            <button type="button" className={estilos.confirmar} onClick={() => onMover(m.id, m.categoria)}>
              Confirmar {FILAS[m.categoria].codigo}
            </button>
          ) : null}
          <label htmlFor={campo} className="apoio">
            Mover para
          </label>
          <select
            id={campo}
            value={m.categoria}
            onChange={(e) => onMover(m.id, e.target.value as Categoria)}
            className={estilos.select}
          >
            {CATEGORIAS.map((c) => (
              <option key={c} value={c}>
                {FILAS[c].codigo} · {FILAS[c].nome}
              </option>
            ))}
          </select>
        </span>
      </div>
    </article>
  );
});
