import { expect, test } from "@playwright/test";

import { API, auth, CLAVE_DEV, iniciarSesion, obtenerToken } from "./helpers";

const unique = `${Date.now()}`;

test.describe("Acceso", () => {
  test("inicia sesión desde el formulario, muestra el usuario y cierra la sesión @smoke", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible({ timeout: 30_000 });

    await page.getByLabel("Usuario").fill("admin");
    await page.getByLabel("Contraseña", { exact: true }).fill(CLAVE_DEV);
    await page.getByRole("button", { name: "Iniciar sesión" }).click();

    await expect(page.getByRole("heading", { name: /Bienvenido de nuevo/ })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("banner", { name: "Barra superior" }).getByText("Administrador de Sistemas")).toBeVisible();

    await page.getByRole("banner", { name: "Barra superior" }).getByRole("button", { name: "Cerrar sesión" }).click();
    await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();
    await page.goto("/usuarios");
    await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();
  });

  test("rechaza credenciales incorrectas sin revelar si el usuario existe", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Usuario").fill("nadie");
    await page.getByLabel("Contraseña", { exact: true }).fill("ClaveMala1");
    await page.getByRole("button", { name: "Iniciar sesión" }).click();
    await expect(page.getByRole("alert")).toHaveText("Usuario o contraseña incorrectos.");

    await page.getByLabel("Usuario").fill("admin");
    await page.getByRole("button", { name: "Iniciar sesión" }).click();
    await expect(page.getByRole("alert")).toHaveText("Usuario o contraseña incorrectos.");
  });

  test("bloquea la cuenta tras tres intentos y el administrador la desbloquea", async ({ page }) => {
    const usuario = `bloqueo${unique}`;
    const adminToken = await obtenerToken(page, "admin", CLAVE_DEV);
    const creado = await page.request.post(`${API}/api/v1/usuarios`, {
      headers: auth(adminToken),
      data: {
        usuario,
        nombre: "Persona Bloqueable",
        tipo_identificacion: "CC",
        identificacion: `9${unique.slice(-9)}`,
        correo: `${usuario}@example.test`,
        clave: "Clave.Segura1",
        rol: "asesor",
      },
    });
    expect(creado.status()).toBe(201);
    const id = ((await creado.json()) as { id: number }).id;

    await page.goto("/login");
    for (const intento of [1, 2, 3]) {
      await page.getByLabel("Usuario").fill(usuario);
      await page.getByLabel("Contraseña", { exact: true }).fill("ClaveMala1");
      await page.getByRole("button", { name: "Iniciar sesión" }).click();
      await expect(page.getByRole("alert")).toContainText(
        intento < 3 ? "Usuario o contraseña incorrectos." : "bloqueada temporalmente",
      );
    }
    // Con la clave correcta sigue bloqueada.
    await page.getByLabel("Contraseña", { exact: true }).fill("Clave.Segura1");
    await page.getByRole("button", { name: "Iniciar sesión" }).click();
    await expect(page.getByRole("alert")).toContainText("bloqueada temporalmente");

    await iniciarSesion(page, "admin");
    await page.goto("/usuarios");
    const aviso = page.getByRole("alert").filter({ hasText: `@${usuario}` });
    await expect(aviso).toContainText("acceso suspendido");
    await aviso.getByRole("button", { name: "Desbloquear" }).click();
    await expect(page.getByRole("status")).toContainText("quedó desbloqueada");

    const login = await page.request.post(`${API}/api/v1/auth/login`, {
      data: { usuario, clave: "Clave.Segura1" },
    });
    expect(login.status()).toBe(200);

    expect((await page.request.delete(`${API}/api/v1/usuarios/${id}`, { headers: auth(adminToken) })).status()).toBe(204);
  });

  test("el asesor entra, no ve Usuarios y la API le niega el módulo", async ({ page }) => {
    const token = await iniciarSesion(page, "asesor");
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /Bienvenido de nuevo/ })).toBeVisible({ timeout: 30_000 });
    const nav = page.getByRole("navigation", { name: "Principal" });
    await expect(nav.getByRole("link", { name: "Inicio" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Usuarios" })).toHaveCount(0);

    const respuesta = await page.request.get(`${API}/api/v1/usuarios`, { headers: auth(token) });
    expect(respuesta.status()).toBe(403);
    await page.goto("/usuarios");
    await expect(page.getByRole("alert")).toContainText("No tiene permisos");
  });
});
