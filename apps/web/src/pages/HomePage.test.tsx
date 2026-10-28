import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import {
  apiError,
  cliente,
  DEV_PRINCIPAL,
  HEALTH_OK,
  json,
  mockApi,
  READY_OK,
} from "../test/mockApi";

function renderApp(path = "/") {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
}

describe("HomePage", () => {
  it("muestra el estado de la API y los clientes registrados", async () => {
    mockApi({
      "GET /api/health": () => json(HEALTH_OK),
      "GET /api/ready": () => json(READY_OK),
      "GET /api/v1/auth/me": () => json(DEV_PRINCIPAL),
      "GET /api/v1/clientes": () =>
        json({ items: [cliente(1, "Cliente Ficticio", "c@example.test")], total: 1, limit: 20, offset: 0 }),
    });

    renderApp();

    expect(within(screen.getByRole("banner")).getByText("APHIA")).toBeInTheDocument();
    expect(await screen.findByText("API conectada")).toBeInTheDocument();
    expect(screen.getByText("ASGI (Uvicorn)")).toBeInTheDocument();
    const table = await screen.findByRole("table");
    expect(within(table).getByText("Cliente Ficticio")).toBeInTheDocument();
    expect(within(table).getByText("1 cliente registrado")).toBeInTheDocument();
  });

  it("muestra estados de error cuando la API no responde", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    renderApp();

    expect(await screen.findByText("API sin conexión")).toBeInTheDocument();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("No fue posible conectar con la API.");
    expect(within(alert).getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });

  it("indica cuando la base de datos no está disponible", async () => {
    mockApi({
      "GET /api/health": () => json(HEALTH_OK),
      "GET /api/ready": () => json({ status: "not_ready", checks: { database: "unavailable" } }, 503),
      "GET /api/v1/auth/me": () => json(DEV_PRINCIPAL),
      "GET /api/v1/clientes": () =>
        apiError(503, "base_de_datos_no_disponible", "La base de datos no está disponible."),
    });

    renderApp();

    expect(await screen.findByText("API sin base de datos")).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent("La base de datos no está disponible.");
  });

  it("registra un cliente y actualiza la lista", async () => {
    const items: ReturnType<typeof cliente>[] = [];
    mockApi({
      "GET /api/health": () => json(HEALTH_OK),
      "GET /api/ready": () => json(READY_OK),
      "GET /api/v1/auth/me": () => json(DEV_PRINCIPAL),
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
});
