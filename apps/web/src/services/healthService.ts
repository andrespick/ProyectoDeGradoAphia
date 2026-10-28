import type { HealthResponse, ReadyResponse } from "../types/api";
import { apiRequest } from "./apiClient";

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/api/health", { signal, timeoutMs: 5_000 });
}

export function getReady(signal?: AbortSignal): Promise<ReadyResponse> {
  return apiRequest<ReadyResponse>("/api/ready", { signal, timeoutMs: 8_000, acceptStatus: [503] });
}
