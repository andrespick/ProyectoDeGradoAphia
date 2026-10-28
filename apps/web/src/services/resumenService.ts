import type { Resumen } from "../types/resumen";
import { apiRequest } from "./apiClient";

export function getResumen(signal?: AbortSignal): Promise<Resumen> {
  return apiRequest<Resumen>("/api/v1/resumen", { signal });
}
