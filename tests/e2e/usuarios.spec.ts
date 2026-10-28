import { expect, test } from "@playwright/test";

import { iniciarSesion } from "./helpers";

const unique = `${Date.now()}`;

test.describe("Usuarios y roles", () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, "admin");
  });

  test("registra, edita y elimina un usuario desde la pantalla", async ({ page }) => {
    const usuario = `e2e${unique}`;
    page.on("dialog", (dialog) => dialog.accept());

    await page.goto("/usuarios");
    await expect(page.getByRole("heading", { name: /Usuarios y roles/ })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("link", { name: "Registrar usuario" }).click();

    const dialog = page.getByRole("dialog", { name: "Registrar usuario" });
    await dialog.getByLabel(/Nombre de usuario/).fill(usuario);
    await dialog.getByLabel(/^Rol/).selectOption("asesor");
    await dialog.getByLabel(/^Clave/).fill("Clave.Segura1");
    await dialog.getByLabel(/Nombre completo/).fill(`Persona E2E ${unique}`);
    await dialog.getByLabel(/Tipo de identificación/).selectOption("CC");
    await dialog.getByLabel(/^Identificación/).fill(`8${unique.slice(-9)}`);
    await dialog.getByLabel(/Correo electrónico/).fill(`${usuario}@example.test`);
    const creado = page.waitForResponse(
      (r) => r.url().endsWith("/api/v1/usuarios") && r.request().method() === "POST",
    );
    await dialog.getByRole("button", { name: "Guardar usuario" }).click();
    expect((await creado).status()).toBe(201);

    await expect(page.getByRole("status")).toContainText("Usuario registrado correctamente.");
    const fila = page.getByRole("row").filter({ hasText: `@${usuario}` });
    await expect(fila).toBeVisible({ timeout: 2_000 }); // RNF: cambios visibles en menos de 2 s
    await expect(fila.getByText("Asesor", { exact: true })).toBeVisible();

    await fila.getByRole("link", { name: `Editar ${usuario}` }).click();
    const edicion = page.getByRole("dialog", { name: "Editar usuario" });
    await expect(edicion.getByLabel(/Nombre completo/)).toHaveValue(`Persona E2E ${unique}`);
    await edicion.getByLabel(/^Rol/).selectOption("administrativo");
    await edicion.getByRole("button", { name: "Guardar usuario" }).click();
    await expect(page.getByRole("status")).toContainText("Usuario actualizado correctamente.");
    await expect(page.getByRole("row").filter({ hasText: `@${usuario}` }).getByText("Administrativo")).toBeVisible();

    await page.getByRole("row").filter({ hasText: `@${usuario}` }).getByRole("button", { name: `Eliminar ${usuario}` }).click();
    await expect(page.getByRole("status")).toContainText("eliminado");
    await expect(page.getByRole("row").filter({ hasText: `@${usuario}` })).toHaveCount(0);
  });

  test("no permite eliminar la propia cuenta ni dejar el sistema sin administrador", async ({ page }) => {
    await page.goto("/usuarios?q=admin");
    const fila = page.getByRole("row").filter({ has: page.getByText("@admin", { exact: true }) });
    await expect(fila).toBeVisible({ timeout: 30_000 });
    await expect(fila.getByRole("button", { name: "Eliminar admin" })).toBeDisabled();
  });
});
