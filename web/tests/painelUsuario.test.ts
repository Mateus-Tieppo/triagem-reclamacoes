import { expect, test } from "vitest";
import { montarPainel } from "@/dados/painelUsuario";
import type { Painel } from "@/dados/tipos";
import type { Predicao } from "@/modelo/tipos";

const pred = (categoria: string, revisao: boolean) =>
  ({ categoria, certeza: revisao ? 0.5 : 0.9, revisao, motivo: revisao ? "certeza baixa" : "", palavras: ["x"], probas: {} }) as Predicao;

const referencia = {
  regras_top: { nao_recebido_atraso: [{ nome: "nao_chegou", rotulo_legivel: "Não chegou", n: 9 }] },
} as unknown as Painel;
const regras = [{ nome: "nao_chegou", padrao: "nao chegou" }];

test("monta o painel com as predições do navegador", () => {
  const p = montarPainel(
    ["Não chegou ainda", "não chegou", "veio quebrado"],
    [pred("nao_recebido_atraso", false), pred("nao_recebido_atraso", true), pred("defeito_qualidade", false)],
    regras,
    referencia,
  );
  expect(p.total).toBe(3);
  expect(p.sem_humano).toBe(2);
  expect(p.por_categoria.nao_recebido_atraso).toBe(2);
  expect(p.por_categoria.sem_estoque).toBe(0);
  expect(p.por_mes).toEqual([]);
  expect(p.regras_top.nao_recebido_atraso).toEqual([{ nome: "nao_chegou", rotulo_legivel: "Não chegou", n: 2 }]);
  expect(new Set(p.mensagens.map((m) => m.id)).size).toBe(3);
  expect(p.mensagens[0]).toMatchObject({ texto: "Não chegou ainda", categoria: "nao_recebido_atraso", data: null });
});

test("mesmo texto em envios diferentes mantém o id, para a correção valer", () => {
  const a = montarPainel(["oi"], [pred("outro", true)], [], referencia).mensagens[0].id;
  const b = montarPainel(["oi"], [pred("outro", true)], [], referencia).mensagens[0].id;
  expect(a).toBe(b);
});
