import { expect, test } from "@playwright/test";

import { iniciarSesion } from "./helpers";

test.describe("Ayuda en línea", () => {
  test("es pública y el login enlaza a la sección de inicio de sesión", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("link", { name: "¿Olvidó su contraseña?" }).click();
    await expect(page).toHaveURL(/\/ayuda#inicio-de-sesion$/);
    await expect(page.getByRole("heading", { name: "Inicio de sesión y bloqueo" })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/3 intentos fallidos/)).toBeVisible();
  });

  test("desde Clientes llega a su sección y el menú tiene Ayuda", async ({ page }) => {
    await iniciarSesion(page, "asesor");
    await page.goto("/clientes");
    await page.getByRole("link", { name: "Ayuda sobre clientes" }).click();

    await expect(page).toHaveURL(/\/ayuda#clientes$/);
    const seccion = page.locator("#clientes");
    await expect(seccion.getByRole("heading", { name: "Clientes" })).toBeVisible({ timeout: 30_000 });
    await expect(seccion).toBeInViewport();
    await expect(page.getByRole("navigation", { name: "Principal" }).getByRole("link", { name: "Ayuda" })).toBeVisible();
  });
});
