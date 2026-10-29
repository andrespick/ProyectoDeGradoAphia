import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { baseRoutes, DB_PRINCIPAL, mockApi } from "../test/mockApi";

function renderApp() {
  const router = createMemoryRouter(routes, { initialEntries: ["/"] });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
  return router;
}

describe("MainLayout", () => {
  beforeEach(() => sessionStorage.setItem("aphia.token", "tok.en"));

  it("el administrador de sistemas solo ve la gestión del sistema y cierra la sesión", async () => {
    mockApi(baseRoutes(DB_PRINCIPAL));
    const user = userEvent.setup();

    const router = renderApp();

    await screen.findByRole("heading", { name: "Estado del sistema" });
    expect(router.state.location.pathname).toBe("/sistema");
    const nav = screen.getByRole("navigation", { name: "Principal" });
    expect(within(nav).getAllByRole("link").map((link) => link.textContent)).toEqual([
      "Sistema",
      "Usuarios",
      "Auditoría",
      "Catálogos",
      "Configuración",
      "Papelera",
      "Ayuda",
    ]);
    expect(await screen.findByText(/Inmobiliaria Ficticia S\.A\.S\. · Gestión inmobiliaria/)).toBeInTheDocument();
    const banner = screen.getByRole("banner", { name: "Barra superior" });
    expect(within(banner).queryByRole("searchbox", { name: "Búsqueda global" })).not.toBeInTheDocument();
    expect(within(banner).getByText("Administradora Ficticia")).toBeInTheDocument();
    expect(within(banner).getByText("Administrador de Sistemas")).toBeInTheDocument();

    await user.click(within(banner).getByRole("button", { name: "Cerrar sesión" }));

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
    expect(sessionStorage.getItem("aphia.token")).toBeNull();
  });

  it("el menú solo muestra Usuarios al administrador de sistemas", async () => {
    mockApi(baseRoutes({ ...DB_PRINCIPAL, roles: ["administrativo"] }));

    renderApp();

    const nav = await screen.findByRole("navigation", { name: "Principal" });
    expect(within(nav).getByRole("link", { name: "Inicio" })).toBeInTheDocument();
    expect(within(nav).queryByRole("link", { name: "Usuarios" })).not.toBeInTheDocument();
    const banner = screen.getByRole("banner", { name: "Barra superior" });
    expect(within(banner).getByRole("searchbox", { name: "Búsqueda global" })).toBeInTheDocument();
  });
});
