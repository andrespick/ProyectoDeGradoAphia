import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig(({ command, mode }) => {
  // Sin VITE_API_BASE_URL la web llama a su propio origen y Pages responde index.html a todo:
  // la aplicación parece «entrar» sin sesión. Mejor fallar al construir que publicar eso.
  const env = { ...loadEnv(mode, process.cwd(), "VITE_"), ...process.env };
  if (command === "build" && mode === "production" && !env.VITE_API_BASE_URL) {
    throw new Error(
      "Defina VITE_API_BASE_URL (URL pública de la API, p. ej. https://aphia-api.<cuenta>.workers.dev) " +
        "para construir la web de producción. Ver docs/despliegue/cloudflare-pages.md.",
    );
  }
  return {
    plugins: [react()],
    server: { host: "localhost", port: 5173, strictPort: true },
    preview: { host: "localhost", port: 4173, strictPort: true },
    build: { outDir: "dist", sourcemap: true },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      restoreMocks: true,
      unstubGlobals: true,
    },
  };
});
