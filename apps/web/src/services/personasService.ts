import type { ListParams } from "../hooks/usePagedList";
import type { Persona, PersonaCreate, PersonaDetalle, PersonasPage } from "../types/persona";
import { apiRequest } from "./apiClient";

/** `api` es el prefijo del módulo: /api/v1/clientes, /api/v1/propietarios o /api/v1/codeudores. */
export function listPersonas(api: string, params: ListParams, signal?: AbortSignal): Promise<PersonasPage> {
  const query = new URLSearchParams({
    ...params.filtros,
    limit: String(params.limit),
    offset: String(params.offset),
  });
  return apiRequest<PersonasPage>(`${api}?${query.toString()}`, { signal });
}

export function getPersona(api: string, id: number, signal?: AbortSignal): Promise<PersonaDetalle> {
  return apiRequest<PersonaDetalle>(`${api}/${id}`, { signal });
}

export function createPersona(api: string, input: PersonaCreate): Promise<Persona> {
  return apiRequest<Persona>(api, { method: "POST", body: input });
}

export function updatePersona(api: string, id: number, input: PersonaCreate): Promise<Persona> {
  return apiRequest<Persona>(`${api}/${id}`, { method: "PUT", body: input });
}

export function deletePersona(api: string, id: number): Promise<void> {
  return apiRequest<void>(`${api}/${id}`, { method: "DELETE" });
}

/** Búsqueda exacta por identificación (cualquier persona, tenga o no papeles). */
export function buscarPersona(tipo: string, numero: string, signal?: AbortSignal): Promise<Persona> {
  const query = new URLSearchParams({ tipo_identificacion: tipo, identificacion: numero });
  return apiRequest<Persona>(`/api/v1/personas/buscar?${query.toString()}`, { signal });
}
