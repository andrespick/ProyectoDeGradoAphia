import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Field } from "./Field";
import { SelectField } from "./SelectField";

describe("Field", () => {
  it("asocia etiqueta, pista y error de forma accesible", async () => {
    const onChange = vi.fn();
    render(
      <Field
        id="nombre"
        label="Nombre"
        value=""
        hint="Como aparece en el documento"
        error="Obligatorio"
        required
        onChange={onChange}
      />,
    );

    const input = screen.getByLabelText(/Nombre/);
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Obligatorio Como aparece en el documento");
    await userEvent.type(input, "A");
    expect(onChange).toHaveBeenCalledWith("A");
  });

  it("SelectField muestra el marcador y las opciones", async () => {
    const onChange = vi.fn();
    render(
      <SelectField
        id="tipo"
        label="Tipo"
        value=""
        options={[{ value: "CC", label: "Cédula" }]}
        onChange={onChange}
      />,
    );

    const select = screen.getByLabelText("Tipo");
    expect(screen.getByRole("option", { name: "Seleccione…" })).toBeInTheDocument();
    await userEvent.selectOptions(select, "CC");
    expect(onChange).toHaveBeenCalledWith("CC");
  });
});
