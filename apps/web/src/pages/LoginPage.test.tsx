import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import { apiError, baseRoutes, DB_PRINCIPAL, json, LOGIN_OK, mockApi } from "../test/mockApi";

function renderLogin(from?: string) {
  const router = createMemoryRouter(routes, {
    initialEntries: [{ pathname: "/login", state: from ? { from } : null }],
  });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
  return router;
}

const SIN_SESION = () => apiError(401, "no_autenticado", "Inicie sesión para continuar.");

describe("LoginPage", () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  it("inicia sesión, guarda el token y vuelve a la ruta de origen", async () => {
    let sesion = false;
    const fetchMock = mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/auth/me": () => (sesion ? json(DB_PRINCIPAL) : SIN_SESION()),
      "POST /api/v1/auth/login": (init) => {
        const body = JSON.parse(String(init?.body)) as { usuario: string; clave: string };
        if (body.usuario !== "admin" || body.clave !== "Aphia.2026") {
          return apiError(401, "credenciales_invalidas", "Usuario o contraseña incorrectos.");
        }
        sesion = true;
        return json(LOGIN_OK);
      },
      "GET /api/v1/usuarios": () => json({ items: [], total: 0, limit: 20, offset: 0 }),
    });
    const user = userEvent.setup();
    const router = renderLogin("/usuarios");

    await user.type(await screen.findByLabelText("Usuario"), "admin");
    await user.type(screen.getByLabelText("Contraseña"), "Aphia.2026");
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));

    expect(await screen.findByRole("heading", { name: /Usuarios y roles/ })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/usuarios");
    expect(sessionStorage.getItem("aphia.token")).toBe("cuerpo.firma");
    expect(localStorage.getItem("aphia.token")).toBeNull();
    const usuariosCall = fetchMock.mock.calls.find(([url]) => String(url).includes("/api/v1/usuarios"));
    expect(usuariosCall?.[1]?.headers).toMatchObject({ Authorization: "Bearer cuerpo.firma" });
  });

  it("«Recordarme» guarda el token en localStorage", async () => {
    mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/auth/me": SIN_SESION,
      "POST /api/v1/auth/login": () => json(LOGIN_OK),
    });
    const user = userEvent.setup();
    renderLogin();

    await user.type(await screen.findByLabelText("Usuario"), "admin");
    await user.type(screen.getByLabelText("Contraseña"), "Aphia.2026");
    await user.click(screen.getByLabelText("Recordarme en este equipo"));
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));

    expect(await screen.findByRole("heading", { name: /Bienvenido de nuevo/ })).toBeInTheDocument();
    expect(localStorage.getItem("aphia.token")).toBe("cuerpo.firma");
  });

  it("muestra los mensajes de credenciales incorrectas y de cuenta bloqueada", async () => {
    let intentos = 0;
    mockApi({
      "GET /api/v1/auth/me": SIN_SESION,
      "GET /api/health": () => json({}),
      "POST /api/v1/auth/login": () => {
        intentos += 1;
        return intentos < 2
          ? apiError(401, "credenciales_invalidas", "Usuario o contraseña incorrectos.")
          : apiError(423, "cuenta_bloqueada", "La cuenta está bloqueada temporalmente. Intente de nuevo en 15 minuto(s) o pida al Administrador de Sistemas que la desbloquee.");
      },
    });
    const user = userEvent.setup();
    renderLogin();

    await user.type(await screen.findByLabelText("Usuario"), "admin");
    await user.type(screen.getByLabelText("Contraseña"), "mala");
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Usuario o contraseña incorrectos.");

    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("bloqueada temporalmente");
    expect(screen.getByLabelText("Usuario")).toHaveValue("admin"); // conserva lo escrito
  });

  it("permite mostrar la contraseña y exige ambos campos", async () => {
    mockApi({ "GET /api/v1/auth/me": SIN_SESION, "GET /api/health": () => json({}) });
    const user = userEvent.setup();
    renderLogin();

    const clave = await screen.findByLabelText("Contraseña");
    expect(clave).toHaveAttribute("type", "password");
    await user.click(screen.getByRole("button", { name: "Mostrar contraseña" }));
    expect(clave).toHaveAttribute("type", "text");

    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Ingrese su usuario y su contraseña.");
  });
});
