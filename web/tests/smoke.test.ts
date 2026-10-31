import { expect, test } from "vitest";
import modelo from "../public/modelo.json";

test("o modelo exportado tem as 8 categorias", () => {
  expect(modelo.classes).toHaveLength(8);
});
