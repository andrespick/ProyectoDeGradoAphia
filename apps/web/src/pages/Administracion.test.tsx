import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthProvider";
import { routes } from "../routes/routes";
import {
  apiError,
  baseRoutes,
  DB_PRINCIPAL,
  EMPRESA,
  ESTADO_SISTEMA,
  json,
  mockApi,
  page,
  usuario,
} from "../test/mockApi";

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
  return router;
}

const POLITICA = { max_intentos: 3, minutos_bloqueo: 15, horas_sesion: 8, largo_minimo_clave: 8 };

beforeEach(() => sessionStorage.setItem("aphia.token", "tok.en"));

describe("SistemaPage", () => {
  it("muestra el estado, avisa del respaldo atrasado y solicita uno", async () => {
    const fetchMock = mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "POST /api/v1/sistema/respaldos": () =>
        json({ id: 1, origen: "manual", estado: "solicitado", solicitado_en: "2026-10-28T15:00:00Z" }, 202),
    });
    const user = userEvent.setup();

    renderAt("/sistema");

    const kpis = await screen.findByRole("region", { name: "Indicadores del sistema" });
    expect(within(kpis).getByText("En línea")).toBeInTheDocument();
    expect(within(kpis).getByText(/Última: 0018/)).toBeInTheDocument();
    expect(screen.getByText(/No hay un respaldo exitoso en las últimas 26 horas/)).toBeInTheDocument();
    expect(screen.getByText("2,0 MB")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Solicitar respaldo ahora/ }));

    expect(await screen.findByRole("status")).toHaveTextContent("Respaldo solicitado");
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(true);
  });

  it("sin base de datos lo indica sin romper la pantalla", async () => {
    mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/sistema/estado": () =>
        json({ ...ESTADO_SISTEMA, base_de_datos: { disponible: false }, migraciones: null, registros: null, respaldos: null }),
    });

    renderAt("/sistema");

    expect(await screen.findByText("Sin conexión")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Respaldos" })).not.toBeInTheDocument();
  });
});

describe("AuditoriaPage", () => {
  it("lista los eventos con etiquetas y filtra por acción en la URL", async () => {
    const fetchMock = mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/auditoria": (_init, url) =>
        json(
          page(
            url.searchParams.get("accion") === "cuenta_bloqueada"
              ? []
              : [
                  {
                    id: 2,
                    fecha: "2026-10-28T15:00:00Z",
                    actor_id: 1,
                    actor_nombre: "Administradora Ficticia",
                    actor_usuario: "admin",
                    accion: "eliminar",
                    entidad: "persona",
                    entidad_id: 7,
                    detalle: "desde clientes",
                    request_id: "abc",
                  },
                ],
          ),
        ),
    });
    const user = userEvent.setup();

    const router = renderAt("/auditoria");

    const tabla = await screen.findByRole("table");
    expect(within(tabla).getByText("Eliminación")).toBeInTheDocument();
    expect(within(tabla).getByText("Persona #7")).toBeInTheDocument();
    expect(within(tabla).getByText("@admin")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Acción"), "cuenta_bloqueada");

    expect(await screen.findByText("No hay eventos que coincidan con los filtros.")).toBeInTheDocument();
    expect(router.state.location.search).toContain("accion=cuenta_bloqueada");
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("accion=cuenta_bloqueada"))).toBe(true);
  });
});

describe("CatalogosPage", () => {
  it("agrega, renombra y no deja eliminar un valor en uso", async () => {
    let items = [
      { id: 1, codigo: "CC", nombre: "Cédula de ciudadanía", en_uso: 4 },
      { id: 2, codigo: "PAS", nombre: "Pasaporte", en_uso: 0 },
    ];
    const fetchMock = mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/catalogos/tipos-identificacion": () => json(items),
      "GET /api/v1/catalogos/ciudades": () => json([{ id: 9001, codigo: null, nombre: "Bogotá", en_uso: 2 }]),
      "POST /api/v1/catalogos/tipos-identificacion": (init) => {
        const body = JSON.parse(String(init?.body)) as { codigo: string; nombre: string };
        items = [...items, { id: 3, ...body, en_uso: 0 }];
        return json(items[2], 201);
      },
      "PUT /api/v1/catalogos/tipos-identificacion/2": (init) => {
        const { nombre } = JSON.parse(String(init?.body)) as { nombre: string };
        items = items.map((i) => (i.id === 2 ? { ...i, nombre } : i));
        return json(items[1]);
      },
    });
    vi.spyOn(window, "prompt").mockReturnValue("Pasaporte extranjero");
    const user = userEvent.setup();

    renderAt("/catalogos");

    await screen.findByText("Cédula de ciudadanía");
    expect(screen.getByRole("button", { name: "Eliminar Cédula de ciudadanía" })).toBeDisabled();

    await user.type(screen.getByLabelText(/Código/), "rc");
    await user.type(screen.getByLabelText(/Nombre/), "Registro civil");
    await user.click(screen.getByRole("button", { name: /Agregar/ }));
    expect(await screen.findByRole("status")).toHaveTextContent("«Registro civil» agregado.");
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({ codigo: "RC", nombre: "Registro civil" });

    await user.click(screen.getByRole("button", { name: "Renombrar Pasaporte" }));
    expect(await screen.findByText("Pasaporte extranjero")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Ciudades" }));
    expect(await screen.findByText("Bogotá")).toBeInTheDocument();
    expect(screen.queryByLabelText(/Código/)).not.toBeInTheDocument();
  });
});

describe("ConfiguracionPage", () => {
  it("guarda la política y marca el campo que la API rechaza", async () => {
    let intentos = 0;
    mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/configuracion/seguridad": () => json(POLITICA),
      "PUT /api/v1/configuracion/seguridad": (init) => {
        intentos += 1;
        return intentos === 1
          ? apiError(422, "validacion", "Los datos enviados no son válidos.", [
              { campo: "max_intentos", ubicacion: "body", mensaje: "Input should be less than or equal to 10", tipo: "x" },
            ])
          : json(JSON.parse(String(init?.body)));
      },
      "PUT /api/v1/configuracion/empresa": (init) => json(JSON.parse(String(init?.body))),
    });
    const user = userEvent.setup();

    renderAt("/configuracion");

    const intentosCampo = await screen.findByLabelText(/Intentos antes del bloqueo/);
    await user.clear(intentosCampo);
    await user.type(intentosCampo, "11");
    await user.click(screen.getByRole("button", { name: "Guardar política" }));
    expect(await screen.findByText("Input should be less than or equal to 10")).toBeInTheDocument();
    expect(intentosCampo).toHaveAttribute("aria-invalid", "true");

    await user.clear(intentosCampo);
    await user.type(intentosCampo, "5");
    await user.click(screen.getByRole("button", { name: "Guardar política" }));
    expect(await screen.findByText(/Política de seguridad guardada/)).toBeInTheDocument();

    expect(screen.getByLabelText(/Razón social/)).toHaveValue(EMPRESA.nombre);
    expect(screen.getByText(/El logotipo no se puede cambiar/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Guardar datos" }));
    expect(await screen.findByText("Datos de la empresa guardados.")).toBeInTheDocument();
  });
});

describe("PapeleraPage", () => {
  it("restaura un registro y elimina otro definitivamente", async () => {
    let liberar = () => {};
    let registros = [
      {
        id: 1,
        tipo: "persona",
        entidad_id: 7,
        descripcion: "Ana García (CC 1020)",
        eliminado_en: "2026-10-28T15:00:00Z",
        eliminado_por: "Diana Administrativa",
      },
      {
        id: 2,
        tipo: "contrato",
        entidad_id: 3,
        descripcion: "Contrato 3 · Calle 1",
        eliminado_en: "2026-10-28T16:00:00Z",
        eliminado_por: "Diana Administrativa",
      },
    ];
    mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/papelera": () => json(page(registros)),
      // La restauración tarda hasta liberarla: el doble clic ocurre con la primera en curso.
      "POST /api/v1/papelera/1/restaurar": () =>
        new Promise<Response>((resolve) => {
          liberar = () => {
            registros = registros.filter((r) => r.id !== 1);
            resolve(json({ tipo: "persona", id: 12 }));
          };
        }),
      "DELETE /api/v1/papelera/2": () => {
        registros = registros.filter((r) => r.id !== 2);
        return new Response(null, { status: 204 });
      },
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();

    const fetchMock = vi.mocked(fetch);
    renderAt("/papelera");

    await user.dblClick(await screen.findByRole("button", { name: "Restaurar Ana García (CC 1020)" }));
    liberar();
    expect(await screen.findByRole("status")).toHaveTextContent("se restauró como persona #12");
    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1);

    await user.click(screen.getByRole("button", { name: "Eliminar definitivamente Contrato 3 · Calle 1" }));
    expect(window.confirm).toHaveBeenCalled();
    expect(await screen.findByText("La papelera está vacía.")).toBeInTheDocument();
  });
});

describe("Usuarios: clave temporal y sesiones", () => {
  it("muestra la clave temporal una vez y cierra sesiones", async () => {
    mockApi({
      ...baseRoutes(DB_PRINCIPAL),
      "GET /api/v1/usuarios": () => json(page([usuario(1, "admin", "admin_sistemas"), usuario(2, "asesor1", "asesor")])),
      "POST /api/v1/usuarios/2/restablecer-clave": () => json({ clave_temporal: "Tmp7xKq2Wn4Z" }),
      "POST /api/v1/usuarios/2/cerrar-sesiones": () => new Response(null, { status: 204 }),
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();

    renderAt("/usuarios");

    await screen.findByRole("table");
    expect(screen.getByRole("button", { name: "Restablecer la clave de admin" })).toBeDisabled();
    expect(await screen.findByText(/se suspende 15 minutos tras 3 intentos/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Restablecer la clave de asesor1" }));
    const aviso = await screen.findByRole("status");
    expect(within(aviso).getByText("Tmp7xKq2Wn4Z")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cerrar las sesiones de asesor1" }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Se cerraron las sesiones"));
    expect(screen.queryByText("Tmp7xKq2Wn4Z")).not.toBeInTheDocument();
  });
});

describe("CambiarClavePage", () => {
  it("obliga a cambiar la clave temporal y renueva la sesión", async () => {
    const temporal = { ...DB_PRINCIPAL, debe_cambiar_clave: true };
    const fetchMock = mockApi({
      ...baseRoutes(temporal),
      "POST /api/v1/auth/cambiar-clave": () =>
        json({ token: "nuevo.token", expira_en: "2026-10-28T23:00:00Z", principal: DB_PRINCIPAL }),
    });
    const user = userEvent.setup();

    const router = renderAt("/usuarios");

    expect(await screen.findByText(/restableció su contraseña/)).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/cambiar-clave");

    await user.type(screen.getByLabelText(/Contraseña temporal/), "Tmp7xKq2Wn4Z");
    await user.type(screen.getByLabelText(/^Contraseña nueva/), "Nueva.Clave22");
    await user.type(screen.getByLabelText(/Repita/), "Otra.Clave22");
    await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
    expect(screen.getByText("Las contraseñas no coinciden.")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("cambiar-clave"))).toBe(false);

    await user.clear(screen.getByLabelText(/Repita/));
    await user.type(screen.getByLabelText(/Repita/), "Nueva.Clave22");
    await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/sistema"));
    expect(sessionStorage.getItem("aphia.token")).toBe("nuevo.token");
  });
});
