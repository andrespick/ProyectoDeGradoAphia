#!/usr/bin/env node
// Crea .env (raíz) y apps/api/.dev.vars a partir de sus ejemplos y genera secretos aleatorios
// para el entorno LOCAL. Nunca sobrescribe valores existentes; si a un archivo ya creado le
// falta AUTH_SECRET (p. ej. instalaciones anteriores), lo añade al final.
// Uso: pnpm env:init            (--if-missing: silencioso cuando no hay nada que hacer)
import { randomBytes } from "node:crypto";
import { appendFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { parseEnv } from "node:util";

import { DEV_VARS_EXAMPLE, DEV_VARS_FILE, ENV_EXAMPLE, ENV_FILE } from "./lib/env.mjs";

// Variables que se generan si están vacías en los archivos de ejemplo.
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

function render(examplePath, fixed) {
  return readFileSync(examplePath, "utf8")
    .split(/\r?\n/)
    .map((line) => {
      const match = /^([A-Z0-9_]+)=$/.exec(line);
      if (match && GENERATED.has(match[1])) return `${match[1]}=${fixed[match[1]] ?? secret()}`;
      return line;
    })
    .join("\n");
}

function readVar(path, name) {
  return existsSync(path) ? parseEnv(readFileSync(path, "utf8"))[name] : undefined;
}

// El mismo AUTH_SECRET en .env (Uvicorn) y en .dev.vars (Workers local): ambos runtimes
// deben aceptar los mismos tokens.
const authSecret = readVar(ENV_FILE, "AUTH_SECRET") ?? readVar(DEV_VARS_FILE, "AUTH_SECRET") ?? secret();

let changed = false;
for (const [file, example, label] of [
  [ENV_FILE, ENV_EXAMPLE, ".env"],
  [DEV_VARS_FILE, DEV_VARS_EXAMPLE, "apps/api/.dev.vars"],
]) {
  if (!existsSync(file)) {
    writeFileSync(file, render(example, { AUTH_SECRET: authSecret }), { encoding: "utf8", mode: 0o600 });
    log(`Se creó ${label} con secretos locales aleatorios (no lo versione).`);
    changed = true;
  } else if (readVar(file, "AUTH_SECRET") === undefined) {
    appendFileSync(file, `\n# Clave de firma de tokens de sesión (agregada por pnpm env:init)\nAUTH_SECRET=${authSecret}\n`);
    log(`Se agregó AUTH_SECRET a ${label}.`);
    changed = true;
  }
}
if (!changed) log(".env y apps/api/.dev.vars ya existen; no se modificaron.");
