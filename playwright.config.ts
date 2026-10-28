import { defineConfig, devices } from "@playwright/test";

// Pruebas E2E: navegador → frontend (Vite) → API (Python Workers local) → MySQL (Docker).
// `pnpm test:e2e` levanta la infraestructura y aplica migraciones antes de ejecutar.
// Si `pnpm dev` ya está corriendo, Playwright reutiliza esos servidores.
export default defineConfig({
  testDir: "tests/e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  timeout: 60_000,
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    // Compatibilidad (RNF): solo las pruebas etiquetadas @smoke en los otros motores.
    { name: "firefox", use: { ...devices["Desktop Firefox"] }, grep: /@smoke/ },
    { name: "webkit", use: { ...devices["Desktop Safari"] }, grep: /@smoke/ },
  ],
  webServer: [
    {
      command: "pnpm --filter @aphia/api dev",
      url: "http://127.0.0.1:8787/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 240_000,
      stdout: "pipe",
    },
    {
      command: "pnpm --filter @aphia/web dev",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
