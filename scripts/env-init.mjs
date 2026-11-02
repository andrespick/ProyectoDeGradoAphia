#!/usr/bin/env node
// Crea .env (raíz) a partir de .env.example y genera secretos aleatorios para el entorno
// LOCAL. Nunca sobrescribe valores existentes; si a un .env ya creado le falta AUTH_SECRET
// (p. ej. instalaciones anteriores), lo añade al final.
// Uso: pnpm env:init            (--if-missing: silencioso cuando no hay nada que hacer)
import { randomBytes } from "node:crypto";
import { appendFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { parseEnv } from "node:util";

import { ENV_EXAMPLE, ENV_FILE } from "./lib/env.mjs";

// Variables que se generan si están vacías en el archivo de ejemplo.
const GENERATED = new Set([
  "MYSQL_ROOT_PASSWORD",
  "DB_PASSWORD",
  "TEST_DB_ROOT_PASSWORD",
  "TEST_DB_PASSWORD",
  "FILES_SERVICE_TOKEN",
  "AUTH_SECRET",
]);

const quiet = process.argv.includes("--if-missing");
const log = (message) => {
  if (!quiet) console.log(message);
};

function secret() {
  return randomBytes(24).toString("hex"); // 48 caracteres
}

function render(examplePath) {
  return readFileSync(examplePath, "utf8")
    .split(/\r?\n/)
    .map((line) => {
      const match = /^([A-Z0-9_]+)=$/.exec(line);
      if (match && GENERATED.has(match[1])) return `${match[1]}=${secret()}`;
      return line;
    })
    .join("\n");
}

if (!existsSync(ENV_FILE)) {
  writeFileSync(ENV_FILE, render(ENV_EXAMPLE), { encoding: "utf8", mode: 0o600 });
  log("Se creó .env con secretos locales aleatorios (no lo versione).");
} else if (parseEnv(readFileSync(ENV_FILE, "utf8")).AUTH_SECRET === undefined) {
  appendFileSync(ENV_FILE, `\n# Clave de firma de tokens de sesión (agregada por pnpm env:init)\nAUTH_SECRET=${secret()}\n`);
  log("Se agregó AUTH_SECRET a .env.");
} else {
  log(".env ya existe; no se modificó.");
}
