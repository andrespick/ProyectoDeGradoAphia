import { expect, type Page, test } from "@playwright/test";

import { CLAVE_DEV, iniciarSesion } from "./helpers";

test.use({ viewport: { width: 375, height: 740 } });

async function sinDesplazamientoHorizontal(page: Page) {
  const { scrollWidth, clientWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(scrollWidth, "la página no debe desplazarse horizontalmente").toBeLessThanOrEqual(clientWidth);
}

test.describe("Diseño adaptable (375 px)", () => {
  test("el login es usable en el celular", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible({ timeout: 30_000 });
    await sinDesplazamientoHorizontal(page);

    await page.getByLabel("Usuario").fill("asesor");
    await page.getByLabel("Contraseña", { exact: true }).fill(CLAVE_DEV);
    await page.getByRole("button", { name: "Iniciar sesión" }).click();
    await expect(page.getByRole("heading", { name: /Bienvenido de nuevo/ })).toBeVisible();
    await sinDesplazamientoHorizontal(page);
  });

  test("el menú es un cajón, la tabla se desplaza en su contenedor y el formulario ocupa la pantalla", async ({
    page,
  }) => {
    await iniciarSesion(page, "asesor");
    await page.goto("/inmuebles");
    await expect(page.getByRole("heading", { name: /Portafolio de inmuebles/ })).toBeVisible({ timeout: 30_000 });
    await sinDesplazamientoHorizontal(page);

    await page.getByRole("button", { name: "Abrir menú" }).click();
    const cajon = page.getByRole("complementary", { name: "Menú de navegación" });
    await expect(cajon.getByRole("link", { name: "Contratos" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(cajon).toHaveCount(0);

    const tabla = page.getByRole("table");
    await expect(tabla).toBeVisible();
    const desplazable = await tabla.evaluate((t) => {
      const wrap = t.parentElement as HTMLElement;
      return wrap.scrollWidth > wrap.clientWidth && getComputedStyle(wrap).overflowX === "auto";
    });
    expect(desplazable, "la tabla se desplaza dentro de .table-wrap").toBe(true);
    await sinDesplazamientoHorizontal(page);

    await page.getByRole("link", { name: "Registrar inmueble" }).click();
    const dialog = page.getByRole("dialog", { name: "Registrar nuevo inmueble" });
    const ancho = await dialog.evaluate((d) => d.getBoundingClientRect().width);
    expect(ancho).toBeGreaterThanOrEqual(370);
    await dialog.getByLabel(/Dirección completa/).fill("Calle móvil 1");
    await expect(dialog.getByLabel(/Dirección completa/)).toHaveValue("Calle móvil 1");
    await sinDesplazamientoHorizontal(page);
  });
});
