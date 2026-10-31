"use client";

import { CabecalhoSecao } from "@/componentes/CabecalhoSecao";
import { CartaoNumero } from "@/componentes/CartaoNumero";
import { useFonteDeDados } from "@/dados/FonteDeDados";

const numero = new Intl.NumberFormat("pt-BR");

export default function Painel() {
  const { estado } = useFonteDeDados();
  const p = estado.painel;
  return (
    <>
      <CabecalhoSecao titulo="Reclamações organizadas. Decisões inteligentes.">
        A TriIA lê cada reclamação, diz para qual time ela vai e separa o que precisa de uma pessoa.
      </CabecalhoSecao>
      {estado.erro ? <p role="alert">{estado.erro}</p> : null}
      {p ? (
        <CartaoNumero
          valor={numero.format(p.total)}
          rotulo="reclamações triadas"
          nota={`${numero.format(p.sem_humano)} sem precisar de ninguém`}
        />
      ) : (
        <p className="apoio" aria-busy="true">
          Carregando as reclamações…
        </p>
      )}
    </>
  );
}
