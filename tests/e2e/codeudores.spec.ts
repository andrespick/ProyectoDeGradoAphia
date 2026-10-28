import { expect, test } from "@playwright/test";

import { iniciarSesion } from "./helpers";

const unique = `${Date.now()}`;

test.describe("Codeudores", () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, "administrativo");
  });

  test("registra un codeudor y lo encuentra por identificación", async ({ page }) => {
    const identificacion = `5${unique.slice(-9)}`;

    await page.goto("/codeudores/nuevo");
    const dialog = page.getByRole("dialog", { name: "Registrar codeudor" });
    await expect(dialog).toBeVisible({ timeout: 30_000 });
    await dialog.getByLabel(/Nombre completo/).fill(`Codeudor E2E ${unique}`);
    await dialog.getByLabel(/^Identificación/).fill(identificacion);
    await dialog.getByLabel(/Teléfono/).fill("3012223344");
    await dialog.getByRole("button", { name: "Guardar codeudor" }).click();

    await expect(page.getByRole("status")).toContainText("Codeudor registrado correctamente.");
    await page.getByLabel("Buscar").fill(identificacion);
    await page.getByRole("button", { name: "Buscar" }).click();
    const fila = page.getByRole("row").filter({ hasText: identificacion });
    await expect(fila).toBeVisible();
    await expect(fila.getByText("Codeudor", { exact: true })).toBeVisible();

    // Una persona del seed con dos papeles aparece también entre los codeudores.
    await page.goto("/codeudores?q=1000009103");
    const mario = page.getByRole("row").filter({ hasText: "1000009103" });
    await expect(mario).toBeVisible();
    await expect(mario.getByText("Propietario", { exact: true })).toBeVisible();
    await expect(mario.getByText("Codeudor", { exact: true })).toBeVisible();
  });
});
