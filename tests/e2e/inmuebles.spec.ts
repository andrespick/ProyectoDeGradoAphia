import { expect, test } from "@playwright/test";

import { iniciarSesion } from "./helpers";

const unique = `${Date.now()}`;

test.describe("Inmuebles", () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, "admin");
  });

  test("registra un inmueble con propietario nuevo, lo filtra, lo edita y lo elimina", async ({ page }) => {
    const identificacion = `7${unique.slice(-9)}`;
    const direccion = `Calle E2E ${unique} # 1-2`;
    page.on("dialog", (dialog) => dialog.accept());

    await page.goto("/inmuebles");
    await expect(page.getByRole("heading", { name: /Portafolio de inmuebles/ })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("link", { name: "Registrar inmueble" }).click();

    const dialog = page.getByRole("dialog", { name: "Registrar nuevo inmueble" });
    await dialog.getByLabel(/Dirección completa/).fill(direccion);
    await dialog.getByLabel(/Ciudad/).fill("Bucaramanga");
    await dialog.getByLabel(/Matrícula/).fill(`E2E-${unique}`);
    await dialog.getByLabel(/Canon mensual/).fill("1.250.000");
    await dialog.getByLabel("Ocupado").check();

    // Propietario inexistente → se registra desde el selector (queda con papel propietario).
    const picker = dialog.getByRole("group", { name: "Propietario legal asociado" });
    await picker.getByLabel("Identificación").fill(identificacion);
    await picker.getByRole("button", { name: /Buscar/ }).click();
    await picker.getByRole("button", { name: "Registrar nueva persona" }).click();
    await picker.getByLabel(/Nombre completo/).fill(`Dueño E2E ${unique}`);
    await picker.getByLabel(/Teléfono/).fill("3151112233");
    await picker.getByLabel(/Correo electrónico/).fill(`dueno-inmueble-${unique}@example.test`);
    await picker.getByRole("button", { name: "Registrar como propietario" }).click();
    await expect(dialog.getByText(`Dueño E2E ${unique}`)).toBeVisible();

    await dialog.getByRole("button", { name: /Agregar servicio/ }).click();
    await dialog.getByLabel("Tipo de servicio").selectOption("ENERGIA");
    await dialog.getByLabel("Proveedor").fill("Enel Colombia");
    await dialog.getByLabel(/Número de contrato/).fill(`EN-${unique}`);
    await dialog.getByRole("button", { name: "Guardar inmueble" }).click();

    await expect(page.getByRole("status")).toContainText("Inmueble registrado correctamente.");
    const fila = page.getByRole("row").filter({ hasText: direccion });
    await expect(fila).toBeVisible({ timeout: 2_000 });
    await expect(fila.getByText(/1\.250\.000/)).toBeVisible();
    await expect(fila.getByText("Ocupado")).toBeVisible();
    await expect(fila.getByText(`ENERGIA · EN-${unique}`)).toBeVisible();

    // Filtros por estado y ciudad (sin distinguir mayúsculas ni acentos) con chips aplicados.
    await page.getByLabel("Estado").selectOption("OCUPADO");
    await page.getByLabel("Ciudad").fill("BUCARAMANGA");
    await page.getByRole("button", { name: "Buscar", exact: true }).click(); // el selector de propietario tiene «Buscar propietario»
    await expect(page).toHaveURL(/estado=OCUPADO/);
    await expect(page.getByRole("row").filter({ hasText: direccion })).toBeVisible();
    await expect(page.getByText("Estado: OCUPADO")).toBeVisible();
    await page.getByRole("button", { name: "Restablecer filtros" }).click();
    await expect(page).not.toHaveURL(/estado=/);

    // Editar el canon y verlo formateado.
    await page.getByRole("link", { name: `Editar ${direccion}` }).click();
    const edicion = page.getByRole("dialog", { name: "Editar inmueble" });
    await expect(edicion.getByLabel(/Dirección completa/)).toHaveValue(direccion);
    await edicion.getByLabel(/Canon mensual/).fill("1.300.000");
    await edicion.getByRole("button", { name: "Guardar inmueble" }).click();
    await expect(page.getByRole("status")).toContainText("Inmueble actualizado correctamente.");
    await expect(page.getByRole("row").filter({ hasText: direccion }).getByText(/1\.300\.000/)).toBeVisible({
      timeout: 2_000,
    });

    // El propietario inscrito desde el inmueble aparece en Propietarios con su inmueble.
    await page.goto(`/propietarios?q=${identificacion}`);
    const filaDueno = page.getByRole("row").filter({ hasText: identificacion });
    await expect(filaDueno).toBeVisible({ timeout: 30_000 });
    await expect(filaDueno.getByText("1 inmueble")).toBeVisible();

    // Eliminar el inmueble.
    await page.goto(`/inmuebles?q=E2E-${unique}`);
    await page.getByRole("button", { name: `Eliminar ${direccion}` }).click();
    await expect(page.getByRole("status")).toContainText("Inmueble eliminado correctamente.");
    await expect(page.getByText(/No hay inmuebles que coincidan/)).toBeVisible();
  });

  test("el asesor registra y edita pero no puede eliminar", async ({ page }) => {
    await iniciarSesion(page, "asesor");
    await page.goto("/inmuebles?q=50C-184920");

    await expect(page.getByRole("row").filter({ hasText: "50C-184920" })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("link", { name: "Registrar inmueble" })).toBeVisible();
    await expect(page.getByRole("link", { name: /^Editar/ })).toHaveCount(1);
    await expect(page.getByRole("button", { name: /^Eliminar/ })).toHaveCount(0);
  });
});
