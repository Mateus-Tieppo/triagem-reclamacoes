import { readFile } from "node:fs/promises";
import { expect, test } from "vitest";
import { carregarPainel } from "@/dados/carregar";

const buscarDoDisco = (async (url: string) =>
  new Response(await readFile(new URL(`../public${url}`, import.meta.url)))) as unknown as typeof fetch;

test("carrega o painel das reclamações nunca vistas", async () => {
  const p = await carregarPainel(buscarDoDisco);
  expect(p.total).toBe(7453);
  expect(p.mensagens).toHaveLength(7453);
  expect(p.sem_humano).toBe(p.mensagens.filter((m) => !m.revisao).length);
});

test("falha com mensagem clara quando o arquivo não vem", async () => {
  const falha = (async () => new Response("", { status: 404 })) as unknown as typeof fetch;
  await expect(carregarPainel(falha)).rejects.toThrow("painel");
});
