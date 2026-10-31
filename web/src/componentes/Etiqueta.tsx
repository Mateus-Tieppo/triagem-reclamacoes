import { FILAS, type Categoria } from "@/dados/tipos";
import estilos from "./Etiqueta.module.css";

/** O código impresso da fila, como numa etiqueta de despacho. */
export function Etiqueta({ categoria, certeza }: { categoria: Categoria; certeza?: number }) {
  const fila = FILAS[categoria];
  return (
    <span className={`${estilos.etiqueta} codigo`} title={fila.nome}>
      <span translate="no">{fila.codigo}</span>
      {certeza !== undefined ? <span className={estilos.certeza}>{Math.round(certeza * 100)}%</span> : null}
      <span className={estilos.oculto}>{fila.nome}</span>
    </span>
  );
}
