import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { apiError, baseRoutes, DEV_PRINCIPAL, json, mockApi } from "../test/mockApi";
import { ProtectedRoute } from "./ProtectedRoute";
import { routes } from "./routes";

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
  return router;
}

describe("ProtectedRoute", () => {
  it("redirige a /login cuando no hay sesión", async () => {
    mockApi({ "GET /api/v1/auth/me": () => apiError(401, "no_autenticado", "Se requiere autenticación.") });

    const router = renderAt("/usuarios");

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
    expect(router.state.location.state).toEqual({ from: "/usuarios" });
  });

  it("muestra la ruta protegida al administrador de sistemas", async () => {
    mockApi({
      ...baseRoutes(),
      "GET /api/v1/usuarios": () => json({ items: [], total: 0, limit: 20, offset: 0 }),
    });

    renderAt("/usuarios");

    expect(await screen.findByRole("heading", { name: /Usuarios y roles/ })).toBeInTheDocument();
  });

  it("niega /usuarios a un asesor", async () => {
    mockApi(baseRoutes({ ...DEV_PRINCIPAL, roles: ["asesor"] }));

    renderAt("/usuarios");

    expect(await screen.findByRole("alert")).toHaveTextContent("No tiene permisos");
  });

  it("niega el acceso sin el rol requerido en una ruta cualquiera", async () => {
    mockApi({ "GET /api/v1/auth/me": () => json({ ...DEV_PRINCIPAL, roles: ["asesor"] }) });
    const router = createMemoryRouter(
      [
        {
          element: <ProtectedRoute roles={["admin_sistemas"]} />,
          children: [{ path: "/solo-admin", element: <h1>Solo administradores</h1> }],
        },
      ],
      { initialEntries: ["/solo-admin"] },
    );
    render(
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("No tiene permisos");
    expect(screen.queryByText("Solo administradores")).not.toBeInTheDocument();
  });
});
