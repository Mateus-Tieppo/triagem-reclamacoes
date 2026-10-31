import { afterEach, expect, test, vi } from "vitest";
import { aplicarCorrecoes, lerCorrecoes, salvarCorrecao } from "@/dados/correcoes";
import type { MensagemTriada } from "@/dados/tipos";

afterEach(() => vi.unstubAllGlobals());

test("correção vence a predição e tira da revisão", () => {
  const [m] = aplicarCorrecoes([{ id: "a", categoria: "outro", revisao: true } as MensagemTriada], { a: "sem_estoque" });
  expect(m.categoria).toBe("sem_estoque");
  expect(m.corrigida).toBe(true);
  expect(m.revisao).toBe(false);
});

test("sem correção a mensagem fica igual", () => {
  const original = { id: "b", categoria: "outro", revisao: true } as MensagemTriada;
  expect(aplicarCorrecoes([original], { a: "sem_estoque" })[0]).toBe(original);
});

test("correção com categoria desconhecida é ignorada", () => {
  const original = { id: "a", categoria: "outro" } as MensagemTriada;
  expect(aplicarCorrecoes([original], { a: "inventada" })[0].categoria).toBe("outro");
});

test("sem localStorage não quebra", () => {
  vi.stubGlobal("localStorage", {
    getItem() {
      throw new Error();
    },
    setItem() {
      throw new Error();
    },
  });
  expect(() => salvarCorrecao("a", "outro")).not.toThrow();
  expect(lerCorrecoes()).toEqual({ a: "outro" });
});

test("localStorage com lixo não quebra", () => {
  vi.stubGlobal("localStorage", { getItem: () => "{nao e json", setItem() {} });
  expect(() => lerCorrecoes()).not.toThrow();
});
