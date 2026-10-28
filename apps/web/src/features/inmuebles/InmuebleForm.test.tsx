import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../services/apiClient";
import { apiError, CATALOGOS, json, mockApi, persona } from "../../test/mockApi";
import { normalizarDecimal } from "../../utils/formato";
import { InmuebleForm } from "./InmuebleForm";

function setup(props: Partial<Parameters<typeof InmuebleForm>[0]> = {}) {
  mockApi({
    "GET /api/v1/catalogos": () => json(CATALOGOS),
    "GET /api/v1/personas/buscar": (_init, url) =>
      url.searchParams.get("identificacion") === "1001"
        ? json(persona(1, "Laura Dueña", "1001", ["propietario"]))
        : apiError(404, "persona_no_encontrada", "La persona no existe."),
  });
  const onSubmit = props.onSubmit ?? vi.fn().mockResolvedValue(undefined);
  render(<InmuebleForm modo="crear" onSubmit={onSubmit} onCancel={vi.fn()} {...props} />);
  return { onSubmit, user: userEvent.setup() };
}

describe("normalizarDecimal", () => {
  it("acepta formato colombiano y punto decimal", () => {
    expect(normalizarDecimal("1.500.000,50")).toBe("1500000.50");
    expect(normalizarDecimal("1500000.5")).toBe("1500000.5");
    expect(normalizarDecimal("$ 850.000")).toBe("850000");
    expect(normalizarDecimal("")).toBeNull();
    expect(normalizarDecimal("abc")).toBe("NaN");
    expect(normalizarDecimal("1.234")).toBe("1234"); // miles, no decimales
  });
});

describe("InmuebleForm", () => {
  it("exige dirección y propietario, valida el canon y envía el cuerpo normalizado", async () => {
    const { user, onSubmit } = setup();

    await user.type(screen.getByLabelText(/Canon mensual/), "abc");
    await user.click(screen.getByRole("button", { name: "Guardar inmueble" }));
    expect(screen.getByText("Ingrese la dirección del inmueble.")).toBeInTheDocument();
    expect(screen.getByText("Asocie al menos un propietario.")).toBeInTheDocument();
    expect(screen.getByText(/Ingrese el canon en pesos/)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText(/Dirección completa/), "Calle 93B # 11A-44");
    await user.type(screen.getByLabelText(/Ciudad/), "Bogotá");
    await user.clear(screen.getByLabelText(/Canon mensual/));
    await user.type(screen.getByLabelText(/Canon mensual/), "1.500.000,50");
    await user.click(screen.getByLabelText("Ocupado"));
    const picker = screen.getByRole("group", { name: "Propietario legal asociado" });
    await user.type(within(picker).getByLabelText("Identificación"), "1001");
    await user.click(within(picker).getByRole("button", { name: /Buscar/ }));
    await user.click(await screen.findByRole("button", { name: "Seleccionar" }));
    expect(screen.getByText("Laura Dueña")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Agregar servicio/ }));
    await user.selectOptions(screen.getByLabelText("Tipo de servicio"), "ENERGIA");
    await user.type(screen.getByLabelText("Proveedor"), "EPM");
    await user.type(screen.getByLabelText(/Número de contrato/), "EPM-1");
    await user.click(screen.getByRole("button", { name: "Guardar inmueble" }));

    expect(onSubmit).toHaveBeenCalledWith({
      direccion: "Calle 93B # 11A-44",
      ciudad: "Bogotá",
      matricula: null,
      canon: "1500000.50",
      estado: "OCUPADO",
      servicios: [{ tipo: "ENERGIA", proveedor: "EPM", numero_contrato: "EPM-1" }],
      propietarios_ids: [1],
    });
  });

  it("permite quitar servicios y propietarios al editar", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { user } = setup({
      modo: "editar",
      onSubmit,
      inicial: {
        id: 5,
        direccion: "Carrera 7 # 1-2",
        ciudad: "Medellín",
        matricula: "M-1",
        canon: "2200000.00",
        moneda: "COP",
        estado: "DISPONIBLE",
        servicios: [{ id: 1, tipo: "AGUA", proveedor: "EPM", numero_contrato: "A-1" }],
        propietarios: [persona(1, "Laura Dueña", "1001", ["propietario"]), persona(2, "Mario", "1002", ["propietario"])],
        total_contratos: 0,
      },
    });

    expect(screen.getByLabelText(/Canon mensual/)).toHaveValue("2200000.00");
    await user.click(screen.getByRole("button", { name: "Quitar servicio 1" }));
    await user.click(screen.getByRole("button", { name: "Quitar Mario" }));
    await user.click(screen.getByRole("button", { name: "Guardar inmueble" }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ servicios: [], propietarios_ids: [1], canon: "2200000.00", matricula: "M-1" }),
    );
  });

  it("muestra el error de la API cuando el propietario ya no existe", async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError("La persona 9 no existe.", { status: 404, code: "persona_no_encontrada" }),
    );
    const { user } = setup({
      onSubmit,
      inicial: {
        id: 1,
        direccion: "Calle 1",
        ciudad: null,
        matricula: null,
        canon: null,
        moneda: null,
        estado: null,
        servicios: [],
        propietarios: [persona(9, "Fantasma", "9999", ["propietario"])],
        total_contratos: 0,
      },
    });

    await user.click(screen.getByRole("button", { name: "Guardar inmueble" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("La persona 9 no existe.");
  });
});
