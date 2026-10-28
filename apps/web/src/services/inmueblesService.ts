import type { ListParams } from "../hooks/usePagedList";
import type { Inmueble, InmuebleCreate, InmueblesPage } from "../types/inmueble";
import { apiRequest } from "./apiClient";

const BASE = "/api/v1/inmuebles";

export function listInmuebles(params: ListParams, signal?: AbortSignal): Promise<InmueblesPage> {
  const query = new URLSearchParams({
    ...params.filtros,
    limit: String(params.limit),
    offset: String(params.offset),
  });
  return apiRequest<InmueblesPage>(`${BASE}?${query.toString()}`, { signal });
}

export function getInmueble(id: number, signal?: AbortSignal): Promise<Inmueble> {
  return apiRequest<Inmueble>(`${BASE}/${id}`, { signal });
}

export function createInmueble(input: InmuebleCreate): Promise<Inmueble> {
  return apiRequest<Inmueble>(BASE, { method: "POST", body: input });
}

export function updateInmueble(id: number, input: InmuebleCreate): Promise<Inmueble> {
  return apiRequest<Inmueble>(`${BASE}/${id}`, { method: "PUT", body: input });
}

export function deleteInmueble(id: number): Promise<void> {
  return apiRequest<void>(`${BASE}/${id}`, { method: "DELETE" });
}
