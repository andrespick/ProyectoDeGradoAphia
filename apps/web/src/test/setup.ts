import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import { invalidateCatalogos } from "../services/catalogosService";

afterEach(() => {
  cleanup();
  invalidateCatalogos();
});
