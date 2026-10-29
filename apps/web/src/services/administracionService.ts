import type { ListParams } from "../hooks/usePagedList";
import type {
  AuditoriaPage,
  CatalogoAdministrable,
  Empresa,
  EstadoSistema,
  ItemCatalogo,
  PapeleraPage,
  PoliticaPublica,
  PoliticaSeguridad,
  Respaldo,
  RespaldosPage,
  TipoRegistro,
} from "../types/administracion";
import { apiRequest } from "./apiClient";

function query(params: ListParams): string {
  return new URLSearchParams({
    ...params.filtros,
    limit: String(params.limit),
    offset: String(params.offset),
  }).toString();
}

// ── Estado del sistema y respaldos ──────────────────────────────────────────────────────────

export function getEstadoSistema(signal?: AbortSignal): Promise<EstadoSistema> {
  return apiRequest<EstadoSistema>("/api/v1/sistema/estado", { signal });
}

export function listRespaldos(signal?: AbortSignal): Promise<RespaldosPage> {
  return apiRequest<RespaldosPage>("/api/v1/sistema/respaldos?limit=10", { signal });
}

export function solicitarRespaldo(): Promise<Respaldo> {
  return apiRequest<Respaldo>("/api/v1/sistema/respaldos", { method: "POST" });
}

// ── Auditoría ───────────────────────────────────────────────────────────────────────────────

export function listAuditoria(params: ListParams, signal?: AbortSignal): Promise<AuditoriaPage> {
  return apiRequest<AuditoriaPage>(`/api/v1/auditoria?${query(params)}`, { signal });
}

// ── Configuración ───────────────────────────────────────────────────────────────────────────

/** Pública: la usan el inicio de sesión y el cambio de contraseña. */
export function getPoliticaPublica(signal?: AbortSignal): Promise<PoliticaPublica> {
  return apiRequest<PoliticaPublica>("/api/v1/auth/politica", { signal });
}

export function getPolitica(signal?: AbortSignal): Promise<PoliticaSeguridad> {
  return apiRequest<PoliticaSeguridad>("/api/v1/configuracion/seguridad", { signal });
}

export function updatePolitica(input: PoliticaSeguridad): Promise<PoliticaSeguridad> {
  return apiRequest<PoliticaSeguridad>("/api/v1/configuracion/seguridad", { method: "PUT", body: input });
}

let empresa: Promise<Empresa> | null = null;

/** Datos de la empresa (pie de página e impresión de contratos). Una petición por pestaña. */
export function getEmpresa(): Promise<Empresa> {
  empresa ??= apiRequest<Empresa>("/api/v1/configuracion/empresa").catch((error: unknown) => {
    empresa = null;
    throw error;
  });
  return empresa;
}

export async function updateEmpresa(input: Empresa): Promise<Empresa> {
  const guardada = await apiRequest<Empresa>("/api/v1/configuracion/empresa", { method: "PUT", body: input });
  empresa = Promise.resolve(guardada);
  return guardada;
}

// ── Catálogos administrables ────────────────────────────────────────────────────────────────

export function listItemsCatalogo(catalogo: CatalogoAdministrable, signal?: AbortSignal): Promise<ItemCatalogo[]> {
  return apiRequest<ItemCatalogo[]>(`/api/v1/catalogos/${catalogo}`, { signal });
}

export function createItemCatalogo(
  catalogo: CatalogoAdministrable,
  input: { codigo?: string; nombre: string },
): Promise<ItemCatalogo> {
  return apiRequest<ItemCatalogo>(`/api/v1/catalogos/${catalogo}`, { method: "POST", body: input });
}

export function renameItemCatalogo(catalogo: CatalogoAdministrable, id: number, nombre: string): Promise<ItemCatalogo> {
  return apiRequest<ItemCatalogo>(`/api/v1/catalogos/${catalogo}/${id}`, { method: "PUT", body: { nombre } });
}

export function deleteItemCatalogo(catalogo: CatalogoAdministrable, id: number): Promise<void> {
  return apiRequest<void>(`/api/v1/catalogos/${catalogo}/${id}`, { method: "DELETE" });
}

// ── Papelera ────────────────────────────────────────────────────────────────────────────────

export function listPapelera(params: ListParams, signal?: AbortSignal): Promise<PapeleraPage> {
  return apiRequest<PapeleraPage>(`/api/v1/papelera?${query(params)}`, { signal });
}

export function restaurarRegistro(id: number): Promise<{ tipo: TipoRegistro; id: number }> {
  return apiRequest<{ tipo: TipoRegistro; id: number }>(`/api/v1/papelera/${id}/restaurar`, { method: "POST" });
}

export function eliminarDefinitivamente(id: number): Promise<void> {
  return apiRequest<void>(`/api/v1/papelera/${id}`, { method: "DELETE" });
}
