"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";
import { CabecalhoSecao } from "@/componentes/CabecalhoSecao";
import { ListaMensagens } from "@/componentes/filas/ListaMensagens";
import { numero } from "@/dados/formato";
import { CATEGORIAS, FILAS, type Categoria } from "@/dados/tipos";
import { useMensagens } from "@/dados/useMensagens";
import estilos from "./filas.module.css";

const PELO_CODIGO = new Map(CATEGORIAS.map((c) => [FILAS[c].codigo, c]));

export function Filas() {
  const codigo = useSearchParams().get("fila") ?? "";
  const ativa: Categoria = PELO_CODIGO.get(codigo) ?? "nao_recebido_atraso";
  const { mensagens, erro, mover, desfazer } = useMensagens();

  const porFila = useMemo(() => {
    const mapa = new Map<Categoria, number>(CATEGORIAS.map((c) => [c, 0]));
    for (const m of mensagens ?? []) mapa.set(m.categoria, mapa.get(m.categoria)! + 1);
    return mapa;
  }, [mensagens]);
  const daFila = useMemo(() => (mensagens ?? []).filter((m) => m.categoria === ativa), [mensagens, ativa]);

  return (
    <>
      <CabecalhoSecao titulo="Filas">
        Uma fila por time, como num sistema de atendimento. Se o modelo errou, mova a reclamação para a fila certa.
      </CabecalhoSecao>
      <nav aria-label="Filas" className={estilos.filas}>
        {CATEGORIAS.map((c) => (
          <Link
            key={c}
            href={`/filas?fila=${FILAS[c].codigo}`}
            scroll={false}
            replace
            aria-current={c === ativa ? "page" : undefined}
            className={estilos.fila}
          >
            <span className="codigo">{FILAS[c].codigo}</span>
            <span className={estilos.nome}>{FILAS[c].nome}</span>
            <span className={`${estilos.n} codigo`}>{mensagens ? numero.format(porFila.get(c)!) : "…"}</span>
          </Link>
        ))}
      </nav>
      <h2 className={estilos.titulo}>
        {FILAS[ativa].nome} <span className="apoio">· time de {FILAS[ativa].time}</span>
      </h2>
      {erro ? <p role="alert">{erro}</p> : null}
      {mensagens ? (
        <ListaMensagens
          key={ativa}
          mensagens={daFila}
          onMover={mover}
          onDesfazer={desfazer}
          arquivo={`triia-${FILAS[ativa].codigo.toLowerCase()}.csv`}
          vazio="Nenhuma reclamação nesta fila."
        />
      ) : (
        <p className="apoio" aria-busy="true">
          Carregando as reclamações…
        </p>
      )}
    </>
  );
}
