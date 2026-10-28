#!/usr/bin/env node
// Ejecuta un comando con las variables del .env de la raíz.
// Uso: node scripts/run.mjs <programa> [argumentos...]
import { loadEnv, run } from "./lib/env.mjs";

const [command, ...args] = process.argv.slice(2);
if (!command) {
  console.error("Uso: node scripts/run.mjs <programa> [argumentos...]");
  process.exit(2);
}

process.exit(await run(command, args, { env: loadEnv(), cwd: process.cwd() }));
