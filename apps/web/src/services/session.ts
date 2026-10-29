// Token de sesión en el navegador. sessionStorage por defecto (cada pestaña inicia sesión);
// localStorage cuando el usuario marca «Recordarme».
const KEY = "aphia.token";

/** Evento global que dispara apiClient cuando la API responde 401 con un token presente. */
export const SESSION_EXPIRED_EVENT = "aphia:sesion-expirada";

export function getToken(): string | null {
  try {
    return sessionStorage.getItem(KEY) ?? localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string, recordar = false): void {
  clearToken();
  try {
    (recordar ? localStorage : sessionStorage).setItem(KEY, token);
  } catch {
    // Almacenamiento no disponible (modo privado estricto): la sesión dura lo que la página.
  }
}

/** Sustituye el token conservando dónde estaba guardado (pestaña o «Recordarme»). */
export function replaceToken(token: string): void {
  let recordado = false;
  try {
    recordado = localStorage.getItem(KEY) !== null;
  } catch {
    // Sin almacenamiento: setToken tampoco podrá guardarlo.
  }
  setToken(token, recordado);
}

export function clearToken(): void {
  try {
    sessionStorage.removeItem(KEY);
    localStorage.removeItem(KEY);
  } catch {
    // Nada que limpiar.
  }
}
