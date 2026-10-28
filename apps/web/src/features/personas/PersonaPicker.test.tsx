import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { apiError, CATALOGOS, json, mockApi, persona } from "../../test/mockApi";
import { PersonaPicker } from "./PersonaPicker";

describe("PersonaPicker", () => {
  it("busca por identificación y selecciona la persona encontrada", async () => {
    mockApi({
      "GET /api/v1/catalogos": () => json(CATALOGOS),
      "GET /api/v1/personas/buscar": (_init, url) =>
        url.searchParams.get("identificacion") === "1020"
          ? json(persona(7, "Ana García", "1020", ["arrendatario"]))
          : apiError(404, "persona_no_encontrada", "La persona no existe."),
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<PersonaPicker idPrefix="p" label="Arrendatario" papel="arrendatario" value={null} onChange={onChange} />);

    await user.type(screen.getByLabelText("Identificación"), "1020");
    await user.click(screen.getByRole("button", { name: /Buscar/ }));
    expect(await screen.findByText("Ana García")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Seleccionar" }));

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ id: 7, nombre: "Ana García" }));
  });

  it("si no existe permite registrarla en el momento con el papel indicado", async () => {
    let cuerpo: Record<string, unknown> | null = null;
    mockApi({
      "GET /api/v1/catalogos": () => json(CATALOGOS),
      "GET /api/v1/personas/buscar": () => apiError(404, "persona_no_encontrada", "La persona no existe."),
      "POST /api/v1/clientes": (init) => {
        cuerpo = JSON.parse(String(init?.body)) as Record<string, unknown>;
        return json(persona(9, "Nuevo Codeudor", "555", ["codeudor"]), 201);
      },
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<PersonaPicker idPrefix="c" label="Codeudor" papel="codeudor" value={null} onChange={onChange} />);

    await user.type(screen.getByLabelText("Identificación"), "555");
    await user.click(screen.getByRole("button", { name: /Buscar/ }));
    expect(await screen.findByText("No existe una persona con esa identificación.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Registrar nueva persona/ }));
    await user.type(screen.getByLabelText(/Nombre completo/), "Nuevo Codeudor");
    await user.click(screen.getByRole("button", { name: "Registrar como codeudor" }));

    expect(cuerpo).toMatchObject({ identificacion: "555", tipo_identificacion: "CC", papeles: ["codeudor"] });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ id: 9 }));
  });

  it("en modo solo búsqueda no ofrece el registro y muestra la persona elegida como chip", async () => {
    mockApi({
      "GET /api/v1/catalogos": () => json(CATALOGOS),
      "GET /api/v1/personas/buscar": () => apiError(404, "persona_no_encontrada", "La persona no existe."),
    });
    const onChange = vi.fn();
    const user = userEvent.setup();
    const { rerender } = render(
      <PersonaPicker idPrefix="f" label="Propietario" papel="propietario" value={null} onChange={onChange} soloBuscar />,
    );

    await user.type(screen.getByLabelText("Identificación"), "1");
    await user.click(screen.getByRole("button", { name: /Buscar/ }));
    expect(await screen.findByText("No existe una persona con esa identificación.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Registrar nueva persona/ })).not.toBeInTheDocument();

    rerender(
      <PersonaPicker
        idPrefix="f"
        label="Propietario"
        papel="propietario"
        value={persona(3, "Laura Dueña", "1001", ["propietario"])}
        onChange={onChange}
        soloBuscar
      />,
    );
    expect(screen.getByText("Laura Dueña")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cambiar propietario" }));
    expect(onChange).toHaveBeenCalledWith(null);
  });
});
