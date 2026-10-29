import { expect, type Page, test } from "@playwright/test";

import { iniciarSesion } from "./helpers";

const unique = `${Date.now()}`;

function fecha(diasDesdeHoy: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + diasDesdeHoy);
  return d.toISOString().slice(0, 10);
}

async function elegirPersona(page: Page, grupo: string, identificacion: string) {
  const picker = page.getByRole("group", { name: grupo });
  await picker.getByLabel("Identificación").fill(identificacion);
  await picker.getByRole("button", { name: /^Buscar/ }).click();
  await picker.getByRole("button", { name: "Seleccionar" }).click();
}

test.describe("Contratos", () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, "administrativo");
  });

  test("registra un contrato con arrendatario existente y codeudor nuevo, lo imprime, filtra, edita y elimina", async ({
    page,
  }) => {
    const codeudorId = `8${unique.slice(-9)}`;
    page.on("dialog", (dialog) => dialog.accept());

    await page.goto("/contratos");
    await expect(page.getByRole("heading", { name: /Contratos y codeudores/ })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("link", { name: "Nuevo contrato" }).click();
    await expect(page.getByRole("heading", { name: "Nuevo contrato" })).toBeVisible();

    // Inmueble del seed por matrícula: sus propietarios se precargan.
    const inmueble = page.getByRole("group", { name: "Inmueble" });
    await inmueble.getByLabel(/Dirección o matrícula/).fill("50C-184920");
    await inmueble.getByRole("button", { name: "Buscar inmueble" }).click();
    await page.getByRole("button", { name: "Seleccionar" }).click();
    await expect(page.getByRole("list", { name: "Propietarios" }).getByText("Laura Propietaria Ficticia")).toBeVisible();

    await page.getByLabel(/Fecha de inicio/).fill(fecha(0));
    await page.getByLabel(/Fecha de fin/).fill(fecha(30));
    await page.getByLabel(/Canon pactado/).fill("1.800.000");
    await elegirPersona(page, "Arrendatario", "1000009102"); // seed: Carlos Arrendatario

    // Codeudor inexistente → se registra desde el selector.
    const codeudores = page.getByRole("group", { name: "Codeudores" });
    await codeudores.getByLabel("Identificación").fill(codeudorId);
    await codeudores.getByRole("button", { name: /^Buscar/ }).click();
    await codeudores.getByRole("button", { name: "Registrar nueva persona" }).click();
    await codeudores.getByLabel(/Nombre completo/).fill(`Fiador E2E ${unique}`);
    await codeudores.getByLabel(/Teléfono/).fill("3160001122");
    await codeudores.getByLabel(/Correo electrónico/).fill(`fiador-${unique}@example.test`);
    await codeudores.getByRole("button", { name: "Registrar como codeudor" }).click();
    await expect(page.getByRole("list", { name: "Codeudores" }).getByText(`Fiador E2E ${unique}`)).toBeVisible();

    await page.getByLabel(/Texto completo/).fill(`CONTRATO E2E ${unique}\nCláusula primera.`);
    await page.getByRole("button", { name: "Guardar contrato" }).click();

    // Detalle con recordatorio de ocupación, partes e impresión (window.print sustituido por una bandera).
    await expect(page.getByRole("status").filter({ hasText: /Recuerde/ })).toBeVisible({ timeout: 2_000 });
    await expect(page.getByRole("heading", { level: 1, name: /Contrato #\d+ · Arrendamiento/ })).toBeVisible();
    const contratoId = Number(new URL(page.url()).pathname.split("/").pop());
    await expect(page.getByText("Por vencer", { exact: true })).toBeVisible();
    await expect(page.getByText("30 días restantes")).toBeVisible();
    await expect(page.getByRole("link", { name: /Carlos Arrendatario Ficticio/ })).toBeVisible();
    await page.evaluate(() => {
      (window as Window & { impreso?: boolean }).impreso = false;
      window.print = () => {
        (window as Window & { impreso?: boolean }).impreso = true;
      };
    });
    await page.getByRole("button", { name: /Imprimir/ }).click();
    expect(await page.evaluate(() => (window as Window & { impreso?: boolean }).impreso)).toBe(true);

    // El codeudor quedó vinculado al contrato y con su papel.
    await page.goto(`/codeudores?contrato_id=${contratoId}`);
    await expect(page.getByRole("row").filter({ hasText: codeudorId })).toBeVisible({ timeout: 30_000 });
    await expect(page.locator("tbody tr")).toHaveCount(1);

    // Filtro por inmueble desde Inmuebles y por fechas.
    await page.goto("/inmuebles?q=50C-184920");
    await page.getByRole("link", { name: /Ver contratos de/ }).click();
    await expect(page).toHaveURL(/contratos\?inmueble_id=9201/);
    const fila = page.getByRole("row").filter({ hasText: `#${contratoId} · Arrendamiento` });
    await expect(fila).toBeVisible({ timeout: 30_000 });
    await expect(fila.getByText(/1\.800\.000/)).toBeVisible();
    await page.getByLabel("Vigente desde").fill(fecha(60));
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    await expect(page.getByText(/No hay contratos que coincidan/)).toBeVisible();

    // Editar la fecha de fin (indefinido) y eliminar.
    await page.goto(`/contratos/${contratoId}/editar`);
    await expect(page.getByLabel(/Texto completo/)).toHaveValue(new RegExp(`CONTRATO E2E ${unique}`), { timeout: 30_000 });
    await page.getByLabel(/Fecha de fin/).fill("");
    await page.getByRole("button", { name: "Guardar contrato" }).click();
    await expect(page.getByRole("status").filter({ hasText: /Contrato guardado/ })).toBeVisible();
    await expect(page.getByText("Vigente", { exact: true })).toBeVisible();
    await expect(page.getByText(/– indefinido/).first()).toBeVisible();
    await page.getByRole("button", { name: "Eliminar" }).click();
    await expect(page.getByRole("heading", { name: /Contratos y codeudores/ })).toBeVisible();
    await expect(page.getByRole("status").filter({ hasText: /Contrato eliminado/ })).toBeVisible();
  });

  test("el asesor crea pero no ve «Eliminar»; la búsqueda global encuentra el contrato del seed", async ({ page }) => {
    await iniciarSesion(page, "asesor");
    await page.goto("/contratos/9301");

    await expect(page.getByRole("heading", { level: 1, name: /Contrato #9301/ })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("link", { name: "Editar" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Eliminar" })).toHaveCount(0);

    await page.getByRole("searchbox", { name: "Búsqueda global" }).fill("Carrera 43A");
    const resultados = page.getByRole("region", { name: "Resultados de búsqueda" });
    await expect(resultados.getByRole("link", { name: /Contrato #9301/ })).toBeVisible();
    await resultados.getByRole("link", { name: /^Carrera 43A/ }).click();
    await expect(page.getByRole("dialog", { name: "Editar inmueble" })).toBeVisible();
  });
});
