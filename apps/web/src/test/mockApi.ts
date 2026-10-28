import { vi } from "vitest";

type Handler = (init: RequestInit | undefined, url: URL) => Response | Promise<Response>;

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function apiError(status: number, codigo: string, mensaje: string, detalles?: unknown[]) {
  return json({ error: { codigo, mensaje, request_id: "test", detalles } }, status);
}

/** Sustituye fetch por un enrutador simple: claves "METODO /ruta" (sin query string). */
export function mockApi(routes: Record<string, Handler>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(raw, "http://localhost");
    const key = `${(init?.method ?? "GET").toUpperCase()} ${url.pathname}`;
    const handler = routes[key];
    if (!handler) return apiError(404, "no_encontrado", `Sin mock para ${key}`);
    return handler(init, url);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export function page<T>(items: T[]) {
  return { items, total: items.length, limit: 20, offset: 0 };
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
  roles: ["admin_sistemas"],
  modo: "development",
};

export const DB_PRINCIPAL = {
  sujeto: "1",
  nombre: "Administradora Ficticia",
  roles: ["admin_sistemas"],
  modo: "database",
};

export const LOGIN_OK = {
  token: "cuerpo.firma",
  expira_en: "2026-10-28T23:00:00Z",
  principal: DB_PRINCIPAL,
};

export const RESUMEN = {
  personas: { total: 6, propietarios: 2, arrendatarios: 2, codeudores: 3 },
  inmuebles: { total: 3, ocupados: 1, disponibles: 1 },
  contratos: {
    total: 2,
    vigentes: 2,
    por_vencer_30: 1,
    por_vencer_60: 1,
    finalizados: 0,
    codeudores_vinculados: 3,
  },
  usuarios: { total: 3, activos: 2, bloqueados: 1 },
};

export const CATALOGOS = {
  tipos_identificacion: [
    { codigo: "CC", nombre: "Cédula de ciudadanía" },
    { codigo: "NIT", nombre: "NIT" },
  ],
  papeles: [
    { codigo: "propietario", nombre: "Propietario" },
    { codigo: "arrendatario", nombre: "Arrendatario" },
    { codigo: "codeudor", nombre: "Codeudor" },
  ],
  roles: [
    { codigo: "admin_sistemas", nombre: "Administrador de Sistemas" },
    { codigo: "administrativo", nombre: "Administrativo" },
    { codigo: "asesor", nombre: "Asesor" },
  ],
  estados_ocupacion: [
    { codigo: "DISPONIBLE", nombre: "Disponible" },
    { codigo: "OCUPADO", nombre: "Ocupado" },
  ],
  tipos_contrato: [
    { codigo: "ARRENDAMIENTO", nombre: "Arrendamiento" },
    { codigo: "ADMINISTRACION", nombre: "Administración" },
  ],
  tipos_cuenta_bancaria: [
    { codigo: "AHORROS", nombre: "Ahorros" },
    { codigo: "CORRIENTE", nombre: "Corriente" },
  ],
  tipos_servicio: [
    { codigo: "AGUA", nombre: "Acueducto y alcantarillado" },
    { codigo: "ENERGIA", nombre: "Energía" },
  ],
  monedas: [{ codigo: "COP", nombre: "Peso colombiano" }],
  ciudades: [{ id: 9001, nombre: "Bogotá" }],
  bancos: ["Bancolombia"],
  proveedores_servicios: ["EPM"],
};

export function persona(
  id: number,
  nombre: string,
  identificacion: string,
  papeles: ("propietario" | "arrendatario" | "codeudor")[],
  extras: Record<string, unknown> = {},
) {
  return {
    id,
    nombre,
    tipo_identificacion: "CC",
    identificacion,
    telefono: "3001234567",
    correo: `${identificacion}@example.test`,
    direccion: null,
    papeles,
    cuenta_bancaria: null,
    total_inmuebles: 0,
    ...extras,
  };
}

export function personaDetalle(base: ReturnType<typeof persona>, extras: Record<string, unknown> = {}) {
  return {
    ...base,
    inmuebles: [],
    contratos_como_propietario: [],
    contratos_como_arrendatario: [],
    contratos_como_codeudor: [],
    usuario: null,
    ...extras,
  };
}

export function contrato(id: number, extras: Record<string, unknown> = {}) {
  return {
    id,
    tipo: "ARRENDAMIENTO",
    inmueble: { id: 1, direccion: "Calle 93B # 11A-44", ciudad: "Bogotá", estado: "OCUPADO" },
    fecha_inicio: "2026-01-01",
    fecha_fin: "2026-12-31",
    canon_pactado: "1500000.00",
    moneda: "COP",
    estado: "vigente" as const,
    dias_restantes: 64,
    propietarios: [persona(1, "Laura Dueña", "1001", ["propietario"])],
    arrendatario: persona(3, "Carlos Inquilino", "1003", ["arrendatario"]),
    codeudores: [persona(4, "Pedro Fiador", "1004", ["codeudor"])],
    condiciones: "Pago anticipado.",
    texto: "CONTRATO DE ARRENDAMIENTO\nTexto ficticio.",
    ...extras,
  };
}

export function usuario(
  id: number,
  usuario: string,
  rol: "admin_sistemas" | "administrativo" | "asesor",
  extras: Record<string, unknown> = {},
) {
  return {
    id,
    usuario,
    nombre: `Persona ${usuario}`,
    tipo_identificacion: "CC",
    identificacion: `10000${id}`,
    correo: `${usuario}@example.test`,
    rol,
    activo: true,
    bloqueada: false,
    bloqueada_hasta: null,
    intentos_fallidos: 0,
    creado_en: "2026-10-27T15:00:00Z",
    ...extras,
  };
}

/** Mocks mínimos para que el cascarón autenticado cargue (sesión, estado, resumen). */
export function baseRoutes(principal: unknown = DEV_PRINCIPAL): Record<string, Handler> {
  return {
    "GET /api/health": () => json(HEALTH_OK),
    "GET /api/ready": () => json(READY_OK),
    "GET /api/v1/auth/me": () => json(principal),
    "GET /api/v1/resumen": () => json(RESUMEN),
    "GET /api/v1/catalogos": () => json(CATALOGOS),
  };
}
