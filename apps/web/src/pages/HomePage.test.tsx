import { render, screen, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { apiError, baseRoutes, DEV_PRINCIPAL, json, mockApi } from "../test/mockApi";

function renderApp(path = "/") {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
  return router;
}

describe("HomePage", () => {
  it("saluda al usuario y muestra los indicadores y los módulos según el rol", async () => {
    mockApi(baseRoutes());

    renderApp();

    expect(await screen.findByRole("heading", { name: /Bienvenido de nuevo, Usuario/ })).toBeInTheDocument();
    const sidebar = screen.getByRole("complementary", { name: "Barra lateral" });
    expect(within(sidebar).getByText("APHIA")).toBeInTheDocument();
    expect(await within(sidebar).findByText("En línea")).toBeInTheDocument();
    expect(within(sidebar).getByText("ASGI (Uvicorn) · test")).toBeInTheDocument();
    for (const nombre of ["Inicio", "Clientes", "Propietarios", "Codeudores", "Usuarios"]) {
      expect(within(sidebar).getByRole("link", { name: nombre })).toBeInTheDocument();
    }

    const indicadores = await screen.findByRole("region", { name: "Indicadores" });
    expect(within(indicadores).getByText("Total inmuebles")).toBeInTheDocument();
    expect(within(indicadores).getByText("1 ocupados · 1 disponibles")).toBeInTheDocument();
    const modulos = screen.getByRole("region", { name: "Módulos de gestión" });
    expect(within(modulos).getByRole("link", { name: /^Clientes/ })).toHaveTextContent("6 registros");
    expect(within(modulos).getByRole("link", { name: /Gestión de usuarios/ })).toHaveTextContent("3 cuentas");
  });

  it("oculta el módulo de usuarios a quien no es administrador de sistemas", async () => {
    mockApi(baseRoutes({ ...DEV_PRINCIPAL, roles: ["asesor"] }));

    renderApp();

    await screen.findByRole("heading", { name: /Bienvenido de nuevo/ });
    const modulos = screen.getByRole("region", { name: "Módulos de gestión" });
    expect(within(modulos).getByRole("link", { name: /^Propietarios/ })).toBeInTheDocument();
    expect(within(modulos).queryByRole("link", { name: /Gestión de usuarios/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Usuarios" })).not.toBeInTheDocument();
  });

  it("envía a iniciar sesión cuando no hay sesión y muestra el estado del servidor", async () => {
    mockApi({
      "GET /api/health": () => json({}, 503),
      "GET /api/v1/auth/me": () => apiError(401, "no_autenticado", "Inicie sesión para continuar."),
    });

    const router = renderApp();

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
    expect(await screen.findByText("Sin conexión")).toBeInTheDocument();
  });

  it("muestra el error cuando el resumen no responde", async () => {
    mockApi({
      ...baseRoutes(),
      "GET /api/v1/resumen": () => apiError(503, "base_de_datos_no_disponible", "La base de datos no está disponible."),
    });
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    renderApp();

    expect(await screen.findByRole("alert")).toHaveTextContent("La base de datos no está disponible.");
  });
});
