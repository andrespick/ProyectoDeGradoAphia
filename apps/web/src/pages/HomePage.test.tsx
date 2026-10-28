import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { apiError, baseRoutes, cliente, DEV_PRINCIPAL, json, mockApi } from "../test/mockApi";

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
    mockApi({
      ...baseRoutes(),
      "GET /api/v1/clientes": () =>
        json({ items: [cliente(1, "Cliente Ficticio", "c@example.test")], total: 1, limit: 20, offset: 0 }),
    });

    renderApp();

    expect(await screen.findByRole("heading", { name: /Bienvenido de nuevo, Usuario/ })).toBeInTheDocument();
    const sidebar = screen.getByRole("complementary", { name: "Barra lateral" });
    expect(within(sidebar).getByText("APHIA")).toBeInTheDocument();
    expect(await within(sidebar).findByText("En línea")).toBeInTheDocument();
    expect(within(sidebar).getByText("ASGI (Uvicorn) · test")).toBeInTheDocument();
    expect(within(sidebar).getByRole("link", { name: "Usuarios" })).toBeInTheDocument();

    const indicadores = await screen.findByRole("region", { name: "Indicadores" });
    expect(within(indicadores).getByText("Total inmuebles")).toBeInTheDocument();
    expect(within(indicadores).getByText("1 ocupados · 1 disponibles")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Gestión de usuarios/ })).toHaveTextContent("3 cuentas");
    const table = await screen.findByRole("table");
    expect(within(table).getByText("Cliente Ficticio")).toBeInTheDocument();
  });

  it("oculta el módulo de usuarios a quien no es administrador de sistemas", async () => {
    mockApi(baseRoutes({ ...DEV_PRINCIPAL, roles: ["asesor"] }));

    renderApp();

    await screen.findByRole("heading", { name: /Bienvenido de nuevo/ });
    expect(screen.queryByRole("link", { name: /Gestión de usuarios/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Usuarios" })).not.toBeInTheDocument();
  });

  it("envía a iniciar sesión cuando no hay sesión y muestra el estado del servidor", async () => {
    mockApi({
      "GET /api/health": () => json({ ...baseRoutes()["GET /api/health"] && {} }, 503),
      "GET /api/v1/auth/me": () => apiError(401, "no_autenticado", "Inicie sesión para continuar."),
    });

    const router = renderApp();

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
    expect(await screen.findByText("Sin conexión")).toBeInTheDocument();
  });

  it("registra un cliente de prueba y actualiza la lista", async () => {
    const items: ReturnType<typeof cliente>[] = [];
    mockApi({
      ...baseRoutes(),
      "GET /api/v1/clientes": () => json({ items, total: items.length, limit: 20, offset: 0 }),
      "POST /api/v1/clientes": (init) => {
        const body = JSON.parse(String(init?.body)) as { nombre: string; correo: string };
        const created = cliente(items.length + 1, body.nombre, body.correo);
        items.unshift(created);
        return json(created, 201);
      },
    });
    const user = userEvent.setup();

    renderApp();
    expect(await screen.findByText("No hay clientes registrados todavía.")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Nombre"), "Nuevo Cliente Ficticio");
    await user.type(screen.getByLabelText("Correo electrónico"), "nuevo@example.test");
    await user.click(screen.getByRole("button", { name: "Registrar cliente" }));

    const table = await screen.findByRole("table");
    expect(within(table).getByText("Nuevo Cliente Ficticio")).toBeInTheDocument();
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
