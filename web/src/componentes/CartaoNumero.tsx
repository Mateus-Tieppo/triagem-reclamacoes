import type { ReactNode } from "react";
import estilos from "./CartaoNumero.module.css";

/** Um número com rótulo e, quando houver, a premissa que o sustenta. */
export function CartaoNumero({ valor, rotulo, nota }: { valor: ReactNode; rotulo: string; nota?: ReactNode }) {
  return (
    <div className={estilos.cartao}>
      <p className={estilos.valor}>{valor}</p>
      <p className={estilos.rotulo}>{rotulo}</p>
      {nota ? <p className={`${estilos.nota} codigo`}>{nota}</p> : null}
    </div>
  );
}
