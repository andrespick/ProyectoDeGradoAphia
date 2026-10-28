// Utilidades compartidas por los scripts de desarrollo (Node, multiplataforma).
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseEnv } from "node:util";

export const ROOT = fileURLToPath(new URL("../..", import.meta.url));
export const ENV_FILE = join(ROOT, ".env");
export const ENV_EXAMPLE = join(ROOT, ".env.example");
// Secretos del Worker local (pywrangler dev los lee de este archivo, no del proceso).
export const DEV_VARS_FILE = join(ROOT, "apps", "api", ".dev.vars");
export const DEV_VARS_EXAMPLE = join(ROOT, "apps", "api", ".dev.vars.example");

/**
 * Variables del proceso + .env de la raíz (las del proceso tienen prioridad, p. ej. en CI).
 * Deriva la cadena de conexión local que Wrangler usa para el binding HYPERDRIVE.
 */
export function loadEnv({ required = false } = {}) {
  if (!existsSync(ENV_FILE) && required) {
    console.error("No existe .env en la raíz del repositorio. Ejecute: pnpm env:init");
    process.exit(1);
  }
  const fromFile = existsSync(ENV_FILE) ? parseEnv(readFileSync(ENV_FILE, "utf8")) : {};
  const env = { ...fromFile, ...process.env };

  if (!env.CLOUDFLARE_HYPERDRIVE_LOCAL_CONNECTION_STRING_HYPERDRIVE && env.DB_USER && env.DB_PASSWORD) {
    const user = encodeURIComponent(env.DB_USER);
    const password = encodeURIComponent(env.DB_PASSWORD);
    const host = env.DB_HOST ?? "127.0.0.1";
    const port = env.DB_PORT ?? "3307";
    const database = env.DB_NAME ?? "aphia";
    env.CLOUDFLARE_HYPERDRIVE_LOCAL_CONNECTION_STRING_HYPERDRIVE = `mysql://${user}:${password}@${host}:${port}/${database}`;
  }
  env.PYTHONUTF8 ??= "1"; // evita errores de codificación de Python en consolas Windows
  return env;
}

/** Ejecuta un programa heredando la consola. Resuelve con el código de salida. */
export function run(command, args, { env = process.env, cwd = ROOT } = {}) {
  return new Promise((resolve) => {
    const child = spawn(command, args, { stdio: "inherit", env, cwd });
    child.on("error", (error) => {
      if (error.code === "ENOENT") {
        console.error(`No se encontró "${command}". Verifique que esté instalado y en el PATH.`);
      } else {
        console.error(error.message);
      }
      resolve(127);
    });
    child.on("exit", (code, signal) => resolve(code ?? (signal ? 1 : 0)));
  });
}
