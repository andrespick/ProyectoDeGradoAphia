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
| Extremo a extremo | Playwright: Chromium (todo) + Firefox y WebKit (pruebas `@smoke`) | `pnpm test:e2e` | Docker, navegadores (`pnpm test:e2e:install`) |

`pnpm test:integration` levanta el contenedor **separado** `mysql-test` (base `aphia_test`,
datos en memoria), aplica las migraciones automáticamente, ejecuta las pruebas y lo elimina
(`--keep` para conservarlo). Las pruebas se niegan a correr si la base no termina en `_test`.

`pnpm test:e2e` levanta la infraestructura local, migra, carga los seeds (usuarios de desarrollo)
y Playwright inicia (o reutiliza) el
frontend y la API con **Uvicorn**, el mismo servidor que producción: navegador → Vite → API
(`127.0.0.1:8000`) → MySQL.

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
| Inicio de sesión y bloqueo (RF-17, RF-18) | `test_passwords.py` (formato, verificación, hash ficticio), `test_tokens.py` (firma, expiración, manipulación), `test_auth.py` (login, `/me`, 3 intentos → 423, bloqueo vencido, inactivo, logs sin credenciales), `test_auth_mysql.py` (bloqueo persistido y desbloqueo por el admin), `LoginPage.test.tsx`, `AuthProvider.test.tsx`, `apiClient.test.ts` (Bearer, 401), E2E `auth.spec.ts` | ✅ |
| Usuarios y roles (RF-16, RNF-03) | `test_usuarios.py` (CRUD, validaciones, último administrador, cuenta propia, desbloqueo, 403 por rol), `test_usuarios_mysql.py` (persona + documento + cuenta + rol; reutilización de persona; 409 de identificación), `UsuariosPage.test.tsx`, `UsuarioForm.test.tsx`, `MainLayout.test.tsx`, E2E `usuarios.spec.ts` | ✅ |
| Tablero e indicadores | `test_resumen.py`, `HomePage.test.tsx` | ✅ |
| Inmuebles (RF-07…RF-09) | `test_inmuebles.py` (crear con propietarios y servicios, moneda solo con canon, 422 parametrizados, propietario inexistente 404, filtros, actualizar reemplaza listas, eliminar con contratos 409, asesor 403), `test_inmuebles_mysql.py` (ciudad única por nombre exacto, canon→COP, papel OWNER automático visible en `/propietarios`, bloqueo por contrato, filtros sin mayúsculas ni acentos), `InmuebleForm.test.tsx` (normalización del canon, propietario obligatorio, servicios, error de API), `InmueblesPage.test.tsx` (filtros de URL, 409 al eliminar, asesor, edición en panel), E2E `inmuebles.spec.ts` y `propietarios.spec.ts` (propietario con inmuebles no se elimina; el inscrito desde el inmueble aparece en Propietarios) | ✅ |
| Migraciones | idempotencia y aviso de fallo parcial (`test_migraciones_mysql.py`) | ✅ |
| Contratos y codeudores (RF-10…RF-15) | `test_contratos.py` (propietarios del inmueble o explícitos, papeles automáticos, 422 parametrizados, 404/409, matriz de solapamiento de fechas, filtros, listado sin texto, actualizar reemplaza partes, dependencias en PUT y DELETE, asesor 403), `test_contratos_mysql.py` (partes con sus códigos, `/codeudores?contrato_id=`, filtros por fechas y estado sobre MySQL, bloqueo por `financial_record`, búsqueda global), `ContratoForm.test.tsx`, `ContratosPage.test.tsx`, `ContratoDetallePage.test.tsx` (impresión y asociar codeudor), `BusquedaGlobal.test.tsx`, E2E `contratos.spec.ts` | ✅ |
| Ayuda en línea y diseño adaptable (RNF-06, RNF-07) | E2E `ayuda.spec.ts` (pública, enlace del login y de Clientes), `responsive.spec.ts` (375 px: sin desplazamiento horizontal, cajón, tabla desplazable, panel a pantalla completa) | ✅ |
| Compatibilidad de navegadores (RNF-08) | `auth.spec.ts` y `clientes.spec.ts` etiquetadas `@smoke` en Firefox y WebKit | ✅ |
| Rendimiento (RNF-01) | `test_rendimiento_mysql.py`: 500 personas; `GET /clientes?q=`, `/propietarios` y `/contratos?fecha_desde=` en menos de 3 s | ✅ |
| Código de soporte en errores | `errorMessage()` añade el `request_id` (`apiClient.test.ts`) | ✅ |
| Administración del sistema (RF-19…RF-24, fase 6) | `test_sesiones.py` (sesión revocada por versión o desactivación, clave temporal solo permite cambiarla, token nuevo al cambiarla, política de intentos/minutos/horas, `/auth/politica`, login auditado sin el usuario tecleado), `test_administracion.py` (clave temporal, cerrar sesiones, cuenta propia 409, política de largo, configuración y límites, empresa por rol, auditoría y fallo tolerado, estado con y sin MySQL, respaldo atrasado y solicitud única, catálogos), `test_papelera.py` (instantánea y restauración de persona, inmueble y contrato; 409 si no es posible), `test_administracion_mysql.py` (colación y valores de 0012–0018, sesiones y auditoría reales, clave temporal → cambio, papelera en la misma transacción, catálogos y empresa con FK, respaldo `SOLICITADO`, política aplicada al bloqueo), `Administracion.test.tsx`, E2E `administracion.spec.ts` | ✅ |

Totales: 77 (web) + 241 (API) + 31 (documentos) unitarias; 61 (API ↔ MySQL) + 5 (documentos)
de integración; 26 E2E en Chromium + 2 `@smoke` en Firefox y 2 en WebKit (inicio de sesión real
contra la API con Uvicorn). Última ejecución E2E completa (2026-11-01): 30 de 30, sin respuestas
500, en 1 minuto. Las fechas de `contratos.spec.ts` se calculan en el día de Colombia, como la API.

## CI

`.github/workflows/ci.yml` ejecuta lint, tipos, unitarias, integración con un servicio MySQL
8.4, construcción del frontend y de las imágenes de la API y de documentos, y E2E.
Corre en cada push y pull request; el workflow *Deploy* la reutiliza antes de desplegar.

## Buenas prácticas

- Datos siempre ficticios (`@example.test`). Las pruebas E2E generan correos únicos por ejecución.
- Pruebe comportamiento, no implementación: en React use roles y textos visibles.
- Una prueba nueva por cada error corregido.
