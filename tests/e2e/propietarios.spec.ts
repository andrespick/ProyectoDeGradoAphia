import { expect, test } from "@playwright/test";

import { iniciarSesion } from "./helpers";

const unique = `${Date.now()}`;

test.describe("Propietarios", () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, "admin");
  });

  test("registra un propietario con cuenta bancaria y lo encuentra por correo", async ({ page }) => {
    const identificacion = `6${unique.slice(-9)}`;
    const correo = `dueno-${unique}@example.test`;

    await page.goto("/propietarios");
    await expect(page.getByRole("heading", { name: /Gestión de propietarios/ })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("link", { name: "Registrar propietario" }).click();

    const dialog = page.getByRole("dialog", { name: "Registrar propietario" });
    await expect(dialog.getByLabel("Propietario", { exact: true })).toBeChecked();
    await dialog.getByLabel(/Nombre completo/).fill(`Propietario E2E ${unique}`);
    await dialog.getByLabel(/^Identificación/).fill(identificacion);
    await dialog.getByLabel(/Teléfono/).fill("3109876543");
    await dialog.getByLabel(/Correo electrónico/).fill(correo);
    await dialog.getByLabel(/Dirección/).fill("Calle 100 # 20-30");
    await dialog.getByLabel(/^Banco/).fill("Bancolombia");
    await dialog.getByLabel(/Tipo de cuenta/).selectOption("AHORROS");
    await dialog.getByLabel(/Número de cuenta/).fill("4455667788");
    await dialog.getByRole("button", { name: "Guardar propietario" }).click();

    await expect(page.getByRole("status")).toContainText("Propietario registrado correctamente.");
    const fila = page.getByRole("row").filter({ hasText: identificacion });
    await expect(fila).toBeVisible({ timeout: 2_000 });
    await expect(fila.getByText("•••• 7788", { exact: false })).toBeVisible();
    await expect(fila.getByText("Sin inmuebles")).toBeVisible();

    await page.getByLabel("Correo").fill(correo.toUpperCase());
    await page.getByRole("button", { name: "Buscar" }).click();
    await expect(page.getByRole("row").filter({ hasText: identificacion })).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(1);

    // Detalle: cuenta bancaria y papel.
    await page.getByRole("link", { name: `Ver Propietario E2E ${unique}` }).click();
    await expect(page.getByText("Bancolombia · AHORROS •••• 7788")).toBeVisible();
  });

  test("el propietario con inmuebles del seed aparece con su conteo y lista sus inmuebles", async ({ page }) => {
    await page.goto("/propietarios?q=1000009101");

    const fila = page.getByRole("row").filter({ hasText: "1000009101" });
    await expect(fila).toBeVisible({ timeout: 30_000 });
    await expect(fila.getByText("Laura Propietaria Ficticia")).toBeVisible();
    await expect(fila.getByText("Propietario", { exact: true })).toBeVisible();
  });
});
