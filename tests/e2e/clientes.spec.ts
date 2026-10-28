import { expect, test } from "@playwright/test";

import { iniciarSesion } from "./helpers";

// Datos ficticios únicos por ejecución (dominio reservado .test).
const unique = `${Date.now()}`;

test.describe("APHIA de extremo a extremo", () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, "admin");
  });

  test("la pantalla inicial muestra el estado del sistema y el runtime real", async ({ page }) => {
    await page.goto("/");

    const sidebar = page.getByRole("complementary", { name: "Barra lateral" });
    await expect(sidebar.getByText("APHIA")).toBeVisible({ timeout: 30_000 });
    await expect(sidebar.getByText("En línea")).toBeVisible({ timeout: 30_000 });
    await expect(sidebar.getByText("Cloudflare Workers · development")).toBeVisible();
    await expect(page.getByRole("region", { name: "Indicadores" })).toBeVisible();
  });

  test("registra un cliente ficticio y lo muestra en la lista", async ({ page }) => {
    const nombre = `Cliente E2E ${unique}`;
    const correo = `e2e-${unique}@example.test`;

    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Bienvenido de nuevo/ })).toBeVisible({ timeout: 30_000 });

    await page.getByLabel("Nombre").fill(nombre);
    await page.getByLabel("Correo electrónico").fill(correo);
    const created = page.waitForResponse(
      (response) => response.url().endsWith("/api/v1/clientes") && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Registrar cliente" }).click();

    expect((await created).status()).toBe(201);
    await expect(page.getByRole("status").filter({ hasText: "Cliente registrado" })).toBeVisible();
    const row = page.getByRole("row").filter({ hasText: correo });
    await expect(row).toContainText(nombre);

    // Persistencia: tras recargar, el registro proviene de MySQL.
    await page.reload();
    await expect(page.getByRole("row").filter({ hasText: correo })).toBeVisible({ timeout: 30_000 });
  });

  test("informa el correo duplicado devuelto por la API", async ({ page }) => {
    const correo = `duplicado-${unique}@example.test`;
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Bienvenido de nuevo/ })).toBeVisible({ timeout: 30_000 });

    for (const attempt of [1, 2]) {
      await page.getByLabel("Nombre").fill(`Cliente Duplicado ${attempt}`);
      await page.getByLabel("Correo electrónico").fill(correo);
      await page.getByRole("button", { name: "Registrar cliente" }).click();
      if (attempt === 1) await expect(page.getByText("Cliente registrado correctamente.")).toBeVisible();
    }

    await expect(page.getByRole("alert")).toContainText("Ya existe un cliente registrado");
  });

  test("valida el formulario en el navegador", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Bienvenido de nuevo/ })).toBeVisible({ timeout: 30_000 });

    await page.getByLabel("Correo electrónico").fill("no-es-un-correo");
    await page.getByRole("button", { name: "Registrar cliente" }).click();

    await expect(page.getByText("Ingrese un correo electrónico válido.")).toBeVisible();
  });
});
