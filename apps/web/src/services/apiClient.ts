import type { ApiErrorBody, ApiErrorDetail } from "../types/api";
import { clearToken, getToken, SESSION_EXPIRED_EVENT } from "./session";

const DEFAULT_TIMEOUT_MS = 10_000;
const LOGIN_PATH = "/api/v1/auth/login";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiErrorDetail[];
  readonly requestId: string | null;

  constructor(
    message: string,
    options: { status: number; code: string; details?: ApiErrorDetail[]; requestId?: string | null },
  ) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.details = options.details ?? [];
    this.requestId = options.requestId ?? null;
  }
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
  timeoutMs?: number;
  /** Estados no-2xx que se devuelven como respuesta válida (p. ej. 503 en /api/ready). */
  acceptStatus?: number[];
}

export function apiBaseUrl(): string {
  return (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  const cancel = () => controller.abort();
  options.signal?.addEventListener("abort", cancel, { once: true });
  const token = getToken();

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      method: options.method ?? "GET",
      headers: {
        Accept: "application/json",
        ...(options.body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
      credentials: "omit",
    });
  } catch (error) {
    if (options.signal?.aborted) throw error; // cancelado por quien llamó
    if (controller.signal.aborted) {
      throw new ApiError("La API no respondió a tiempo.", { status: 0, code: "tiempo_agotado" });
    }
    throw new ApiError("No fue posible conectar con la API.", { status: 0, code: "sin_conexion" });
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", cancel);
  }

  // Token rechazado (vencido o rotado): se cierra la sesión en toda la aplicación.
  if (response.status === 401 && token && path !== LOGIN_PATH) {
    clearToken();
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
  }

  const payload = await readJson(response);
  if (!response.ok && !options.acceptStatus?.includes(response.status)) {
    throw toApiError(response.status, payload);
  }
  return payload as T;
}

async function readJson(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined;
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function toApiError(status: number, payload: unknown): ApiError {
  if (isErrorBody(payload)) {
    const { codigo, mensaje, request_id, detalles } = payload.error;
    return new ApiError(mensaje, { status, code: codigo, details: detalles, requestId: request_id });
  }
  return new ApiError(`La API respondió con el estado ${status}.`, { status, code: "error_http" });
}

function isErrorBody(payload: unknown): payload is ApiErrorBody {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "error" in payload &&
    typeof (payload as ApiErrorBody).error?.mensaje === "string"
  );
}

/** Mensaje para el usuario; los errores de la API llevan el código de soporte (request_id). */
export function errorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return "Ocurrió un error inesperado.";
  return error.requestId ? `${error.message} Código de soporte: ${error.requestId}.` : error.message;
}
