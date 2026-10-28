# Guía de instalación y mantenimiento

Para la persona responsable de operar APHIA. Complementa las guías paso a paso de
[despliegue](README.md) y el [manual de usuario](../manual-usuario.md).

## 1. Instalación local (desarrollo y demostración)

Requisitos: Node.js 22.12+, pnpm 12, uv, Docker Desktop (o Docker Engine) y Git.

```bash
git clone <repositorio> aphia && cd aphia
pnpm install                 # dependencias Node y Python (uv sync en apps/api y apps/files)
pnpm env:init                # crea .env y apps/api/.dev.vars con un AUTH_SECRET aleatorio
pnpm infra:up                # MySQL 8.4 y servicio de documentos en Docker (solo 127.0.0.1)
pnpm db:migrate && pnpm db:seed   # modelo 3FN + catálogos + datos ficticios de desarrollo
pnpm dev                     # API en Python Workers local (8787) y web (5173)
```

Usuarios de desarrollo (seed `0003`, contraseña `Aphia.2026`): `admin`, `administrativo`,
`asesor`. **Nunca** cargue los seeds en producción.

Verificación: `pnpm lint && pnpm typecheck && pnpm test`, `pnpm test:integration` y
`pnpm test:e2e` (ver [pruebas](../pruebas/README.md)).

## 2. Despliegue en producción

Siga el [orden recomendado](README.md): VPS → MySQL → documentos → túnel y Workers VPC →
Hyperdrive → Workers (API) → Pages (web) → GitHub Actions → respaldos. Secretos:

| Secreto | Dónde | Cómo |
| --- | --- | --- |
| `AUTH_SECRET` (≥ 32 caracteres) | Worker | `uv run pywrangler secret put AUTH_SECRET --env production` |
| Contraseñas de MySQL y token del servicio de documentos | VPS | `infra/production/secrets/` (no versionado) |
| Clave privada `age` de respaldos | Fuera del VPS | Gestor de contraseñas |

La API no arranca en modo `database` sin `AUTH_SECRET`; el mensaje de configuración lo indica.

## 3. Primer administrador en producción

Los seeds no se usan en producción. Genere el hash localmente y cree la cuenta por SQL:

```bash
cd apps/api && uv run python -c "from modules.auth.passwords import hash_password; print(hash_password('ContraseñaInicial.2026'))"
```

```sql
INSERT INTO person (full_name) VALUES ('Nombre del administrador');
SET @p = LAST_INSERT_ID();
INSERT INTO person_document (person_id, document_type_id, document_identifier)
SELECT @p, document_type_id, '<identificación>' FROM document_type WHERE issuer_scope = 'CO' AND code = 'CC';
INSERT INTO user_account (person_id, user_name, login_email, hashed_password, is_active)
VALUES (@p, 'admin', 'admin@<dominio>', '<hash pbkdf2_sha256$…>', 1);
INSERT INTO user_role (account_id, role_id)
SELECT LAST_INSERT_ID(), role_id FROM app_role WHERE code = 'ADMIN_SISTEMAS';
```

Inicie sesión y cambie la contraseña desde Usuarios. Los demás usuarios se crean desde la pantalla.

## 4. Tareas recurrentes

| Tarea | Frecuencia | Cómo |
| --- | --- | --- |
| Respaldo cifrado (MySQL + documentos) | Diario (cron 03:15 UTC) | `infra/production/backup/backup.sh`: copia local en `BACKUP_LOCAL_DIR` (700/600, retención 14 días) y copia externa opcional con rclone. Ver [restauración](restauracion.md) |
| Prueba de restauración | Trimestral | `restore.sh` en una réplica local; verificar `/api/ready` y un contrato |
| Rotación de `AUTH_SECRET` | Anual o ante sospecha de fuga | `pywrangler secret put AUTH_SECRET`; cierra todas las sesiones (los usuarios vuelven a iniciar sesión) |
| Desbloqueo manual de una cuenta | A demanda | Pantalla Usuarios → «Desbloquear», o por SQL: `UPDATE user_account SET failed_login_attempts = 0, locked_until = NULL WHERE user_name = '…'` |
| Migraciones | En cada versión | Respaldo verificado → `pnpm db:migrate -- --confirm-backup` contra producción (nunca al iniciar el Worker) |
| Actualización de dependencias | Mensual | `pnpm update --interactive`, `uv lock --upgrade` en `apps/api` y `apps/files`; correr las pruebas; verificar compatibilidad con Pyodide antes de subir una dependencia Python |
| Revisión de logs | Semanal | Ver abajo |

## 5. Qué vigilar en los logs

Los logs de la API son JSON (una línea por evento) sin datos personales ni cuerpos de solicitud.

| Evento | Significado | Acción |
| --- | --- | --- |
| `login_failed` repetido para un `account_id` | Contraseña olvidada o intento de fuerza bruta | Confirmar con el usuario; el bloqueo de 15 min actúa solo |
| `cuenta_bloqueada` | Tercer intento fallido | Desbloquear desde Usuarios si el usuario lo solicita |
| `login_failed` con `motivo: cuenta_no_disponible` | Usuario inexistente o inactivo | Muchos seguidos = enumeración de usuarios; revisar origen |
| `unhandled_exception` | Error no controlado (respuesta 500) | Buscar el `request_id` que el usuario cita como «código de soporte» |
| `db_connect_failed` / `/api/ready` 503 | MySQL o Hyperdrive inaccesibles | Revisar túnel, contenedor MySQL y Hyperdrive |
| `duration_ms` alto de forma sostenida | Consultas lentas | Revisar índices y volumen; RNF: < 3 s |

## 6. Restauración y recuperación

Ver [restauración](restauracion.md): escenarios de borrado accidental, contenedor dañado,
pérdida del VPS y migración fallida. La copia local **no** sobrevive a la pérdida del VPS;
mantenga el destino externo configurado.

## 7. Límites conocidos

- Plan gratuito de Workers: el inicio de sesión (PBKDF2, ~260 ms de CPU) supera el límite de
  10 ms; use el plan de pago o sirva la API con Uvicorn en el VPS.
- Los cambios de rol o la desactivación aplican en el siguiente inicio de sesión o a las 8 h.
- No hay recuperación de contraseña por correo: la asigna el Administrador de Sistemas.
