import { Suspense } from "react";
import { Filas } from "./Filas";

export default function Pagina() {
  return (
    <Suspense>
      <Filas />
    </Suspense>
  );
}
