#!/usr/bin/env node
// Crea .env a partir de .env.example y genera secretos aleatorios para el entorno LOCAL.
// Uso: pnpm env:init            (no sobrescribe un .env existente)
import { randomBytes } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";

import { ENV_EXAMPLE, ENV_FILE } from "./lib/env.mjs";

// Variables que se generan si están vacías en .env.example.
const GENERATED = new Set([
  "MYSQL_ROOT_PASSWORD",
  "DB_PASSWORD",
  "TEST_DB_ROOT_PASSWORD",
  "TEST_DB_PASSWORD",
  "FILES_SERVICE_TOKEN",
]);

const quiet = process.argv.includes("--if-missing");

if (existsSync(ENV_FILE)) {
  if (!quiet) console.log(".env ya existe; no se modificó.");
  process.exit(0);
}

const lines = readFileSync(ENV_EXAMPLE, "utf8").split(/\r?\n/);
const output = lines.map((line) => {
  const match = /^([A-Z0-9_]+)=$/.exec(line);
  if (match && GENERATED.has(match[1])) return `${match[1]}=${randomBytes(24).toString("hex")}`;
  return line;
});

writeFileSync(ENV_FILE, output.join("\n"), { encoding: "utf8", mode: 0o600 });
console.log("Se creó .env con secretos locales aleatorios (no lo versione).");
