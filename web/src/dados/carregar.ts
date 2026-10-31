import type { Painel } from "./tipos";

/** Busca o painel pré-calculado das reclamações que o modelo nunca viu. */
export async function carregarPainel(buscar: typeof fetch = fetch): Promise<Painel> {
  const resposta = await buscar("/painel.json");
  if (!resposta.ok) throw new Error(`Não foi possível carregar o painel (${resposta.status}).`);
  return (await resposta.json()) as Painel;
}
