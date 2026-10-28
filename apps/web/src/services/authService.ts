import type { Principal } from "../types/auth";
import { apiRequest } from "./apiClient";

/** Identidad actual. En esta fase solo existe el usuario ficticio de desarrollo. */
export function getCurrentPrincipal(signal?: AbortSignal): Promise<Principal> {
  return apiRequest<Principal>("/api/v1/auth/me", { signal, timeoutMs: 5_000 });
}
