import { expect, test } from "vitest";
import { colunaDeTexto, lerCsv, linhasColadas } from "@/dados/csv";

test("csv do Excel brasileiro", () => {
  const r = lerCsv('﻿id;mensagem\n1;"não chegou;\nainda"\n2;veio quebrado');
  expect(r.colunas).toEqual(["id", "mensagem"]);
  expect(r.linhas[0].mensagem).toBe("não chegou;\nainda");
  expect(r.linhas[1].mensagem).toBe("veio quebrado");
  expect(colunaDeTexto(r.colunas)).toBe("mensagem");
});

test("csv com vírgula, CRLF, aspas escapadas e linhas vazias", () => {
  const r = lerCsv('texto,nota\r\n"disse ""oi"", tchau",5\r\n\r\nsó isso,3\r\n');
  expect(r.colunas).toEqual(["texto", "nota"]);
  expect(r.linhas).toEqual([
    { texto: 'disse "oi", tchau', nota: "5" },
    { texto: "só isso", nota: "3" },
  ]);
});

test("coluna desconhecida pede escolha", () => {
  expect(colunaDeTexto(["a", "b"])).toBeNull();
});

test("acha a coluna sem ligar para acento e maiúscula", () => {
  expect(colunaDeTexto(["ID", "Comentário"])).toBe("Comentário");
  expect(colunaDeTexto(["review_comment_message", "texto"])).toBe("texto");
});

test("cabeçalho vazio vira nome de coluna", () => {
  expect(lerCsv(";texto\n1;oi").colunas).toEqual(["coluna_1", "texto"]);
});

test("texto colado vira uma reclamação por linha", () => {
  expect(linhasColadas("  não chegou \n\n\nveio errado\r\n")).toEqual(["não chegou", "veio errado"]);
});
