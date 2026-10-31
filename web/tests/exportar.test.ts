import { expect, test } from "vitest";
import { paraCsv } from "@/dados/exportar";
import type { MensagemTriada } from "@/dados/tipos";

const m = (texto: string) =>
  ({ id: "a", texto, categoria: "outro", certeza: 0.5, revisao: true, motivo: "certeza baixa" }) as MensagemTriada;

test("csv tem o cabeçalho combinado", () => {
  expect(paraCsv([]).replace(/^﻿/, "").split("\r\n")[0]).toBe("id;texto;categoria;certeza;revisao;motivo");
});

test("csv escapa aspas e ponto e vírgula", () => {
  expect(paraCsv([m('disse "oi"; tchau')])).toContain('"disse ""oi""; tchau"');
});

test("csv mantém quebra de linha dentro de aspas", () => {
  expect(paraCsv([m("linha 1\nlinha 2")])).toContain('"linha 1\nlinha 2"');
});

test("csv neutraliza fórmulas de planilha", () => {
  expect(paraCsv([m("=HYPERLINK(1)")])).toContain("'=HYPERLINK(1)");
});

test("csv usa vírgula decimal para o Excel em português", () => {
  expect(paraCsv([m("ok")])).toContain(";0,50;sim;certeza baixa");
});
