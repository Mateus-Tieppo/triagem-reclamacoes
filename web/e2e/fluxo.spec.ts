import { expect, test, type Page } from "@playwright/test";

const SCREENSHOTS = "../docs/screenshots";

async function semRolagemLateral(page: Page) {
  const [largura, janela] = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  expect(largura).toBeLessThanOrEqual(janela);
}

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => localStorage.clear());
});

test("fluxo principal: painel, fila, mover, triar", async ({ page }, info) => {
  const tela = info.project.name;

  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("7.453 reclamações triadas");
  await semRolagemLateral(page);
  await page.screenshot({ path: `${SCREENSHOTS}/${tela}-painel.png`, fullPage: true, animations: "disabled" });

  await page.getByRole("link", { name: /Produto errado/ }).first().click();
  await expect(page).toHaveURL(/\/filas\?fila=ERR/);
  await expect(page.getByRole("heading", { level: 2, name: /Produto errado/ })).toBeVisible();
  await semRolagemLateral(page);

  await page.getByLabel("Mover para").first().selectOption("outro");
  await expect(page.getByText("Movida para Outro.")).toBeVisible();
  await expect(page.getByText(/^1\.155 reclamações/)).toBeVisible();
  await page.getByRole("button", { name: "Desfazer" }).click();
  await expect(page.getByText(/^1\.156 reclamações/)).toBeVisible();
  await page.getByLabel("Mover para").first().selectOption("outro");
  await page.screenshot({ path: `${SCREENSHOTS}/${tela}-filas.png`, animations: "disabled" });

  await page.getByRole("link", { name: "Revisão" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Revisão" })).toBeVisible();
  await semRolagemLateral(page);
  await page.screenshot({ path: `${SCREENSHOTS}/${tela}-revisao.png`, animations: "disabled" });

  await page.getByRole("link", { name: "Triar as minhas" }).click();
  await page.getByLabel("Reclamações, uma por linha").fill(
    ["Comprei faz um mês e não chegou", "Pedi dois e só veio um", "Veio quebrado e não funciona"].join("\n"),
  );
  await page.getByRole("button", { name: "Triar 3 reclamações" }).click();
  await expect(page.getByRole("heading", { name: /^3 triadas/ })).toBeVisible();
  await expect(page.getByText(/Seus dados · 3/)).toBeVisible();
  await semRolagemLateral(page);
  await page.screenshot({ path: `${SCREENSHOTS}/${tela}-triar.png`, fullPage: true, animations: "disabled" });

  await page.getByRole("link", { name: "Sobre" }).click();
  await expect(page.getByRole("table")).toContainText("75,5%");
  await semRolagemLateral(page);
});
