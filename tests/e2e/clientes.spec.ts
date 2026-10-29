import { expect, test } from "@playwright/test";

import { iniciarSesion } from "./helpers";

// Datos ficticios únicos por ejecución (dominio reservado .test).
const unique = `${Date.now()}`;

test.describe("Clientes", () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, "administrativo");
  });

  test("la pantalla inicial muestra el estado del sistema y el runtime real", async ({ page }) => {
    await page.goto("/");

    const sidebar = page.getByRole("complementary", { name: "Barra lateral" });
    await expect(sidebar.getByText("APHIA")).toBeVisible({ timeout: 30_000 });
    await expect(sidebar.getByText("En línea")).toBeVisible({ timeout: 30_000 });
    await expect(sidebar.getByText("Cloudflare Workers · development")).toBeVisible();
    await expect(page.getByRole("region", { name: "Indicadores" })).toBeVisible();
  });

  test("registra, filtra, edita y elimina un cliente @smoke", async ({ page }) => {
    const nombre = `Cliente E2E ${unique}`;
    const identificacion = `7${unique.slice(-9)}`;
    page.on("dialog", (dialog) => dialog.accept());

    await page.goto("/clientes");
    await expect(page.getByRole("heading", { name: /Gestión de clientes/ })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("link", { name: "Registrar cliente" }).click();

    const dialog = page.getByRole("dialog", { name: "Registrar cliente" });
    await dialog.getByLabel(/Nombre completo/).fill(nombre);
    await dialog.getByLabel(/^Identificación/).fill(identificacion);
    await dialog.getByLabel(/Teléfono/).fill("3001234567");
    await dialog.getByLabel(/Correo electrónico/).fill(`e2e-${unique}@example.test`);
    await dialog.getByLabel(/Tipo de cliente/).selectOption("arrendatario");
    const created = page.waitForResponse(
      (r) => r.url().endsWith("/api/v1/clientes") && r.request().method() === "POST",
    );
    await dialog.getByRole("button", { name: "Guardar cliente" }).click();
    expect((await created).status()).toBe(201);

    await expect(page.getByRole("status")).toContainText("Cliente registrado correctamente.");
    const fila = page.getByRole("row").filter({ hasText: identificacion });
    await expect(fila).toBeVisible({ timeout: 2_000 }); // RNF: cambios visibles en menos de 2 s
    await expect(fila.getByText("Arrendatario", { exact: true })).toBeVisible();

    // Filtro por identificación y por tipo de cliente.
    await page.getByLabel("Buscar").fill(identificacion);
    await page.getByRole("button", { name: "Buscar" }).click();
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await page.getByRole("button", { name: "Propietarios" }).click();
    await expect(page.getByText(/No hay clientes que coincidan/)).toBeVisible();
    await page.getByRole("button", { name: "Todos" }).click();

    // Editar: agregar el papel de codeudor.
    await page.getByRole("link", { name: `Editar ${nombre}` }).click();
    const edicion = page.getByRole("dialog", { name: "Editar cliente" });
    await edicion.getByLabel("Codeudor", { exact: true }).check();
    await edicion.getByRole("button", { name: "Guardar cliente" }).click();
    await expect(page.getByRole("status")).toContainText("Cliente actualizado correctamente.");
    await expect(page.getByRole("row").filter({ hasText: identificacion }).getByText("Codeudor", { exact: true })).toBeVisible();

    // Detalle y eliminación.
    await page.getByRole("link", { name: `Ver ${nombre}` }).click();
    await expect(page.getByRole("heading", { name: nombre })).toBeVisible();
    await expect(page.getByText(`CC ${identificacion}`)).toBeVisible();
    await page.getByRole("button", { name: "Eliminar" }).click();
    await expect(page.getByRole("heading", { name: /Gestión de clientes/ })).toBeVisible();
    await page.getByLabel("Buscar").fill(identificacion);
    await page.getByRole("button", { name: "Buscar" }).click();
    await expect(page.getByText(/No hay clientes que coincidan/)).toBeVisible();
  });

  test("informa la identificación duplicada devuelta por la API", async ({ page }) => {
    await page.goto("/clientes/nuevo");
    const dialog = page.getByRole("dialog", { name: "Registrar cliente" });
    await dialog.getByLabel(/Nombre completo/).fill("Duplicado Ficticio");
    await dialog.getByLabel(/^Identificación/).fill("1000009101"); // seed: Laura Propietaria
    await dialog.getByLabel(/Tipo de cliente/).selectOption("arrendatario");
    await dialog.getByRole("button", { name: "Guardar cliente" }).click();

    await expect(dialog.getByRole("alert")).toContainText("Ya existe una persona registrada");
  });

  test("el asesor registra pero no puede eliminar", async ({ page }) => {
    await iniciarSesion(page, "asesor");
    await page.goto("/clientes");

    await expect(page.getByRole("link", { name: "Registrar cliente" })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("row").first()).toBeVisible();
    await expect(page.getByRole("button", { name: /^Eliminar/ })).toHaveCount(0);
  });
});
