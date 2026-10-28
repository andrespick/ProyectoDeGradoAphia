import { describe, expect, it, vi } from "vitest";

import { apiError, json, mockApi } from "../test/mockApi";
import { ApiError, apiRequest } from "./apiClient";

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
});
