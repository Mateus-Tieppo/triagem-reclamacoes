import type { ReactNode } from "react";
import estilos from "./CabecalhoSecao.module.css";

export function CabecalhoSecao({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div className={estilos.secao}>
      <h1 className={estilos.titulo}>{titulo}</h1>
      {children ? <p className={`${estilos.texto} apoio`}>{children}</p> : null}
    </div>
  );
}
