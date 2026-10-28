#!/usr/bin/env node
// Pruebas de integración:
//   1. API ↔ MySQL real (contenedor mysql-test, base aphia_test, datos efímeros en tmpfs).
//   2. Servicio de documentos en Docker: persistencia al recrear el contenedor.
// Uso: pnpm test:integration [--keep]   (--keep deja corriendo mysql-test)
import { join } from "node:path";

import { ENV_FILE, ROOT, loadEnv, run } from "./lib/env.mjs";

const keep = process.argv.includes("--keep");
const env = loadEnv({ required: true });
const compose = ["compose", "-f", join(ROOT, "infra", "local", "compose.yaml"), "--env-file", ENV_FILE];

function step(title) {
  console.log(`\n▶ ${title}`);
}

let failures = 0;

step("Iniciando MySQL de pruebas y servicio de documentos");
if ((await run("docker", [...compose, "--profile", "test", "up", "-d", "--build", "--wait", "mysql-test", "files"], { env })) !== 0) {
  process.exit(1);
}

step("API ↔ MySQL (pytest -m integration)");
const testDbEnv = {
  ...env,
  TEST_DB_HOST: "127.0.0.1",
  TEST_DB_PORT: env.TEST_DB_PORT ?? "3308",
  TEST_DB_NAME: "aphia_test",
  TEST_DB_USER: "aphia_test",
  TEST_DB_PASSWORD: env.TEST_DB_PASSWORD,
};
failures += (await run("uv", ["run", "pytest", "-m", "integration"], { env: testDbEnv, cwd: join(ROOT, "apps", "api") })) !== 0 ? 1 : 0;

step("Servicio de documentos en Docker (node --test)");
failures += (await run(process.execPath, ["--test", "tests/integration/*.test.mjs"], { env })) !== 0 ? 1 : 0;

if (!keep) {
  step("Deteniendo MySQL de pruebas");
  await run("docker", [...compose, "--profile", "test", "rm", "-sf", "mysql-test"], { env });
}

console.log(failures === 0 ? "\n✔ Pruebas de integración superadas" : `\n✖ ${failures} grupo(s) de pruebas fallaron`);
process.exit(failures === 0 ? 0 : 1);
