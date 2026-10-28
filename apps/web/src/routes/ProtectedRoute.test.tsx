import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { apiError, DEV_PRINCIPAL, json, mockApi } from "../test/mockApi";
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

    const router = renderAt("/panel");

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
  });

  it("muestra la ruta protegida con el usuario de desarrollo", async () => {
    mockApi({ "GET /api/v1/auth/me": () => json(DEV_PRINCIPAL) });

    renderAt("/panel");

    expect(await screen.findByRole("heading", { name: "Panel" })).toBeInTheDocument();
    expect(screen.getByText("Usuario de desarrollo")).toBeInTheDocument();
  });

  it("niega el acceso sin el rol requerido", async () => {
    mockApi({ "GET /api/v1/auth/me": () => json({ ...DEV_PRINCIPAL, roles: ["consulta"] }) });

    renderAt("/panel");

    expect(await screen.findByRole("alert")).toHaveTextContent("No tiene permisos");
  });
});
