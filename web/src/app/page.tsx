"use client";

import { Manchete } from "@/componentes/painel/Manchete";
import { PorFila } from "@/componentes/painel/PorFila";
import { PorMes } from "@/componentes/painel/PorMes";
import { Problemas } from "@/componentes/painel/Problemas";
import { useFonteDeDados } from "@/dados/FonteDeDados";

export default function Painel() {
  const { estado } = useFonteDeDados();
  const p = estado.painel;

  if (estado.erro) return <p role="alert">{estado.erro} Recarregue a página para tentar de novo.</p>;
  if (!p)
    return (
      <p className="apoio" aria-busy="true">
        Carregando as reclamações…
      </p>
    );

  const origem =
    estado.fonte === "usuario"
      ? "Reclamações que você enviou, triadas aqui no seu navegador."
      : "Reclamações reais da base pública da Olist que o modelo nunca viu no treino.";

  return (
    <>
      <Manchete mensagens={p.mensagens} origem={origem} />
      <PorFila mensagens={p.mensagens} />
      <PorMes porMes={p.por_mes} />
      <Problemas painel={p} />
    </>
  );
}
