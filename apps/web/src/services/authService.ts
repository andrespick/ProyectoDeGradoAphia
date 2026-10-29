import type { LoginResponse, Principal } from "../types/auth";
import { apiRequest } from "./apiClient";

/** Identidad de la sesión actual (según el token enviado por apiClient). */
export function getCurrentPrincipal(signal?: AbortSignal): Promise<Principal> {
  return apiRequest<Principal>("/api/v1/auth/me", { signal, timeoutMs: 5_000 });
}

export function login(usuario: string, clave: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: { usuario, clave },
    timeoutMs: 15_000, // el hash de la contraseña tarda más que una consulta normal
  });
}

/** Cambia la clave propia; la API cierra las demás sesiones y entrega un token nuevo. */
export function cambiarClave(clave_actual: string, clave_nueva: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/v1/auth/cambiar-clave", {
    method: "POST",
    body: { clave_actual, clave_nueva },
    timeoutMs: 15_000,
  });
}
