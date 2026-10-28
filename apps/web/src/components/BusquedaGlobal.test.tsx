import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";

import { json, mockApi, persona } from "../test/mockApi";
import { BusquedaGlobal } from "./BusquedaGlobal";

describe("BusquedaGlobal", () => {
  it("agrupa los resultados y Enter abre el primero", async () => {
    const consultas: string[] = [];
    mockApi({
      "GET /api/v1/buscar": (_init, url) => {
        consultas.push(url.searchParams.get("q") ?? "");
        return json({
          personas: [persona(1, "Laura Dueña", "1001", ["propietario"])],
          inmuebles: [{ id: 2, direccion: "Calle 93B # 11A-44", ciudad: "Bogotá", estado: null }],
          contratos: [
            {
              id: 3,
              tipo: "ARRENDAMIENTO",
              fecha_inicio: "2026-01-01",
              fecha_fin: null,
              inmueble: { id: 2, direccion: "Calle 93B # 11A-44", ciudad: "Bogotá", estado: null },
            },
          ],
        });
      },
    });
    const router = createMemoryRouter([{ path: "/", element: <BusquedaGlobal /> }, { path: "/clientes/:id", element: <p>ficha</p> }]);
    render(<RouterProvider router={router} />);
    const user = userEvent.setup();

    const caja = screen.getByRole("searchbox", { name: "Búsqueda global" });
    await user.type(caja, "calle");

    const region = await screen.findByRole("region", { name: "Resultados de búsqueda" });
    expect(consultas).toEqual(["calle"]); // una sola consulta tras la pausa de escritura
    expect(screen.getByRole("link", { name: /Laura Dueña/ })).toHaveAttribute("href", "/clientes/1");
    expect(screen.getByRole("link", { name: /^Calle 93B/ })).toHaveAttribute("href", "/inmuebles/2/editar");
    expect(screen.getByRole("link", { name: /Contrato #3 · Arrendamiento/ })).toHaveAttribute("href", "/contratos/3");
    expect(region).toHaveTextContent("Personas");

    await user.keyboard("{Enter}");
    await waitFor(() => expect(router.state.location.pathname).toBe("/clientes/1"));
    expect(screen.queryByRole("region", { name: "Resultados de búsqueda" })).not.toBeInTheDocument();
  });
});
