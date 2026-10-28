import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../services/apiClient";
import { CATALOGOS, json, mockApi, persona } from "../../test/mockApi";
import { PersonaForm } from "./PersonaForm";

function setup(props: Partial<Parameters<typeof PersonaForm>[0]> = {}) {
  mockApi({ "GET /api/v1/catalogos": () => json(CATALOGOS) });
  const onSubmit = props.onSubmit ?? vi.fn().mockResolvedValue(undefined);
  render(<PersonaForm modo="crear" papelFijo={null} onSubmit={onSubmit} onCancel={vi.fn()} {...props} />);
  return { onSubmit, user: userEvent.setup() };
}

describe("PersonaForm", () => {
  it("al registrar un cliente pide un tipo de cliente y valida los campos", async () => {
    const { user, onSubmit } = setup();

    await user.type(screen.getByLabelText(/Identificación/), "12 34");
    await user.type(screen.getByLabelText(/Correo electrónico/), "no-es-correo");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(screen.getByText("Ingrese el nombre completo.")).toBeInTheDocument();
    expect(screen.getByText(/solo letras, números o guiones/)).toBeInTheDocument();
    expect(screen.getByText("Ingrese un correo electrónico válido.")).toBeInTheDocument();
    expect(screen.getByText("Seleccione al menos un tipo de cliente.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();

    await user.selectOptions(await screen.findByLabelText(/Tipo de cliente/), "arrendatario");
    await user.type(screen.getByLabelText(/Nombre completo/), "  Ana García ");
    await user.clear(screen.getByLabelText(/Identificación/));
    await user.type(screen.getByLabelText(/Identificación/), "1020304050");
    await user.clear(screen.getByLabelText(/Correo electrónico/));
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(onSubmit).toHaveBeenCalledWith({
      nombre: "Ana García",
      tipo_identificacion: "CC",
      identificacion: "1020304050",
      telefono: null,
      correo: null,
      direccion: null,
      papeles: ["arrendatario"],
      cuenta_bancaria: null,
    });
  });

  it("un propietario exige dirección, contacto y cuenta bancaria", async () => {
    const { user, onSubmit } = setup({ papelFijo: "propietario" });

    expect(screen.getByLabelText("Propietario")).toBeChecked();
    expect(screen.getByLabelText("Propietario")).toBeDisabled();
    await user.type(screen.getByLabelText(/Nombre completo/), "Pedro Dueño");
    await user.type(screen.getByLabelText(/^Identificación/), "55667788");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(screen.getByText("La dirección es obligatoria para un propietario.")).toBeInTheDocument();
    expect(screen.getByText("Indique el banco.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText(/Teléfono/), "3001112233");
    await user.type(screen.getByLabelText(/Correo electrónico/), "pedro@example.test");
    await user.type(screen.getByLabelText(/Dirección/), "Calle 1 # 2-3");
    await user.type(screen.getByLabelText(/^Banco/), "Bancolombia");
    await user.selectOptions(screen.getByLabelText(/Tipo de cuenta/), "AHORROS");
    await user.type(screen.getByLabelText(/Número de cuenta/), "0123456789");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        papeles: ["propietario"],
        direccion: "Calle 1 # 2-3",
        cuenta_bancaria: { banco: "Bancolombia", tipo: "AHORROS", numero: "0123456789" },
      }),
    );
  });

  it("al editar muestra casillas de papeles y permite agregar otro", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { user } = setup({
      modo: "editar",
      inicial: persona(5, "Mario Pérez", "1003", ["propietario"]) as never,
      onSubmit,
    });

    await user.click(screen.getByLabelText("Codeudor"));
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ papeles: ["propietario", "codeudor"] }));
  });

  it("muestra el conflicto de identificación duplicada y conserva lo escrito", async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError("Ya existe una persona registrada con ese tipo y número de identificación.", {
        status: 409,
        code: "identificacion_duplicada",
      }),
    );
    const { user } = setup({ papelFijo: "codeudor", onSubmit });

    await user.type(screen.getByLabelText(/Nombre completo/), "Otra Persona");
    await user.type(screen.getByLabelText(/^Identificación/), "99887766");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Ya existe una persona registrada");
    expect(screen.getByLabelText(/^Identificación/)).toHaveValue("99887766");
  });
});
