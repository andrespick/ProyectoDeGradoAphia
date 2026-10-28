import { vi } from "vitest";

type Handler = (init: RequestInit | undefined) => Response | Promise<Response>;

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function apiError(status: number, codigo: string, mensaje: string, detalles?: unknown[]) {
  return json({ error: { codigo, mensaje, request_id: "test", detalles } }, status);
}

/** Sustituye fetch por un enrutador simple: claves "METODO /ruta". */
export function mockApi(routes: Record<string, Handler>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(raw, "http://localhost");
    const key = `${(init?.method ?? "GET").toUpperCase()} ${url.pathname}`;
    const handler = routes[key];
    if (!handler) return apiError(404, "no_encontrado", `Sin mock para ${key}`);
    return handler(init);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export const HEALTH_OK = {
  status: "ok",
  service: "aphia-api",
  version: "0.1.0",
  environment: "test",
  runtime: "asgi",
};

export const READY_OK = { status: "ready", checks: { database: "ok" } };

export const DEV_PRINCIPAL = {
  sujeto: "desarrollo-local",
  nombre: "Usuario de desarrollo",
  roles: ["admin"],
  modo: "development",
};

export function cliente(id: number, nombre: string, correo: string) {
  return {
    id,
    nombre,
    correo,
    creado_en: "2026-10-27T15:00:00Z",
    actualizado_en: "2026-10-27T15:00:00Z",
  };
}
