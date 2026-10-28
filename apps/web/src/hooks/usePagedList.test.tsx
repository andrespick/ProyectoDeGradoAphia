import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { Page } from "../types/api";
import { type ListParams, usePagedList } from "./usePagedList";

const FILTROS = ["q"] as const;

function Lista({ fetcher }: { fetcher: (p: ListParams, s: AbortSignal) => Promise<Page<string>> }) {
  const lista = usePagedList(fetcher, { filtros: FILTROS, limitPorDefecto: 10 });
  return (
    <div>
      <p>{lista.loading ? "cargando" : `total ${lista.total}`}</p>
      <p>offset {lista.offset}</p>
      <p>q {lista.filtros.q ?? "-"}</p>
      <ul>
        {lista.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <button type="button" onClick={() => lista.setFiltros({ q: "ana" })}>
        filtrar
      </button>
      <button type="button" onClick={() => lista.setOffset(10)}>
        siguiente
      </button>
    </div>
  );
}

function renderAt(path: string, fetcher: (p: ListParams, s: AbortSignal) => Promise<Page<string>>) {
  const router = createMemoryRouter([{ path: "/", element: <Lista fetcher={fetcher} /> }], {
    initialEntries: [path],
  });
  render(<RouterProvider router={router} />);
  return router;
}

describe("usePagedList", () => {
  it("lee filtros y paginación de la URL y los escribe al cambiarlos", async () => {
    const fetcher = vi.fn(async (params: ListParams) => ({
      items: [`item-${params.offset}-${params.filtros.q ?? ""}`],
      total: 25,
      limit: params.limit,
      offset: params.offset,
    }));
    const router = renderAt("/?q=inicial&offset=20", fetcher);

    expect(await screen.findByText("total 25")).toBeInTheDocument();
    expect(fetcher).toHaveBeenLastCalledWith(
      { limit: 10, offset: 20, filtros: { q: "inicial" } },
      expect.any(AbortSignal),
    );

    await userEvent.click(screen.getByRole("button", { name: "filtrar" }));
    await waitFor(() => expect(router.state.location.search).toBe("?q=ana"));
    expect(await screen.findByText("item-0-ana")).toBeInTheDocument(); // el filtro reinicia el offset

    await userEvent.click(screen.getByRole("button", { name: "siguiente" }));
    await waitFor(() => expect(router.state.location.search).toBe("?q=ana&offset=10"));
    expect(await screen.findByText("item-10-ana")).toBeInTheDocument();
  });

  it("expone el mensaje de error de la API", async () => {
    const fetcher = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });
    renderAt("/", fetcher);

    expect(await screen.findByText("total 0")).toBeInTheDocument();
  });
});
