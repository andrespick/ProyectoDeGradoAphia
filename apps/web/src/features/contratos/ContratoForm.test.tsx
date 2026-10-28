import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { apiError, CATALOGOS, contrato, json, mockApi, page, persona } from "../../test/mockApi";
import { ContratoForm } from "./ContratoForm";

const INMUEBLE = {
  id: 1,
  direccion: "Calle 93B # 11A-44",
  ciudad: "Bogotá",
  matricula: "50C-1",
  canon: null,
  moneda: null,
  estado: "DISPONIBLE",
  servicios: [],
  propietarios: [persona(1, "Laura Dueña", "1001", ["propietario"])],
  total_contratos: 0,
};
const PERSONAS: Record<string, ReturnType<typeof persona>> = {
  "1003": persona(3, "Carlos Inquilino", "1003", ["arrendatario"]),
  "1004": persona(4, "Pedro Fiador", "1004", []),
};

function setup(props: Partial<Parameters<typeof ContratoForm>[0]> = {}) {
  mockApi({
    "GET /api/v1/catalogos": () => json(CATALOGOS),
    "GET /api/v1/inmuebles": (_init, url) => json(page(url.searchParams.get("q") === "93b" ? [INMUEBLE] : [])),
    "GET /api/v1/personas/buscar": (_init, url) => {
      const encontrada = PERSONAS[url.searchParams.get("identificacion") ?? ""];
      return encontrada ? json(encontrada) : apiError(404, "persona_no_encontrada", "La persona no existe.");
    },
  });
  const onSubmit = props.onSubmit ?? vi.fn().mockResolvedValue(undefined);
  render(<ContratoForm modo="crear" onSubmit={onSubmit} onCancel={vi.fn()} {...props} />);
  return { onSubmit, user: userEvent.setup() };
}

async function elegirPersona(user: ReturnType<typeof userEvent.setup>, grupo: string, identificacion: string) {
  const picker = screen.getByRole("group", { name: grupo });
  await user.type(within(picker).getByLabelText("Identificación"), identificacion);
  await user.click(within(picker).getByRole("button", { name: /^Buscar/ }));
  await user.click(await within(picker).findByRole("button", { name: "Seleccionar" }));
}

describe("ContratoForm", () => {
  it("precarga los propietarios del inmueble, valida las fechas y envía el cuerpo", async () => {
    const { user, onSubmit } = setup();

    await user.click(screen.getByRole("button", { name: "Guardar contrato" }));
    expect(screen.getByText("Seleccione el inmueble del contrato.")).toBeInTheDocument();
    expect(screen.getByText("Ingrese la fecha de inicio.")).toBeInTheDocument();
    expect(screen.getByText("Asocie al menos un propietario.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();

    const inmueble = screen.getByRole("group", { name: "Inmueble" });
    await user.type(within(inmueble).getByLabelText(/Dirección o matrícula/), "93b");
    await user.click(within(inmueble).getByRole("button", { name: "Buscar inmueble" }));
    await user.click(await screen.findByRole("button", { name: "Seleccionar" }));
    expect(screen.getByRole("button", { name: "Cambiar inmueble" })).toBeInTheDocument();
    expect(within(screen.getByRole("list", { name: "Propietarios" })).getByText("Laura Dueña")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/Fecha de inicio/), "2026-01-01");
    await user.type(screen.getByLabelText(/Fecha de fin/), "2025-12-31");
    await user.click(screen.getByRole("button", { name: "Guardar contrato" }));
    expect(screen.getByText("La fecha de fin no puede ser anterior a la de inicio.")).toBeInTheDocument();
    await user.clear(screen.getByLabelText(/Fecha de fin/));
    await user.type(screen.getByLabelText(/Fecha de fin/), "2026-12-31");

    await elegirPersona(user, "Arrendatario", "1003");
    await elegirPersona(user, "Codeudores", "1004");
    await user.type(screen.getByLabelText(/Canon pactado/), "1.500.000");
    await user.type(screen.getByLabelText(/Texto completo/), "CONTRATO");
    await user.click(screen.getByRole("button", { name: "Guardar contrato" }));

    expect(onSubmit).toHaveBeenCalledWith({
      tipo: "ARRENDAMIENTO",
      inmueble_id: 1,
      fecha_inicio: "2026-01-01",
      fecha_fin: "2026-12-31",
      canon_pactado: "1500000",
      condiciones: null,
      texto: "CONTRATO",
      propietarios_ids: [1],
      arrendatario_id: 3,
      codeudores_ids: [4],
    });
  });

  it("al editar muestra los datos y no deja elegir al arrendatario como codeudor", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { user } = setup({ modo: "editar", onSubmit, inicial: contrato(7) });

    expect(screen.getByLabelText(/Fecha de inicio/)).toHaveValue("2026-01-01");
    expect(screen.getByLabelText(/Texto completo/)).toHaveValue("CONTRATO DE ARRENDAMIENTO\nTexto ficticio.");
    expect(screen.getByRole("button", { name: "Cambiar arrendatario" })).toBeInTheDocument();

    const codeudores = screen.getByRole("group", { name: "Agregar otro codeudores" });
    await user.type(within(codeudores).getByLabelText("Identificación"), "1003");
    await user.click(within(codeudores).getByRole("button", { name: /^Buscar/ }));
    expect(await within(codeudores).findByText("Esa persona ya está en la lista.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Quitar Pedro Fiador" }));
    await user.click(screen.getByRole("button", { name: "Guardar contrato" }));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ inmueble_id: 1, propietarios_ids: [1], arrendatario_id: 3, codeudores_ids: [] }),
    );
  });
});
