import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../../services/apiClient";
import { CATALOGOS, json, mockApi, usuario } from "../../test/mockApi";
import { UsuarioForm } from "./UsuarioForm";

function setup(props: Partial<Parameters<typeof UsuarioForm>[0]> = {}) {
  mockApi({ "GET /api/v1/catalogos": () => json(CATALOGOS) });
  const onSubmit = props.onSubmit ?? vi.fn().mockResolvedValue(undefined);
  render(<UsuarioForm modo="crear" onSubmit={onSubmit} onCancel={vi.fn()} {...props} />);
  return { onSubmit, user: userEvent.setup() };
}

describe("UsuarioForm", () => {
  it("valida los campos antes de enviar", async () => {
    const { user, onSubmit } = setup();

    await user.type(screen.getByLabelText(/Nombre de usuario/), "Con Espacios");
    await user.type(screen.getByLabelText(/^Clave/), "12345678");
    await user.click(screen.getByRole("button", { name: "Guardar usuario" }));

    expect(screen.getByText(/minúsculas, números, punto, guion/)).toBeInTheDocument();
    expect(screen.getByText("La clave debe tener al menos 8 caracteres, con letras y números.")).toBeInTheDocument();
    expect(screen.getByText("Seleccione un rol.")).toBeInTheDocument();
    expect(screen.getByText("Ingrese un correo electrónico válido.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("en edición no pide la clave y envía el estado activo", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const { user } = setup({
      modo: "editar",
      inicial: { ...usuario(3, "asesor1", "asesor"), rol: "asesor" },
      onSubmit,
    });

    expect(screen.getByLabelText(/Nombre de usuario/)).toBeDisabled();
    await user.click(screen.getByLabelText("Cuenta activa"));
    await user.click(screen.getByRole("button", { name: "Guardar usuario" }));

    expect(onSubmit).toHaveBeenCalledWith({
      nombre: "Persona asesor1",
      tipo_identificacion: "CC",
      identificacion: "100003",
      correo: "asesor1@example.test",
      rol: "asesor",
      activo: false,
    });
  });

  it("muestra el conflicto devuelto por la API y conserva lo escrito", async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError("Ya existe un usuario con ese nombre de usuario.", { status: 409, code: "usuario_duplicado" }),
    );
    const { user } = setup({ onSubmit });

    await user.type(screen.getByLabelText(/Nombre de usuario/), "admin");
    await user.selectOptions(await screen.findByLabelText(/^Rol/), "asesor");
    await user.type(screen.getByLabelText(/^Clave/), "Clave.Segura1");
    await user.type(screen.getByLabelText(/Nombre completo/), "Otra Persona");
    await user.selectOptions(screen.getByLabelText(/Tipo de identificación/), "CC");
    await user.type(screen.getByLabelText(/^Identificación/), "99887766");
    await user.type(screen.getByLabelText(/Correo electrónico/), "otra@example.test");
    await user.click(screen.getByRole("button", { name: "Guardar usuario" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Ya existe un usuario");
    expect(screen.getByLabelText(/Nombre de usuario/)).toHaveValue("admin");
  });
});
