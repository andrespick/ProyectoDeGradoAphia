import { expect, test } from "@playwright/test";

import { API, auth, CLAVE_DEV, iniciarSesion, obtenerToken } from "./helpers";

const unique = `${Date.now()}`;

test.describe("Administración del sistema", () => {
  test("el panel muestra la base de datos y permite solicitar un respaldo", async ({ page }) => {
    await iniciarSesion(page, "admin");
    await page.goto("/sistema");

    const kpis = page.getByRole("region", { name: "Indicadores del sistema" });
    await expect(kpis.getByText("En línea")).toBeVisible({ timeout: 30_000 });
    await expect(kpis.getByText(/Última: 0018/)).toBeVisible();

    // En desarrollo no corre el cron de respaldos: una solicitud anterior puede seguir pendiente.
    const boton = page.getByRole("button", { name: /Solicitar respaldo ahora/ });
    if (await boton.isEnabled()) {
      await boton.click();
      await expect(page.getByRole("status")).toContainText("Respaldo solicitado");
    }
    await expect(page.getByText(/Respaldo solicitado desde/)).toBeVisible();
    await expect(boton).toBeDisabled();
  });

  test("lo que elimina el administrativo se restaura desde la papelera y queda auditado", async ({ page }) => {
    const identificacion = `7${unique.slice(-9)}`;
    const nombre = `Cliente Papelera ${unique}`;
    const administrativo = await obtenerToken(page, "administrativo", CLAVE_DEV);
    const creado = await page.request.post(`${API}/api/v1/clientes`, {
      headers: auth(administrativo),
      data: { nombre, tipo_identificacion: "CC", identificacion, papeles: ["arrendatario"] },
    });
    expect(creado.status()).toBe(201);
    const id = ((await creado.json()) as { id: number }).id;
    expect((await page.request.delete(`${API}/api/v1/clientes/${id}`, { headers: auth(administrativo) })).status()).toBe(204);

    await iniciarSesion(page, "admin");
    await page.goto("/papelera?tipo=persona");
    await page.getByRole("button", { name: `Restaurar ${nombre} (CC ${identificacion})` }).click({ timeout: 30_000 });
    await expect(page.getByRole("status")).toContainText("se restauró como persona #");

    const busqueda = await page.request.get(`${API}/api/v1/clientes?q=${identificacion}`, { headers: auth(administrativo) });
    expect(((await busqueda.json()) as { total: number }).total).toBe(1);

    await page.goto("/auditoria?accion=restaurar&entidad=persona");
    await expect(page.getByRole("table").getByText(`desde la papelera (antes #${id})`)).toBeVisible();
  });

  test("la clave temporal obliga a cambiarla al entrar", async ({ page }) => {
    const usuario = `temporal${unique}`;
    const admin = await obtenerToken(page, "admin", CLAVE_DEV);
    const creado = await page.request.post(`${API}/api/v1/usuarios`, {
      headers: auth(admin),
      data: {
        usuario,
        nombre: "Persona Clave Temporal",
        tipo_identificacion: "CC",
        identificacion: `6${unique.slice(-9)}`,
        correo: `${usuario}@example.test`,
        clave: "Clave.Segura1",
        rol: "asesor",
      },
    });
    expect(creado.status()).toBe(201);
    const id = ((await creado.json()) as { id: number }).id;

    await iniciarSesion(page, "admin");
    page.on("dialog", (dialog) => dialog.accept());
    await page.goto(`/usuarios?q=${usuario}`);
    await page.getByRole("button", { name: `Restablecer la clave de ${usuario}` }).click({ timeout: 30_000 });
    const temporal = (await page.locator("code.clave-temporal").textContent()) ?? "";
    expect(temporal).toMatch(/^[A-Za-z0-9]{12,}$/);

    // Pestaña nueva: sessionStorage vacío (la sesión del administrador vive en la otra pestaña).
    const nueva = await page.context().newPage();
    await nueva.goto("/login");
    await nueva.getByLabel("Usuario").fill(usuario);
    await nueva.getByLabel("Contraseña", { exact: true }).fill(temporal);
    await nueva.getByRole("button", { name: "Iniciar sesión" }).click();

    await expect(nueva).toHaveURL(/\/cambiar-clave$/, { timeout: 30_000 });
    await nueva.getByLabel(/Contraseña temporal/).fill(temporal);
    await nueva.getByLabel(/^Contraseña nueva/).fill("Nueva.Clave22");
    await nueva.getByLabel(/Repita/).fill("Nueva.Clave22");
    await nueva.getByRole("button", { name: "Cambiar contraseña" }).click();
    await expect(nueva.getByRole("heading", { name: /Bienvenido de nuevo/ })).toBeVisible({ timeout: 30_000 });

    expect((await page.request.delete(`${API}/api/v1/usuarios/${id}`, { headers: auth(admin) })).status()).toBe(204);
  });

  test("agrega, renombra y elimina una ciudad del catálogo", async ({ page }) => {
    const ciudad = `Ciudad E2E ${unique}`;
    page.on("dialog", (dialog) => dialog.accept(dialog.type() === "prompt" ? `${ciudad} renombrada` : undefined));
    await iniciarSesion(page, "admin");
    await page.goto("/catalogos?catalogo=ciudades");

    await page.getByLabel(/^Nombre/).fill(ciudad, { timeout: 30_000 });
    await page.getByRole("button", { name: /Agregar/ }).click();
    await expect(page.getByRole("status")).toContainText(`«${ciudad}» agregado.`);

    await page.getByRole("button", { name: `Renombrar ${ciudad}` }).click();
    await expect(page.getByRole("cell", { name: `${ciudad} renombrada`, exact: true })).toBeVisible();

    await page.getByRole("button", { name: `Eliminar ${ciudad} renombrada` }).click();
    await expect(page.getByRole("status")).toContainText("eliminado");
    await expect(page.getByRole("cell", { name: `${ciudad} renombrada`, exact: true })).toHaveCount(0);
  });

  test("los datos de la empresa aparecen en el pie de página", async ({ page }) => {
    const admin = await obtenerToken(page, "admin", CLAVE_DEV);
    const original = await (await page.request.get(`${API}/api/v1/configuracion/empresa`, { headers: auth(admin) })).json();
    await iniciarSesion(page, "admin");
    await page.goto("/configuracion");

    await page.getByLabel(/Razón social/).fill(`Inmobiliaria E2E ${unique}`, { timeout: 30_000 });
    await page.getByLabel("NIT").fill("900.123.456-7");
    await page.getByRole("button", { name: "Guardar datos" }).click();
    await expect(page.getByText("Datos de la empresa guardados.")).toBeVisible();
    await page.reload();
    await expect(page.getByRole("contentinfo")).toContainText(`Inmobiliaria E2E ${unique}`);

    await page.request.put(`${API}/api/v1/configuracion/empresa`, { headers: auth(admin), data: original });
  });
});
