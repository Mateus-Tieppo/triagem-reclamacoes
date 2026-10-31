import type { Modelo } from "@/modelo/tipos";
import type { Painel } from "./tipos";

/** Busca o painel pré-calculado das reclamações que o modelo nunca viu. */
export async function carregarPainel(buscar: typeof fetch = fetch): Promise<Painel> {
  const resposta = await buscar("/painel.json");
  if (!resposta.ok) throw new Error(`Não foi possível carregar o painel (${resposta.status}).`);
  return (await resposta.json()) as Painel;
}

let modelo: Promise<Modelo> | null = null;

/** Busca o modelo uma vez só; só é preciso para triar reclamações novas. */
export function carregarModelo(buscar: typeof fetch = fetch): Promise<Modelo> {
  modelo ??= buscar("/modelo.json").then((r) => {
    if (!r.ok) throw new Error(`Não foi possível carregar o modelo (${r.status}).`);
    return r.json() as Promise<Modelo>;
  });
  modelo.catch(() => (modelo = null));
  return modelo;
}
