import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { baseRoutes, contrato, DB_PRINCIPAL, json, mockApi, persona } from "../test/mockApi";

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

describe("ContratoDetallePage", () => {
  it("muestra partes y texto, imprime y asocia un codeudor sin editar el resto", async () => {
    const print = vi.spyOn(window, "print").mockImplementation(() => undefined);
    let guardado: unknown = null;
    const user = userEvent.setup();
    renderAt("/contratos/7", DB_PRINCIPAL, {
      "GET /api/v1/contratos/7": () => json(contrato(7)),
      "GET /api/v1/personas/buscar": () => json(persona(5, "Sofía Fiadora", "1005", [])),
      "PUT /api/v1/contratos/7": (init) => {
        guardado = JSON.parse(String(init?.body));
        return json(contrato(7, { codeudores: [persona(4, "Pedro Fiador", "1004", []), persona(5, "Sofía Fiadora", "1005", [])] }));
      },
    });

    expect(await screen.findByRole("heading", { level: 1, name: /Contrato #7 · Arrendamiento/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Laura Dueña/ })).toHaveAttribute("href", "/propietarios/1");
    expect(screen.getByRole("link", { name: /Carlos Inquilino/ })).toHaveAttribute("href", "/clientes/3");
    expect(document.querySelector("pre.contrato-texto")).toHaveTextContent(/CONTRATO DE ARRENDAMIENTO\s+Texto ficticio\./);

    await user.click(screen.getByRole("button", { name: /Imprimir/ }));
    expect(print).toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Asociar codeudor" }));
    const picker = screen.getByRole("group", { name: "Nuevo codeudor" });
    await user.type(within(picker).getByLabelText("Identificación"), "1005");
    await user.click(within(picker).getByRole("button", { name: /^Buscar/ }));
    await user.click(await screen.findByRole("button", { name: "Seleccionar" }));

    await waitFor(() => expect(guardado).not.toBeNull());
    expect(guardado).toMatchObject({
      tipo: "ARRENDAMIENTO",
      inmueble_id: 1,
      propietarios_ids: [1],
      arrendatario_id: 3,
      codeudores_ids: [4, 5],
      texto: "CONTRATO DE ARRENDAMIENTO\nTexto ficticio.",
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Codeudores del contrato actualizados.");
    expect(within(screen.getByRole("list", { name: "Codeudores del contrato" })).getByText("Sofía Fiadora")).toBeInTheDocument();
  });

  it("sin texto deshabilita la impresión y el asesor no ve «Eliminar»", async () => {
    renderAt("/contratos/7", { ...DB_PRINCIPAL, roles: ["asesor"] }, {
      "GET /api/v1/contratos/7": () => json(contrato(7, { texto: null, codeudores: [] })),
    });

    expect(await screen.findByRole("button", { name: /Imprimir/ })).toBeDisabled();
    expect(screen.getByText(/no tiene texto completo registrado/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Editar" })).toHaveAttribute("href", "/contratos/7/editar");
    expect(screen.queryByRole("button", { name: "Eliminar" })).not.toBeInTheDocument();
  });
});
