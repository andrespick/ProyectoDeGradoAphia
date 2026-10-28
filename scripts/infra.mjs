#!/usr/bin/env node
// Infraestructura local con Docker Compose (MySQL, MySQL de pruebas y servicio de documentos).
// Uso: node scripts/infra.mjs <up|down|logs|ps|test-up|test-down|reset --yes>
import { join } from "node:path";

import { ENV_FILE, ROOT, loadEnv, run } from "./lib/env.mjs";

const COMPOSE = ["compose", "-f", join(ROOT, "infra", "local", "compose.yaml"), "--env-file", ENV_FILE];

const commands = {
  up: ["up", "-d", "--build", "--wait", "mysql", "files"],
  down: ["--profile", "test", "down"],
  logs: ["logs", "-f", "--tail", "100"],
  ps: ["ps"],
  "test-up": ["--profile", "test", "up", "-d", "--wait", "mysql-test"],
  "test-down": ["--profile", "test", "rm", "-sf", "mysql-test"],
  reset: ["--profile", "test", "down", "--volumes"],
};

const [action, ...rest] = process.argv.slice(2);
if (!action || !(action in commands)) {
  console.error(`Uso: node scripts/infra.mjs <${Object.keys(commands).join("|")}>`);
  process.exit(2);
}
if (action === "reset" && !rest.includes("--yes")) {
  console.error("reset elimina los volúmenes locales (MySQL y documentos). Confirme con --yes.");
  process.exit(2);
}

const env = loadEnv({ required: true });
const code = await run("docker", [...COMPOSE, ...commands[action]], { env });
if (code === 127) {
  console.error("Instale Docker Desktop (Windows/macOS) o Docker Engine (Linux) e inícielo.");
}
process.exit(code);
