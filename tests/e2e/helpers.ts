import type { Page } from "@playwright/test";

export const API = "http://127.0.0.1:8787";
/** Contraseña de los usuarios de desarrollo (database/seeds/0003_usuarios_desarrollo.sql). */
export const CLAVE_DEV = "Aphia.2026";

/** Inicia sesión por la API y deja el token en sessionStorage antes de cargar la página. */
export async function iniciarSesion(page: Page, usuario = "admin", clave = CLAVE_DEV): Promise<string> {
  const token = await obtenerToken(page, usuario, clave);
  await page.addInitScript((t) => sessionStorage.setItem("aphia.token", t), token);
  return token;
}

export async function obtenerToken(page: Page, usuario: string, clave: string): Promise<string> {
  const response = await page.request.post(`${API}/api/v1/auth/login`, { data: { usuario, clave } });
  if (!response.ok()) throw new Error(`El inicio de sesión de ${usuario} falló: ${response.status()}`);
  return ((await response.json()) as { token: string }).token;
}

export function auth(token: string) {
  return { Authorization: `Bearer ${token}` };
}
