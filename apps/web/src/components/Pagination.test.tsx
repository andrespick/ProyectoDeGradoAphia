import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Pagination } from "./Pagination";

describe("Pagination", () => {
  it("muestra el rango y navega entre páginas", async () => {
    const onOffsetChange = vi.fn();
    const onLimitChange = vi.fn();
    render(
      <Pagination
        total={57}
        limit={20}
        offset={20}
        onOffsetChange={onOffsetChange}
        onLimitChange={onLimitChange}
        etiqueta="clientes"
      />,
    );

    expect(screen.getByText("Mostrando 21–40 de 57 clientes")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(onOffsetChange).toHaveBeenCalledWith(40);
    await userEvent.click(screen.getByRole("button", { name: "Anterior" }));
    expect(onOffsetChange).toHaveBeenCalledWith(0);
    await userEvent.selectOptions(screen.getByLabelText("Por página"), "50");
    expect(onLimitChange).toHaveBeenCalledWith(50);
  });

  it("deshabilita los extremos", () => {
    render(<Pagination total={5} limit={20} offset={0} onOffsetChange={vi.fn()} />);

    expect(screen.getByText("Mostrando 1–5 de 5 registros")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
  });
});
