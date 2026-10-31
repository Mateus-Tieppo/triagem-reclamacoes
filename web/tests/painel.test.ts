import { expect, test } from "vitest";
import { calcularResumo } from "@/dados/resumo";
import type { MensagemTriada } from "@/dados/tipos";

const msgs = (revisoes: boolean[]) => revisoes.map((revisao) => ({ revisao }) as MensagemTriada);

test("horas poupadas usam a premissa", () => {
  const r = calcularResumo(msgs([false, false, true]), 30);
  expect(r.total).toBe(3);
  expect(r.semHumano).toBe(2);
  expect(r.pctSemHumano).toBeCloseTo(2 / 3);
  expect(r.horasPoupadas).toBeCloseTo(60 / 3600);
});

test("sem mensagens não vira NaN", () => {
  const r = calcularResumo([], 30);
  expect(r).toEqual({ total: 0, semHumano: 0, pctSemHumano: 0, horasPoupadas: 0 });
});

test("premissa inválida conta como zero segundos", () => {
  expect(calcularResumo(msgs([false]), Number.NaN).horasPoupadas).toBe(0);
  expect(calcularResumo(msgs([false]), -5).horasPoupadas).toBe(0);
});
