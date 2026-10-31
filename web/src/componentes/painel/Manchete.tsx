"use client";

import { useId, useState } from "react";
import { calcularResumo } from "@/dados/resumo";
import { numero, pct } from "@/dados/formato";
import type { MensagemTriada } from "@/dados/tipos";
import estilos from "./Manchete.module.css";

export function Manchete({ mensagens, origem }: { mensagens: MensagemTriada[]; origem: string }) {
  const [segundos, setSegundos] = useState(30);
  const campo = useId();
  const r = calcularResumo(mensagens, segundos);
  const horas = r.horasPoupadas >= 10 ? Math.round(r.horasPoupadas) : Math.round(r.horasPoupadas * 10) / 10;

  return (
    <section aria-labelledby="manchete" className={estilos.manchete}>
      <h1 id="manchete" className={estilos.titulo}>
        {numero.format(r.total)} reclamações triadas.{" "}
        <span className={estilos.destaque}>
          {numero.format(r.semHumano)} sem precisar de ninguém.
        </span>
      </h1>
      <p className={estilos.origem}>
        {origem} O modelo decidiu sozinho em {pct.format(r.pctSemHumano)} delas; o resto foi para revisão humana.
      </p>
      <p className={estilos.premissa}>
        Isso poupa cerca de <strong>{numero.format(horas)} horas</strong> de leitura, se cada mensagem leva{" "}
        <label htmlFor={campo} className={estilos.oculto}>
          segundos por mensagem
        </label>
        <input
          id={campo}
          className={`${estilos.segundos} codigo`}
          type="number"
          inputMode="numeric"
          min={1}
          max={600}
          value={segundos}
          onChange={(e) => setSegundos(e.target.valueAsNumber)}
        />{" "}
        segundos para ler e encaminhar. <span className="apoio">É uma estimativa: troque o número se o seu time for mais rápido ou mais lento.</span>
      </p>
    </section>
  );
}
