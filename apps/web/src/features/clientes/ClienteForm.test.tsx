import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../services/apiClient";
import { ClienteForm } from "./ClienteForm";

function setup(onSubmit = vi.fn().mockResolvedValue(undefined)) {
  render(<ClienteForm onSubmit={onSubmit} />);
  return {
    onSubmit,
    user: userEvent.setup(),
    nombre: screen.getByLabelText("Nombre"),
    correo: screen.getByLabelText("Correo electrónico"),
    submit: screen.getByRole("button", { name: "Registrar cliente" }),
  };
}

describe("ClienteForm", () => {
  it("valida los campos antes de enviar", async () => {
    const { user, submit, onSubmit, correo } = setup();

    await user.type(correo, "no-es-correo");
    await user.click(submit);

    expect(screen.getByText("El nombre debe tener al menos 2 caracteres.")).toBeInTheDocument();
    expect(screen.getByText("Ingrese un correo electrónico válido.")).toBeInTheDocument();
    expect(correo).toHaveAttribute("aria-invalid", "true");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("envía los datos sin espacios sobrantes y limpia el formulario", async () => {
    const { user, nombre, correo, submit, onSubmit } = setup();

    await user.type(nombre, "  Cliente Ficticio  ");
    await user.type(correo, " ficticio@example.test ");
    await user.click(submit);

    expect(onSubmit).toHaveBeenCalledWith({
      nombre: "Cliente Ficticio",
      correo: "ficticio@example.test",
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Cliente registrado correctamente.");
    expect(nombre).toHaveValue("");
  });

  it("muestra los errores de validación devueltos por la API", async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError("Los datos enviados no son válidos.", {
        status: 422,
        code: "validacion",
        details: [
          {
            campo: "correo",
            ubicacion: "body",
            mensaje: "Value error, El correo electrónico no es válido",
            tipo: "value_error",
          },
        ],
      }),
    );
    const { user, nombre, correo, submit } = setup(onSubmit);

    await user.type(nombre, "Cliente");
    await user.type(correo, "a@b.co");
    await user.click(submit);

    expect(await screen.findByRole("alert")).toHaveTextContent("Los datos enviados no son válidos.");
    expect(screen.getByText("El correo electrónico no es válido")).toBeInTheDocument();
  });

  it("muestra el conflicto de correo duplicado", async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError("Ya existe un cliente registrado con ese correo electrónico.", {
        status: 409,
        code: "correo_duplicado",
      }),
    );
    const { user, nombre, correo, submit } = setup(onSubmit);

    await user.type(nombre, "Cliente");
    await user.type(correo, "dup@example.test");
    await user.click(submit);

    expect(await screen.findByRole("alert")).toHaveTextContent("Ya existe un cliente registrado");
    expect(nombre).toHaveValue("Cliente"); // conserva lo escrito
  });
});
