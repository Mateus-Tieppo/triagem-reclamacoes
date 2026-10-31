import { expect, test } from "vitest";
import modeloJson from "../public/modelo.json";
import paridade from "./fixtures/paridade.json";
import { normalizar } from "@/modelo/normalizar";
import { prever, preverEmLotes } from "@/modelo/prever";
import type { Modelo } from "@/modelo/tipos";

const modelo = modeloJson as unknown as Modelo;

test("normaliza como o Python", () => {
  expect(normalizar("NÃO Chegou")).toBe("nao chegou");
  expect(normalizar("péssimooooo")).toBe("pessimo");
  expect(normalizar("veja http://x.com/a e mail@x.com")).toBe("veja _link_ e _link_");
  expect(normalizar("pedido 12345 de 20/12/2017 R$ 59,90")).toBe("pedido _num_ de _num_ r$ _num_");
  expect(normalizar("linha1\n\nlinha2")).toBe("linha1 linha2");
  expect(normalizar("😡😡😡")).toBe("😡");
});

test("texto sem letras vai para revisão", () => {
  for (const t of ["", "😡😡😡", "123456789012345"]) {
    const p = prever(modelo, t);
    expect(p.revisao).toBe(true);
    expect(p.motivo).toBe("texto sem conteúdo");
  }
});

test("explica com as palavras que mais pesaram", () => {
  const p = prever(modelo, "o produto chegou quebrado e com defeito");
  expect(p.categoria).toBe("defeito_qualidade");
  expect(p.palavras.length).toBeGreaterThan(0);
});

test("1.000 mensagens em menos de 2 s, com progresso", async () => {
  const textos = paridade.slice(0, 1000).map((r) => r.texto);
  const progresso: number[] = [];
  const t0 = performance.now();
  const r = await preverEmLotes(modelo, textos, (n) => progresso.push(n));
  expect(performance.now() - t0).toBeLessThan(2000);
  expect(r).toHaveLength(1000);
  expect(progresso.at(-1)).toBe(1000);
});

test("palavras com nome de propriedade do JavaScript não quebram a predição", () => {
  const p = prever(modelo, "constructor toString __proto__ hasOwnProperty valueOf não chegou");
  expect(Object.values(p.probas).every(Number.isFinite)).toBe(true);
  expect(p.categoria).toBe(prever(modelo, "não chegou").categoria);
});
