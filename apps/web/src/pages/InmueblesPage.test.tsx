import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { apiError, baseRoutes, DB_PRINCIPAL, json, mockApi, page, persona } from "../test/mockApi";

function inmueble(id: number, direccion: string, extras: Record<string, unknown> = {}) {
  return {
    id,
    direccion,
    ciudad: "Bogotá",
    matricula: `50C-${id}`,
    canon: "1500000.00",
    moneda: "COP",
    estado: "DISPONIBLE",
    servicios: [{ id: 1, tipo: "ENERGIA", proveedor: "Enel", numero_contrato: "E-1" }],
    propietarios: [persona(1, "Laura Dueña", "1001", ["propietario"])],
    total_contratos: 0,
    ...extras,
  };
}

function renderAt(path: string, principal: unknown = DB_PRINCIPAL, extra: Record<string, Parameters<typeof mockApi>[0][string]> = {}) {
  mockApi({ ...baseRoutes(principal), ...extra });
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
  return router;
}

describe("InmueblesPage", () => {
  it("lista inmuebles con canon formateado y envía los filtros de la URL", async () => {
    const llamadas: string[] = [];
    renderAt("/inmuebles?estado=OCUPADO&ciudad=bog&propietario_id=1", DB_PRINCIPAL, {
      "GET /api/v1/inmuebles": (_init, url) => {
        llamadas.push(url.search);
        return json(page([inmueble(1, "Calle 93B # 11A-44", { estado: "OCUPADO" })]));
      },
    });

    const table = await screen.findByRole("table");
    expect(within(table).getByText("Calle 93B # 11A-44")).toBeInTheDocument();
    expect(within(table).getByText(/1\.500\.000/)).toBeInTheDocument();
    expect(within(table).getByText("Ocupado")).toBeInTheDocument();
    expect(within(table).getByRole("link", { name: "Laura Dueña" })).toHaveAttribute("href", "/propietarios/1");
    expect(within(table).getByText("ENERGIA · E-1")).toBeInTheDocument();
    expect(llamadas[0]).toContain("estado=OCUPADO");
    expect(llamadas[0]).toContain("ciudad=bog");
    expect(llamadas[0]).toContain("propietario_id=1");
    expect(screen.getByText("Propietario #1")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Portafolio de inmuebles/ })).toHaveTextContent("3 activos");
  });

  it("restablece los filtros y elimina mostrando el 409 de la API", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    const router = renderAt("/inmuebles?q=calle", DB_PRINCIPAL, {
      "GET /api/v1/inmuebles": () => json(page([inmueble(1, "Calle 1", { total_contratos: 2 })])),
      "DELETE /api/v1/inmuebles/1": () =>
        apiError(409, "inmueble_con_contratos", "No se puede eliminar el inmueble: tiene 2 contrato(s). Elimine primero los contratos."),
    });

    await screen.findByRole("table");
    await user.click(screen.getByRole("button", { name: "Restablecer filtros" }));
    await waitFor(() => expect(router.state.location.search).toBe(""));

    await user.click(screen.getByRole("button", { name: "Eliminar Calle 1" }));
    expect(await screen.findByText(/tiene 2 contrato\(s\)/)).toBeInTheDocument();
  });

  it("el asesor registra y edita pero no ve «Eliminar»", async () => {
    renderAt("/inmuebles", { ...DB_PRINCIPAL, roles: ["asesor"] }, {
      "GET /api/v1/inmuebles": () => json(page([inmueble(1, "Calle 1")])),
    });

    await screen.findByRole("table");
    expect(screen.getByRole("link", { name: "Registrar inmueble" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Editar Calle 1" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Eliminar/ })).not.toBeInTheDocument();
  });

  it("abre el panel de edición con los datos y guarda", async () => {
    let guardado: unknown = null;
    const user = userEvent.setup();
    const router = renderAt("/inmuebles/1/editar", DB_PRINCIPAL, {
      "GET /api/v1/inmuebles": () => json(page([inmueble(1, "Calle 1")])),
      "GET /api/v1/inmuebles/1": () => json(inmueble(1, "Calle 1")),
      "PUT /api/v1/inmuebles/1": (init) => {
        guardado = JSON.parse(String(init?.body));
        return json(inmueble(1, "Calle 1 editada"));
      },
    });

    const dialog = await screen.findByRole("dialog", { name: "Editar inmueble" });
    const direccion = await within(dialog).findByLabelText(/Dirección completa/);
    expect(direccion).toHaveValue("Calle 1");
    await user.clear(direccion);
    await user.type(direccion, "Calle 1 editada");
    await user.click(within(dialog).getByRole("button", { name: "Guardar inmueble" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/inmuebles"));
    expect(guardado).toMatchObject({ direccion: "Calle 1 editada", propietarios_ids: [1], canon: "1500000.00" });
    expect(await screen.findByRole("status")).toHaveTextContent("Inmueble actualizado correctamente.");
  });
});
