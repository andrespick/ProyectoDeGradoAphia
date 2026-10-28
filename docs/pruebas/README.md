# Pruebas

## Niveles

| Nivel | Herramientas | Comando | Requiere |
| --- | --- | --- | --- |
| Unitarias frontend | Vitest 5 + Testing Library + jsdom | `pnpm --filter @aphia/web test` | — |
| Unitarias API | Pytest + HTTPX (ASGITransport) | `pnpm --filter @aphia/api test` | — |
| Unitarias documentos | Pytest + HTTPX | `pnpm --filter @aphia/files test` | — |
| Todas las unitarias | | `pnpm test` | — |
| Lint / tipos | Ruff · TypeScript | `pnpm lint` · `pnpm typecheck` | — |
| Integración | Pytest contra MySQL real · `node --test` contra Docker | `pnpm test:integration` | Docker |
| Extremo a extremo | Playwright (Chromium) | `pnpm test:e2e` | Docker, navegador instalado |

`pnpm test:integration` levanta el contenedor **separado** `mysql-test` (base `aphia_test`,
datos en memoria), aplica las migraciones automáticamente, ejecuta las pruebas y lo elimina
(`--keep` para conservarlo). Las pruebas se niegan a correr si la base no termina en `_test`.

`pnpm test:e2e` levanta la infraestructura local, migra, carga los seeds (usuarios de desarrollo)
y Playwright inicia (o reutiliza) el
frontend y la API en **Python Workers local**, de modo que la prueba recorre el mismo runtime
que producción: navegador → Vite → Worker → Hyperdrive local → MySQL.

## Cobertura actual (resultados de la última ejecución local, 2026-10-28)

| Requisito | Pruebas | Resultado |
| --- | --- | --- |
| 1. Disponibilidad de la API | `test_health.py` (health, ready OK/503, MySQL inaccesible), integración `test_ready_con_mysql_real`, E2E «API conectada» | ✅ |
| 2. Validación de entradas | `test_personas.py` (identificación, correo, teléfono, papeles, cuenta bancaria, campos extra, paginación), `PersonaForm.test.tsx`, E2E | ✅ |
| 3. Clientes, propietarios y codeudores (RF-01…RF-06, RF-10, RF-12) | `test_personas.py` (papeles por lista, filtros, detalle, papel en uso, dependencias al eliminar, permisos del asesor, búsqueda), `test_personas_mysql.py` (tablas hijas, acentos, duplicados sin filas parciales, propietario con inmueble), `PersonasListPage.test.tsx`, `PersonaPicker.test.tsx`, E2E `clientes/propietarios/codeudores.spec.ts` | ✅ |
| 4. Persistencia en MySQL | integración (lectura directa por SQL, nueva instancia de la API, duplicado sin filas parciales, idempotencia de migraciones), E2E | ✅ |
| 5. Subida y recuperación de documento | `apps/files/tests` + `tests/integration/files-service.test.mjs` (incluye recrear el contenedor) | ✅ |
| 6. Rechazo de archivos no permitidos | ejecutable, HTML, texto, GIF, tipo declarado falso, demasiado grande (con y sin Content-Length), vacío, ids con *path traversal* | ✅ |
| 7. Manejo de errores | 404/405/422/409/401/403/500/503 con formato uniforme, sin trazas ni datos reflejados; configuración inválida | ✅ |
| 8. Comunicación frontend-backend | `apiClient.test.ts`, `HomePage.test.tsx` (mock de fetch), E2E real con CORS | ✅ |
| Integridad del modelo 3FN | `test_modelo_3fn.py`: 32 tablas + `person_party_role`, 36 + 2 FK con `RESTRICT`, códigos de la migración `0008`, escenarios válidos (incluida una persona con dos papeles) y 11 violaciones rechazadas con su código MySQL | ✅ |
| Catálogos para formularios | `test_catalogos.py` (contenido y 401), `test_catalogos_mysql.py` (códigos de `0008` sobre MySQL) | ✅ |
| Roles y configuración de autenticación | `test_auth.py`: roles `admin_sistemas`/`administrativo`/`asesor`, 403 por rol insuficiente, `AUTH_MODE=database` exige `AUTH_SECRET` de 32 caracteres | ✅ |
| Componentes compartidos de la web | `Field.test.tsx`, `Pagination.test.tsx`, `usePagedList.test.tsx` (filtros y paginación en la URL) | ✅ |
| Inicio de sesión y bloqueo (RF-17, RF-18) | `test_passwords.py` (formato, verificación, implementación pura = `hashlib`), `test_tokens.py` (firma, expiración, manipulación), `test_auth.py` (login, `/me`, 3 intentos → 423, bloqueo vencido, inactivo, logs sin credenciales), `test_auth_mysql.py` (bloqueo persistido y desbloqueo por el admin), `LoginPage.test.tsx`, `AuthProvider.test.tsx`, `apiClient.test.ts` (Bearer, 401), E2E `auth.spec.ts` | ✅ |
| Usuarios y roles (RF-16, RNF-03) | `test_usuarios.py` (CRUD, validaciones, último administrador, cuenta propia, desbloqueo, 403 por rol), `test_usuarios_mysql.py` (persona + documento + cuenta + rol; reutilización de persona; 409 de identificación), `UsuariosPage.test.tsx`, `UsuarioForm.test.tsx`, `MainLayout.test.tsx`, E2E `usuarios.spec.ts` | ✅ |
| Tablero e indicadores | `test_resumen.py`, `HomePage.test.tsx` | ✅ |
| Migraciones | idempotencia y aviso de fallo parcial (`test_migraciones_mysql.py`) | ✅ |

Totales: 50 (web) + 136 (API) + 31 (documentos) unitarias; 37 (API ↔ MySQL) + 5 (documentos)
de integración; 13 E2E (con inicio de sesión real contra el Worker local).

## CI

`.github/workflows/ci.yml` ejecuta lint, tipos, unitarias, integración con un servicio MySQL
8.4, construcción del frontend y de la imagen de documentos, *dry-run* del Worker y E2E.
La CI está escrita pero **todavía no se ha ejecutado en GitHub**: verifique la primera
ejecución tras el primer push.

## Buenas prácticas

- Datos siempre ficticios (`@example.test`). Las pruebas E2E generan correos únicos por ejecución.
- Pruebe comportamiento, no implementación: en React use roles y textos visibles.
- Una prueba nueva por cada error corregido.
