export interface ApiErrorDetail {
  campo: string;
  ubicacion: string;
  mensaje: string;
  tipo: string;
}

export interface ApiErrorBody {
  error: {
    codigo: string;
    mensaje: string;
    request_id: string | null;
    detalles?: ApiErrorDetail[];
  };
}

/** Respuesta paginada de todos los listados de la API. */
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
  runtime: "workers" | "asgi";
}

export interface ReadyResponse {
  status: "ready" | "not_ready";
  checks: Record<string, "ok" | "unavailable">;
}
