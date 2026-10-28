import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { apiRequest } from "../../services/apiClient";
import { SESSION_EXPIRED_EVENT } from "../../services/session";
import { apiError, DB_PRINCIPAL, json, mockApi } from "../../test/mockApi";
import { AuthProvider, useAuth } from "./AuthProvider";

function Estado() {
  const { status, principal, logout } = useAuth();
  return (
    <div>
      <p>{status}</p>
      <p>{principal?.nombre ?? "sin principal"}</p>
      <button type="button" onClick={logout}>
        salir
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  it("consulta /me con el token guardado y queda autenticado", async () => {
    sessionStorage.setItem("aphia.token", "tok.en");
    const fetchMock = mockApi({ "GET /api/v1/auth/me": () => json(DB_PRINCIPAL) });

    render(
      <AuthProvider>
        <Estado />
      </AuthProvider>,
    );

    expect(await screen.findByText("autenticado")).toBeInTheDocument();
    expect(screen.getByText("Administradora Ficticia")).toBeInTheDocument();
    expect(fetchMock.mock.calls[0]?.[1]?.headers).toMatchObject({ Authorization: "Bearer tok.en" });
  });

  it("un 401 con token borra la sesión; el evento de expiración vuelve a anónimo", async () => {
    sessionStorage.setItem("aphia.token", "viejo");
    mockApi({ "GET /api/v1/auth/me": () => apiError(401, "no_autenticado", "Inicie sesión.") });

    render(
      <AuthProvider>
        <Estado />
      </AuthProvider>,
    );

    expect(await screen.findByText("anonimo")).toBeInTheDocument();
    expect(sessionStorage.getItem("aphia.token")).toBeNull();
  });

  it("cierra la sesión en toda la aplicación cuando otra petición recibe 401", async () => {
    sessionStorage.setItem("aphia.token", "tok.en");
    mockApi({
      "GET /api/v1/auth/me": () => json(DB_PRINCIPAL),
      "GET /api/v1/usuarios": () => apiError(401, "no_autenticado", "Inicie sesión."),
    });
    render(
      <AuthProvider>
        <Estado />
      </AuthProvider>,
    );
    expect(await screen.findByText("autenticado")).toBeInTheDocument();

    let disparado = 0;
    window.addEventListener(SESSION_EXPIRED_EVENT, () => (disparado += 1));
    await act(async () => {
      await apiRequest("/api/v1/usuarios").catch(() => undefined);
    });

    expect(disparado).toBe(1);
    expect(await screen.findByText("anonimo")).toBeInTheDocument();
    expect(sessionStorage.getItem("aphia.token")).toBeNull();
  });
});
