// Prueba de integración del servicio de documentos ejecutándose en Docker.
// Verifica subida, recuperación, persistencia al recrear el contenedor, rechazo de tipos
// no permitidos y eliminación autorizada. Requiere: pnpm infra:up (o pnpm test:integration).
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { after, before, describe, test } from "node:test";

import { ENV_FILE, ROOT, loadEnv, run } from "../../scripts/lib/env.mjs";

const env = loadEnv({ required: true });
const BASE = `http://127.0.0.1:${env.FILES_PORT ?? "4000"}`;
const AUTH = { Authorization: `Bearer ${env.FILES_SERVICE_TOKEN}` };
const COMPOSE = ["compose", "-f", join(ROOT, "infra", "local", "compose.yaml"), "--env-file", ENV_FILE];

// PDF mínimo válido generado en la prueba (sin datos reales).
const PDF = Buffer.from(
  "%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n" +
    "2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n",
);
const sha256 = (buffer) => createHash("sha256").update(buffer).digest("hex");

async function upload(body, contentType = "application/pdf", headers = AUTH) {
  return fetch(`${BASE}/v1/files`, {
    method: "POST",
    headers: { ...headers, "Content-Type": contentType, "X-Filename": "contrato-de-prueba.pdf" },
    body,
  });
}

describe("servicio de documentos (Docker)", () => {
  let fileId;

  before(async () => {
    const response = await fetch(`${BASE}/health`).catch(() => null);
    assert.ok(response?.ok, `El servicio no responde en ${BASE}. Ejecute pnpm infra:up.`);
  });

  after(async () => {
    if (fileId) await fetch(`${BASE}/v1/files/${fileId}`, { method: "DELETE", headers: AUTH });
  });

  test("sube un PDF y lo recupera íntegro", async () => {
    const response = await upload(PDF);
    assert.equal(response.status, 201);
    const stored = await response.json();
    assert.match(stored.id, /^[0-9a-f]{32}$/);
    assert.equal(stored.sha256, sha256(PDF));
    fileId = stored.id;

    const download = await fetch(`${BASE}/v1/files/${fileId}`, { headers: AUTH });
    assert.equal(download.status, 200);
    assert.equal(download.headers.get("content-type"), "application/pdf");
    assert.equal(sha256(Buffer.from(await download.arrayBuffer())), sha256(PDF));
  });

  test("el documento persiste al recrear el contenedor", async () => {
    assert.ok(fileId, "requiere la prueba anterior");
    const code = await run("docker", [...COMPOSE, "up", "-d", "--force-recreate", "--wait", "files"], { env });
    assert.equal(code, 0, "no se pudo recrear el contenedor files");

    const download = await fetch(`${BASE}/v1/files/${fileId}`, { headers: AUTH });
    assert.equal(download.status, 200);
    assert.equal(sha256(Buffer.from(await download.arrayBuffer())), sha256(PDF));
  });

  test("rechaza archivos no permitidos", async () => {
    const executable = await upload(Buffer.from("MZ\x90\x00 contenido ejecutable"), "application/pdf");
    assert.equal(executable.status, 415);
    const text = await upload(Buffer.from("texto plano"), "text/plain");
    assert.equal(text.status, 415);
  });

  test("exige el token de servicio", async () => {
    assert.ok(fileId);
    const anonymous = await fetch(`${BASE}/v1/files/${fileId}`);
    assert.equal(anonymous.status, 401);
    const wrong = await fetch(`${BASE}/v1/files/${fileId}`, {
      method: "DELETE",
      headers: { Authorization: "Bearer token-incorrecto" },
    });
    assert.equal(wrong.status, 401);
  });

  test("elimina el documento con autorización", async () => {
    assert.ok(fileId);
    const deleted = await fetch(`${BASE}/v1/files/${fileId}`, { method: "DELETE", headers: AUTH });
    assert.equal(deleted.status, 204);
    const missing = await fetch(`${BASE}/v1/files/${fileId}`, { headers: AUTH });
    assert.equal(missing.status, 404);
    fileId = undefined;
  });
});
