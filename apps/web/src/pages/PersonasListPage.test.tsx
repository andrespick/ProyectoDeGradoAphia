import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { apiError, baseRoutes, ADMINISTRATIVO_PRINCIPAL, json, mockApi, page, persona, personaDetalle } from "../test/mockApi";

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

const PERSONAS = [
  persona(1, "Ana García", "1020", ["arrendatario"]),
  persona(2, "Mario Dueño", "1030", ["propietario", "codeudor"], {
    cuenta_bancaria: { id: 1, banco: "Bancolombia", tipo: "AHORROS", numero: "0123456789" },
    total_inmuebles: 2,
  }),
];

describe("PersonasListPage", () => {
  it("lista clientes, envía los filtros de la URL y muestra los papeles", async () => {
    const llamadas: string[] = [];
    renderAt("/clientes?papel=codeudor&q=mario", ADMINISTRATIVO_PRINCIPAL, {
      "GET /api/v1/clientes": (_init, url) => {
        llamadas.push(url.search);
        return json(page(PERSONAS));
      },
    });

    const table = await screen.findByRole("table");
    expect(within(table).getByText("Mario Dueño")).toBeInTheDocument();
    expect(within(table).getAllByText("Codeudor")).toHaveLength(1);
    expect(llamadas[0]).toContain("papel=codeudor");
    expect(llamadas[0]).toContain("q=mario");
    expect(screen.getByRole("button", { name: "Codeudores" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("heading", { name: /Gestión de clientes/ })).toHaveTextContent("6 en total");
  });

  it("propietarios muestra la cuenta enmascarada, los inmuebles y la regla de eliminación", async () => {
    renderAt("/propietarios", ADMINISTRATIVO_PRINCIPAL, { "GET /api/v1/propietarios": () => json(page([PERSONAS[1]!])) });

    const table = await screen.findByRole("table");
    expect(within(table).getByText("•••• 6789", { exact: false })).toBeInTheDocument();
    expect(within(table).getByText("2 inmuebles")).toBeInTheDocument();
    expect(screen.getByText(/no se puede eliminar/)).toBeInTheDocument();
  });

  it("el asesor puede registrar y editar pero no ve «Eliminar»", async () => {
    renderAt("/clientes", { ...ADMINISTRATIVO_PRINCIPAL, roles: ["asesor"] }, {
      "GET /api/v1/clientes": () => json(page(PERSONAS)),
    });

    await screen.findByRole("table");
    expect(screen.getByRole("link", { name: "Registrar cliente" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Editar Ana García" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Eliminar/ })).not.toBeInTheDocument();
  });

  it("elimina con confirmación y muestra el motivo cuando la API responde 409", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    renderAt("/propietarios", ADMINISTRATIVO_PRINCIPAL, {
      "GET /api/v1/propietarios": () => json(page([PERSONAS[1]!])),
      "DELETE /api/v1/propietarios/2": () =>
        apiError(409, "persona_con_dependencias", "No se puede eliminar: es propietaria de 2 inmueble(s)."),
    });

    await screen.findByRole("table");
    await user.click(screen.getByRole("button", { name: "Eliminar Mario Dueño" }));

    expect(window.confirm).toHaveBeenCalled();
    expect(await screen.findByText(/propietaria de 2 inmueble\(s\)/)).toBeInTheDocument();
  });

  it("abre el panel de registro y vuelve a la lista con el mensaje", async () => {
    const creados: unknown[] = [];
    const user = userEvent.setup();
    const router = renderAt("/codeudores/nuevo", ADMINISTRATIVO_PRINCIPAL, {
      "GET /api/v1/codeudores": () => json(page([])),
      "POST /api/v1/codeudores": (init) => {
        creados.push(JSON.parse(String(init?.body)));
        return json(persona(9, "Nuevo", "777", ["codeudor"]), 201);
      },
    });

    const dialog = await screen.findByRole("dialog", { name: "Registrar codeudor" });
    expect(within(dialog).getByLabelText("Codeudor")).toBeChecked();
    await user.type(within(dialog).getByLabelText(/Nombre completo/), "Nuevo Codeudor");
    await user.type(within(dialog).getByLabelText(/^Identificación/), "7778889");
    await user.click(within(dialog).getByRole("button", { name: "Guardar codeudor" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/codeudores"));
    expect(creados[0]).toMatchObject({ identificacion: "7778889", papeles: ["codeudor"] });
    expect(await screen.findByRole("status")).toHaveTextContent("Codeudor registrado correctamente.");
  });

  it("el detalle muestra los datos y las relaciones por papel", async () => {
    renderAt("/clientes/2", ADMINISTRATIVO_PRINCIPAL, {
      "GET /api/v1/clientes/2": () =>
        json(
          personaDetalle(PERSONAS[1]!, {
            inmuebles: [{ id: 4, direccion: "Calle 5 # 6-7", ciudad: "Bogotá", estado: "OCUPADO" }],
            contratos_como_codeudor: [
              {
                id: 3,
                tipo: "ARRENDAMIENTO",
                fecha_inicio: "2026-01-01",
                fecha_fin: null,
                inmueble: { id: 4, direccion: "Calle 5 # 6-7", ciudad: "Bogotá", estado: "OCUPADO" },
              },
            ],
            usuario: "mdueno",
          }),
        ),
    });

    expect(await screen.findByRole("heading", { name: "Mario Dueño" })).toBeInTheDocument();
    expect(screen.getByText("Bancolombia · AHORROS •••• 6789")).toBeInTheDocument();
    expect(screen.getByText("@mdueno")).toBeInTheDocument();
    const inmuebles = screen.getByRole("region", { name: "Inmuebles de los que es propietario" });
    expect(within(inmuebles).getByText("Calle 5 # 6-7")).toBeInTheDocument();
    const codeudor = screen.getByRole("region", { name: "Contratos como codeudor" });
    expect(within(codeudor).getByText(/Contrato #3/)).toBeInTheDocument();
    const arrendatario = screen.getByRole("region", { name: "Contratos como arrendatario" });
    expect(within(arrendatario).getByText("Ninguno.")).toBeInTheDocument();
  });
});
