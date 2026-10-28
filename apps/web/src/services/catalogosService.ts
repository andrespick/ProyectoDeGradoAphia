import type { Catalogos } from "../types/catalogos";
import { apiRequest } from "./apiClient";

let cache: Promise<Catalogos> | null = null;

/** Catálogos para formularios. Se piden una sola vez por sesión de la pestaña. */
export function getCatalogos(): Promise<Catalogos> {
  cache ??= apiRequest<Catalogos>("/api/v1/catalogos").catch((error: unknown) => {
    cache = null;
    throw error;
  });
  return cache;
}

/** Olvida la copia en memoria (tras crear una ciudad, banco o proveedor nuevos). */
export function invalidateCatalogos(): void {
  cache = null;
}
