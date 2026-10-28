import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiError, json, mockApi } from "../test/mockApi";
import { ApiError, apiRequest, errorMessage } from "./apiClient";
import { SESSION_EXPIRED_EVENT } from "./session";

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
});

describe("apiRequest", () => {
  it("devuelve el cuerpo JSON en respuestas exitosas", async () => {
    mockApi({ "GET /api/health": () => json({ status: "ok" }) });

    await expect(apiRequest("/api/health")).resolves.toEqual({ status: "ok" });
  });

  it("envía JSON en el cuerpo con la cabecera adecuada", async () => {
    const fetchMock = mockApi({ "POST /api/v1/clientes": () => json({ id: 1 }, 201) });

    await apiRequest("/api/v1/clientes", { method: "POST", body: { nombre: "A" } });

    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.body).toBe(JSON.stringify({ nombre: "A" }));
    expect(init?.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(init?.credentials).toBe("omit");
  });

  it("convierte el formato de error de la API en ApiError", async () => {
    mockApi({
      "POST /api/v1/clientes": () =>
        apiError(422, "validacion", "Los datos enviados no son válidos.", [
          { campo: "correo", ubicacion: "body", mensaje: "inválido", tipo: "value_error" },
        ]),
    });

    const error = await apiRequest("/api/v1/clientes", { method: "POST", body: {} }).catch(
      (e: unknown) => e,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 422, code: "validacion", requestId: "test" });
    expect((error as ApiError).details[0]?.campo).toBe("correo");
  });

  it("acepta estados indicados explícitamente", async () => {
    mockApi({ "GET /api/ready": () => json({ status: "not_ready" }, 503) });

    await expect(apiRequest("/api/ready", { acceptStatus: [503] })).resolves.toEqual({
      status: "not_ready",
    });
  });

  it("informa la falta de conexión con un mensaje claro", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(apiRequest("/api/health")).rejects.toMatchObject({
      code: "sin_conexion",
      message: "No fue posible conectar con la API.",
    });
  });

  it("maneja respuestas de error sin JSON", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>", { status: 502 })));

    await expect(apiRequest("/api/health")).rejects.toMatchObject({
      status: 502,
      code: "error_http",
    });
  });

  it("envía el token guardado como Bearer y no envía nada sin token", async () => {
    const fetchMock = mockApi({ "GET /api/v1/resumen": () => json({}) });

    await apiRequest("/api/v1/resumen");
    expect(fetchMock.mock.calls[0]?.[1]?.headers).not.toHaveProperty("Authorization");

    sessionStorage.setItem("aphia.token", "tok.en");
    await apiRequest("/api/v1/resumen");
    expect(fetchMock.mock.calls[1]?.[1]?.headers).toMatchObject({ Authorization: "Bearer tok.en" });
  });

  it("un 401 con token borra la sesión y avisa; en el login no", async () => {
    sessionStorage.setItem("aphia.token", "tok.en");
    mockApi({
      "GET /api/v1/usuarios": () => apiError(401, "no_autenticado", "Inicie sesión."),
      "POST /api/v1/auth/login": () => apiError(401, "credenciales_invalidas", "Incorrectas."),
    });
    let avisos = 0;
    window.addEventListener(SESSION_EXPIRED_EVENT, () => (avisos += 1));

    await expect(apiRequest("/api/v1/auth/login", { method: "POST", body: {} })).rejects.toMatchObject({
      code: "credenciales_invalidas",
    });
    expect(avisos).toBe(0);
    expect(sessionStorage.getItem("aphia.token")).toBe("tok.en");

    await expect(apiRequest("/api/v1/usuarios")).rejects.toMatchObject({ status: 401 });
    expect(avisos).toBe(1);
    expect(sessionStorage.getItem("aphia.token")).toBeNull();
  });
});

describe("apiRequest con respuestas que no son de la API", () => {
  it("rechaza un 200 que no es JSON (index.html de Pages sin VITE_API_BASE_URL)", async () => {
    mockApi({
      "GET /api/v1/auth/me": () =>
        new Response("<!doctype html><title>APHIA</title>", { status: 200, headers: { "Content-Type": "text/html" } }),
    });

    await expect(apiRequest("/api/v1/auth/me")).rejects.toMatchObject({ status: 200, code: "respuesta_invalida" });
  });
});

describe("errorMessage", () => {
  it("añade el código de soporte cuando la API devolvió request_id", () => {
    const conCodigo = new ApiError("No se puede eliminar.", { status: 409, code: "x", requestId: "abc123" });
    const sinCodigo = new ApiError("Sin conexión.", { status: 0, code: "sin_conexion" });

    expect(errorMessage(conCodigo)).toBe("No se puede eliminar. Código de soporte: abc123.");
    expect(errorMessage(sinCodigo)).toBe("Sin conexión.");
    expect(errorMessage(new Error("otro"))).toBe("Ocurrió un error inesperado.");
  });
});
