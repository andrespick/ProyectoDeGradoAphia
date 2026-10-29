import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { apiError, baseRoutes, contrato, ADMINISTRATIVO_PRINCIPAL, json, mockApi, page, persona } from "../test/mockApi";

function renderAt(path: string, principal: unknown = ADMINISTRATIVO_PRINCIPAL, extra: Record<string, Parameters<typeof mockApi>[0][string]> = {}) {
  mockApi({ ...baseRoutes(principal), ...extra });
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
  return router;
}

describe("ContratosPage", () => {
  it("lista contratos con estado calculado y envía los filtros de la URL", async () => {
    const llamadas: string[] = [];
    renderAt("/contratos?estado=por_vencer&inmueble_id=1&q=calle&fecha_desde=2026-01-01", ADMINISTRATIVO_PRINCIPAL, {
      "GET /api/v1/contratos": (_init, url) => {
        llamadas.push(url.search);
        return json(page([contrato(1, { dias_restantes: 20 }), contrato(2, { estado: "finalizado", dias_restantes: 0, fecha_fin: "2026-02-01" })]));
      },
    });

    const table = await screen.findByRole("table");
    expect(within(table).getByText("#1 · Arrendamiento")).toBeInTheDocument();
    expect(within(table).getByText("20 días restantes")).toBeInTheDocument();
    expect(within(table).getByText("Por vencer")).toBeInTheDocument();
    expect(within(table).getByText("Finalizado")).toBeInTheDocument();
    expect(within(table).getAllByText(/1\.500\.000/)).toHaveLength(2);
    expect(within(table).getByRole("link", { name: "Ver contrato 1" })).toHaveAttribute("href", "/contratos/1");
    expect(llamadas[0]).toContain("estado=por_vencer");
    expect(llamadas[0]).toContain("inmueble_id=1");
    expect(llamadas[0]).toContain("fecha_desde=2026-01-01");
    expect(screen.getByText("Inmueble #1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Por vencer", pressed: true })).toBeInTheDocument();
  });

  it("cambia de pestaña, restablece filtros y muestra el 409 al eliminar", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    const router = renderAt("/contratos?q=calle", ADMINISTRATIVO_PRINCIPAL, {
      "GET /api/v1/contratos": () => json(page([contrato(1)])),
      "DELETE /api/v1/contratos/1": () =>
        apiError(409, "contrato_con_dependencias", "No se puede modificar ni eliminar el contrato: tiene 2 registro(s) financiero(s)."),
    });

    await screen.findByRole("table");
    await user.click(screen.getByRole("button", { name: "Finalizados" }));
    await waitFor(() => expect(router.state.location.search).toContain("estado=finalizado"));
    await user.click(screen.getByRole("button", { name: "Restablecer filtros" }));
    await waitFor(() => expect(router.state.location.search).not.toContain("q=calle"));

    await user.click(screen.getByRole("button", { name: "Eliminar contrato 1" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/2 registro\(s\) financiero\(s\)/);
  });

  it("el asesor crea y edita pero no ve «Eliminar»", async () => {
    renderAt("/contratos", { ...ADMINISTRATIVO_PRINCIPAL, roles: ["asesor"] }, {
      "GET /api/v1/contratos": () => json(page([contrato(1, { codeudores: [persona(9, "Sin Codeudor", "9", [])] })])),
    });

    await screen.findByRole("table");
    expect(screen.getByRole("link", { name: "Nuevo contrato" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Editar contrato 1" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Eliminar/ })).not.toBeInTheDocument();
  });
});
