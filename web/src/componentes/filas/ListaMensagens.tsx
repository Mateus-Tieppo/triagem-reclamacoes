"use client";

import { useCallback, useDeferredValue, useId, useMemo, useState } from "react";
import { baixarCsv, paraCsv } from "@/dados/exportar";
import { normalizar } from "@/modelo/normalizar";
import { numero } from "@/dados/formato";
import { FILAS, type Categoria, type MensagemTriada } from "@/dados/tipos";
import { ItemMensagem } from "./ItemMensagem";
import estilos from "./ListaMensagens.module.css";

const POR_PAGINA = 30;

/** Lista com busca, paginação, mover de fila e exportação do que está filtrado. */
export function ListaMensagens({
  mensagens,
  onMover,
  arquivo,
  vazio,
}: {
  mensagens: MensagemTriada[];
  onMover: (id: string, categoria: Categoria) => void;
  arquivo: string;
  vazio: string;
}) {
  const [busca, setBusca] = useState("");
  const [mostrar, setMostrar] = useState(POR_PAGINA);
  const [aviso, setAviso] = useState("");
  const campo = useId();
  const termo = useDeferredValue(busca);

  const filtradas = useMemo(() => {
    const t = normalizar(termo);
    return t ? mensagens.filter((m) => normalizar(m.texto).includes(t)) : mensagens;
  }, [mensagens, termo]);

  const mover = useCallback(
    (id: string, categoria: Categoria) => {
      onMover(id, categoria);
      setAviso(`Movida para ${FILAS[categoria].nome}.`);
    },
    [onMover],
  );

  return (
    <div>
      <div className={estilos.ferramentas}>
        <label htmlFor={campo} className={estilos.busca}>
          <span className="apoio">Buscar no texto</span>
          <input
            id={campo}
            type="search"
            value={busca}
            onChange={(e) => {
              setBusca(e.target.value);
              setMostrar(POR_PAGINA);
            }}
            placeholder="ex.: não chegou"
            autoComplete="off"
            spellCheck={false}
          />
        </label>
        <button
          type="button"
          className={estilos.exportar}
          disabled={!filtradas.length}
          onClick={() => baixarCsv(arquivo, paraCsv(filtradas))}
        >
          Exportar {numero.format(filtradas.length)} em CSV
        </button>
      </div>
      <p className={`${estilos.contagem} codigo`} aria-live="polite">
        {numero.format(filtradas.length)} {filtradas.length === 1 ? "reclamação" : "reclamações"}
        {aviso ? ` · ${aviso}` : ""}
      </p>
      {filtradas.length ? (
        <ol className={estilos.lista}>
          {filtradas.slice(0, mostrar).map((m) => (
            <li key={m.id}>
              <ItemMensagem m={m} onMover={mover} />
            </li>
          ))}
        </ol>
      ) : (
        <p className={estilos.vazio}>{termo ? "Nenhuma reclamação com esse texto." : vazio}</p>
      )}
      {mostrar < filtradas.length ? (
        <button type="button" className={estilos.mais} onClick={() => setMostrar((n) => n + POR_PAGINA)}>
          Mostrar mais {Math.min(POR_PAGINA, filtradas.length - mostrar)}
          <span className="apoio"> de {numero.format(filtradas.length - mostrar)} restantes</span>
        </button>
      ) : null}
    </div>
  );
}
