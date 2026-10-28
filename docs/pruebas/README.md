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

`pnpm test:e2e` levanta la infraestructura local, migra, y Playwright inicia (o reutiliza) el
frontend y la API en **Python Workers local**, de modo que la prueba recorre el mismo runtime
que producción: navegador → Vite → Worker → Hyperdrive local → MySQL.

## Cobertura actual (resultados de la última ejecución local, 2026-10-27)

| Requisito | Pruebas | Resultado |
| --- | --- | --- |
| 1. Disponibilidad de la API | `test_health.py` (health, ready OK/503, MySQL inaccesible), integración `test_ready_con_mysql_real`, E2E «API conectada» | ✅ |
| 2. Validación de entradas | `test_clientes.py` (correo, longitudes, caracteres de control, campos extra, paginación), `ClienteForm.test.tsx`, E2E validación | ✅ |
| 3. Creación y consulta de cliente ficticio | unitarias + integración + E2E | ✅ |
| 4. Persistencia en MySQL | integración (lectura directa por SQL, nueva instancia de la API, rollback, idempotencia de migraciones), E2E recarga | ✅ |
| 5. Subida y recuperación de documento | `apps/files/tests` + `tests/integration/files-service.test.mjs` (incluye recrear el contenedor) | ✅ |
| 6. Rechazo de archivos no permitidos | ejecutable, HTML, texto, GIF, tipo declarado falso, demasiado grande (con y sin Content-Length), vacío, ids con *path traversal* | ✅ |
| 7. Manejo de errores | 404/405/422/409/401/403/500/503 con formato uniforme, sin trazas ni datos reflejados; configuración inválida | ✅ |
| 8. Comunicación frontend-backend | `apiClient.test.ts`, `HomePage.test.tsx` (mock de fetch), E2E real con CORS | ✅ |
| Integridad del modelo 3FN | `test_modelo_3fn.py`: 32 tablas, 36 FK con `RESTRICT`, escenarios válidos y 9 violaciones rechazadas con su código MySQL | ✅ |
| Migraciones | idempotencia y aviso de fallo parcial (`test_migraciones_mysql.py`) | ✅ |

Totales: 17 (web) + 60 (API) + 31 (documentos) unitarias; 21 (API ↔ MySQL) + 5 (documentos)
de integración; 5 E2E.

## CI

`.github/workflows/ci.yml` ejecuta lint, tipos, unitarias, integración con un servicio MySQL
8.4, construcción del frontend y de la imagen de documentos, *dry-run* del Worker y E2E.
La CI está escrita pero **todavía no se ha ejecutado en GitHub**: verifique la primera
ejecución tras el primer push.

## Buenas prácticas

- Datos siempre ficticios (`@example.test`). Las pruebas E2E generan correos únicos por ejecución.
- Pruebe comportamiento, no implementación: en React use roles y textos visibles.
- Una prueba nueva por cada error corregido.
