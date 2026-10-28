import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { apiError, baseRoutes, DB_PRINCIPAL, json, mockApi, usuario } from "../test/mockApi";

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
  return router;
}

describe("UsuariosPage", () => {
  it("lista usuarios, filtra por la URL y desbloquea una cuenta", async () => {
    let bloqueada = true;
    const items = () => [
      usuario(1, "admin", "admin_sistemas"),
      usuario(2, "dbermeo", "administrativo", {
        bloqueada,
        intentos_fallidos: bloqueada ? 3 : 0,
        bloqueada_hasta: bloqueada ? "2026-10-28T23:00:00Z" : null,
      }),
    ];
    const fetchMock = mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/usuarios": (_init, url) => {
        const estado = url.searchParams.get("estado");
        const filtrados = items().filter((u) => (estado === "bloqueado" ? u.bloqueada : true));
        return json({ items: filtrados, total: filtrados.length, limit: 20, offset: 0 });
      },
      "POST /api/v1/usuarios/2/desbloquear": () => {
        bloqueada = false;
        return json(items()[1]);
      },
    });
    const user = userEvent.setup();

    renderAt("/usuarios?rol=administrativo");

    const table = await screen.findByRole("table");
    expect(within(table).getByText("@dbermeo")).toBeInTheDocument();
    expect(within(table).getByText("Bloqueada")).toBeInTheDocument();
    const listado = fetchMock.mock.calls.find(([url]) => String(url).includes("/api/v1/usuarios?"));
    expect(String(listado?.[0])).toContain("rol=administrativo");
    const alerta = (await screen.findAllByRole("alert")).find((a) => a.textContent?.includes("acceso suspendido"));
    expect(alerta).toHaveTextContent("Persona dbermeo");

    await user.click(within(alerta as HTMLElement).getByRole("button", { name: /Desbloquear/ }));

    expect(await screen.findByRole("status")).toHaveTextContent("quedó desbloqueada");
    await waitFor(() => expect(screen.queryByText("Bloqueada")).not.toBeInTheDocument());
  });

  it("elimina con confirmación y muestra el 409 de la API", async () => {
    mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/usuarios": () =>
        json({ items: [usuario(1, "admin", "admin_sistemas"), usuario(5, "root", "admin_sistemas")], total: 2, limit: 20, offset: 0 }),
      "DELETE /api/v1/usuarios/5": () =>
        apiError(409, "ultimo_administrador", "No se puede dejar el sistema sin un Administrador de Sistemas activo."),
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();

    renderAt("/usuarios");

    await screen.findByRole("table");
    expect(screen.getByRole("button", { name: "Eliminar admin" })).toBeDisabled(); // cuenta propia
    await user.click(screen.getByRole("button", { name: "Eliminar root" }));

    expect(window.confirm).toHaveBeenCalled();
    expect(await screen.findByText(/sin un Administrador de Sistemas activo/)).toBeInTheDocument();
  });

  it("abre el panel de registro desde la ruta hija y vuelve a la lista al guardar", async () => {
    const creados: unknown[] = [];
    mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/usuarios": () => json({ items: [], total: creados.length, limit: 20, offset: 0 }),
      "POST /api/v1/usuarios": (init) => {
        creados.push(JSON.parse(String(init?.body)));
        return json(usuario(9, "nuevo", "asesor"), 201);
      },
    });
    const user = userEvent.setup();

    const router = renderAt("/usuarios/nuevo");

    const dialog = await screen.findByRole("dialog", { name: "Registrar usuario" });
    await user.type(within(dialog).getByLabelText(/Nombre de usuario/), "nuevo.asesor");
    await user.selectOptions(within(dialog).getByLabelText(/^Rol/), "asesor");
    await user.type(within(dialog).getByLabelText(/^Clave/), "Clave.Segura1");
    await user.type(within(dialog).getByLabelText(/Nombre completo/), "Nuevo Asesor");
    await user.selectOptions(within(dialog).getByLabelText(/Tipo de identificación/), "CC");
    await user.type(within(dialog).getByLabelText(/^Identificación/), "1234567");
    await user.type(within(dialog).getByLabelText(/Correo electrónico/), "nuevo@example.test");
    await user.click(within(dialog).getByRole("button", { name: "Guardar usuario" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/usuarios"));
    expect(creados[0]).toMatchObject({ usuario: "nuevo.asesor", rol: "asesor", clave: "Clave.Segura1" });
    expect(await screen.findByRole("status")).toHaveTextContent("Usuario registrado correctamente.");
  });
});
