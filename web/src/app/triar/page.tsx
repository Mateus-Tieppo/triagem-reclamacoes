import { CabecalhoSecao } from "@/componentes/CabecalhoSecao";
import { Triar } from "./Triar";

export default function Pagina() {
  return (
    <>
      <CabecalhoSecao titulo="Triar as minhas">
        Cole reclamações, uma por linha, ou suba um CSV. O modelo roda aqui no seu navegador: nada é enviado para
        lugar nenhum.
      </CabecalhoSecao>
      <Triar />
    </>
  );
}
