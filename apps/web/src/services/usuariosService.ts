import type { ListParams } from "../hooks/usePagedList";
import type { Usuario, UsuarioCreate, UsuariosPage, UsuarioUpdate } from "../types/usuario";
import { apiRequest } from "./apiClient";

const BASE = "/api/v1/usuarios";

export function listUsuarios(params: ListParams, signal?: AbortSignal): Promise<UsuariosPage> {
  const query = new URLSearchParams({
    ...params.filtros,
    limit: String(params.limit),
    offset: String(params.offset),
  });
  return apiRequest<UsuariosPage>(`${BASE}?${query.toString()}`, { signal });
}

export function getUsuario(id: number, signal?: AbortSignal): Promise<Usuario> {
  return apiRequest<Usuario>(`${BASE}/${id}`, { signal });
}

export function createUsuario(input: UsuarioCreate): Promise<Usuario> {
  return apiRequest<Usuario>(BASE, { method: "POST", body: input });
}

export function updateUsuario(id: number, input: UsuarioUpdate): Promise<Usuario> {
  return apiRequest<Usuario>(`${BASE}/${id}`, { method: "PUT", body: input });
}

export function deleteUsuario(id: number): Promise<void> {
  return apiRequest<void>(`${BASE}/${id}`, { method: "DELETE" });
}

export function desbloquearUsuario(id: number): Promise<Usuario> {
  return apiRequest<Usuario>(`${BASE}/${id}/desbloquear`, { method: "POST" });
}

/** Clave temporal (se muestra una sola vez); obliga a cambiarla y cierra sus sesiones. */
export function restablecerClave(id: number): Promise<{ clave_temporal: string }> {
  return apiRequest<{ clave_temporal: string }>(`${BASE}/${id}/restablecer-clave`, { method: "POST" });
}

export function cerrarSesiones(id: number): Promise<void> {
  return apiRequest<void>(`${BASE}/${id}/cerrar-sesiones`, { method: "POST" });
}
