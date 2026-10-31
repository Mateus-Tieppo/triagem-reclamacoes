"use client";

import { useMemo } from "react";
import { CabecalhoSecao } from "@/componentes/CabecalhoSecao";
import { ListaMensagens } from "@/componentes/filas/ListaMensagens";
import { useMensagens } from "@/dados/useMensagens";

export default function Revisao() {
  const { mensagens, erro, mover } = useMensagens();
  const pendentes = useMemo(() => (mensagens ?? []).filter((m) => m.revisao), [mensagens]);

  return (
    <>
      <CabecalhoSecao titulo="Revisão">
        Quando a certeza fica abaixo de 80% ou a mensagem não tem texto, o modelo não decide sozinho. Escolha a fila
        certa e a reclamação sai daqui.
      </CabecalhoSecao>
      {erro ? <p role="alert">{erro}</p> : null}
      {mensagens ? (
        <ListaMensagens
          mensagens={pendentes}
          onMover={mover}
          arquivo="triia-revisao.csv"
          vazio="Nada para revisar. Todas as reclamações já têm fila."
        />
      ) : (
        <p className="apoio" aria-busy="true">
          Carregando as reclamações…
        </p>
      )}
    </>
  );
}
