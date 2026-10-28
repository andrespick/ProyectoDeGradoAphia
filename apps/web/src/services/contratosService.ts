import type { ListParams } from "../hooks/usePagedList";
import type { Contrato, ContratoCreate, ContratosPage, ResultadosBusqueda } from "../types/contrato";
import { apiRequest } from "./apiClient";

const BASE = "/api/v1/contratos";

export function listContratos(params: ListParams, signal?: AbortSignal): Promise<ContratosPage> {
  const query = new URLSearchParams({
    ...params.filtros,
    limit: String(params.limit),
    offset: String(params.offset),
  });
  return apiRequest<ContratosPage>(`${BASE}?${query.toString()}`, { signal });
}

export function getContrato(id: number, signal?: AbortSignal): Promise<Contrato> {
  return apiRequest<Contrato>(`${BASE}/${id}`, { signal });
}

export function createContrato(input: ContratoCreate): Promise<Contrato> {
  return apiRequest<Contrato>(BASE, { method: "POST", body: input });
}

export function updateContrato(id: number, input: ContratoCreate): Promise<Contrato> {
  return apiRequest<Contrato>(`${BASE}/${id}`, { method: "PUT", body: input });
}

export function deleteContrato(id: number): Promise<void> {
  return apiRequest<void>(`${BASE}/${id}`, { method: "DELETE" });
}

/** Búsqueda global de la barra superior (hasta 5 resultados por grupo). */
export function buscarGlobal(q: string, signal?: AbortSignal): Promise<ResultadosBusqueda> {
  return apiRequest<ResultadosBusqueda>(`/api/v1/buscar?q=${encodeURIComponent(q)}`, { signal });
}
