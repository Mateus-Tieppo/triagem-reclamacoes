import { describe, expect, test } from "vitest";
import modeloJson from "../public/modelo.json";
import paridade from "./fixtures/paridade.json";
import { prever } from "@/modelo/prever";
import type { Modelo } from "@/modelo/tipos";

const modelo = modeloJson as unknown as Modelo;

describe("paridade com o Python", () => {
  test("mesma categoria e probabilidades em todas as referências", () => {
    const divergentes: string[] = [];
    for (const r of paridade) {
      const p = prever(modelo, r.texto);
      const probas = r.probas as Record<string, number>;
      const maiorDiferenca = Math.max(...modelo.classes.map((c) => Math.abs(p.probas[c] - probas[c])));
      if (p.categoria !== r.categoria || maiorDiferenca >= 1e-3) divergentes.push(r.texto);
    }
    expect(divergentes).toEqual([]);
  });

  test("marca texto sem conteúdo igual ao Python", () => {
    for (const r of paridade) expect(prever(modelo, r.texto).motivo === "texto sem conteúdo").toBe(r.sem_conteudo);
  });
});
