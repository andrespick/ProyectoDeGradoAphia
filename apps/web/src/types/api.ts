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
